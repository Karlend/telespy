from datetime import datetime
from telethon import TelegramClient, events, functions
from telethon.tl.types import UserStatusOnline
from time import mktime
from os import path
import logging

from telespy.config import Config

logger = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
config = Config()

def utc2localtime(utc):
	pivot = mktime(utc.timetuple())
	offset = datetime.fromtimestamp(pivot) - datetime.utcfromtimestamp(pivot)
	return utc + offset

file_name = "online.csv"

def append_file(text):
	with open(file_name, "a") as f:
		f.write("\n" + text)

def check_file():
	if not path.exists(file_name):
		with open(file_name, "w") as f:
			f.write("\"user\", \"date_start\", \"session_time\"")

class User():
	id: int
	name: str
	first_name: str
	last_name: str
	db_name: str
	is_online: bool
	online_start: int

	def __init__(self, client, db_name):
		self.id = client.id
		self.first_name = client.first_name
		self.last_name = client.last_name or ""
		name = client.first_name
		if client.last_name:
			name = f"{name} {client.last_name}"
		self.name = name
		self.db_name = db_name
		self.is_online = False

		logger.info(f"Added account - {self.id}, {self.name}")

		if isinstance(client.status, UserStatusOnline):
			self.online()

	def online(self):
		if self.is_online:
			return
		self.is_online = True
		now = datetime.now()
		self.online_start = datetime.timestamp(now)
		print(f'~{now.strftime(DATETIME_FORMAT)}: {self.db_name} went online. | {self.name}')

	def offline(self):
		if not self.is_online:
			return
		self.is_online = False
		now = datetime.now()
		session_time = round(datetime.timestamp(now) - self.online_start)
		del self.online_start
		stamp = now.strftime(DATETIME_FORMAT)
		append_file(f"{self.db_name}, {stamp}, {session_time}")
		logger.info(f'~{stamp}: {self.db_name} went offline. Session time: {session_time}. | {self.name}')
		

targets = {}

client = TelegramClient('telespy', config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
client.start()

async def check_contacts():
	logger.debug("Parsing contacts")
	result = await client(functions.contacts.GetContactsRequest(hash=0))
	ids = []
	for user in result.users:
		ids.append(user.id)
	logger.debug("Checking contacts")
	for track_id in targets:
		if not track_id in ids:
			user = targets.get(track_id)
			await client(functions.contacts.AddContactRequest(
				id = track_id,
				first_name = user.first_name,
				last_name = user.last_name,
				phone = "",
				add_phone_privacy_exception = False
			))
			logger.info(f"Added contact {user.name} - {user.id}")


async def get_contact():
	global targets
	logger.debug("Loading tracked users")
	for user in config["TRACK_USERS"]:
		contact = await client.get_entity(user)
		if contact is None:
			print(f"Contact {user} not found")
			continue
		track_user = User(contact, user)
		targets[contact.id] = track_user

	await check_contacts()
			

@client.on(events.UserUpdate())
async def update(event):
	user = targets.get(event.user_id)
	if user is None:
		return
	logger.debug(f"Received update for {user.name} - {user.id}")
	if event.online:
		user.online()
	else:
		user.offline()

def main():
	check_file()
	client.loop.create_task(get_contact())
	client.loop.create_task(check_contacts())
	client.run_until_disconnected()