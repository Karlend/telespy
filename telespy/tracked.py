"""Tracked list"""

import logging

from os import path
from datetime import datetime

from telethon.tl.types import UserStatusOnline

from telespy.config import Config
from telespy.dispatcher import bot

logger = logging.getLogger(__name__)
config = Config()

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
FILE_NAME = "online.csv"

def append_file(text):
	if not config["TRACK_LOG_FILE"]:
		return
	with open(FILE_NAME, "a") as f:
		f.write("\n" + text)

def check_file():
	if not path.exists(FILE_NAME):
		with open(FILE_NAME, "w") as f:
			f.write("\"user\", \"date_start\", \"session_time\"")

check_file()

class User():
	id: int
	name: str
	first_name: str
	last_name: str
	is_online: bool
	online_start: int

	def __init__(self, client):
		self.id = client.id
		self.first_name = client.first_name
		self.last_name = client.last_name or ""
		name = client.first_name
		if client.last_name:
			name = f"{name} {client.last_name}"
		self.name = name
		self.link = f"<a href=\"tg://user?id={self.id}\">{self.name}</a>"
		self.is_online = False

		logger.info(f"Added account - {self.id}, {self.name}")

		if isinstance(client.status, UserStatusOnline):
			self.online()

	def __str__(self):
		return self.name

	def online(self):
		if self.is_online:
			return
		self.is_online = True
		now = datetime.now()
		self.online_start = datetime.timestamp(now)
		text = f"{now.strftime(DATETIME_FORMAT)}: {self.name} went online."
		print(text)
		if config["TRACK_LOG_PM"]:
			bot.notify_admins(f"{self.link} went online")

	def offline(self):
		if not self.is_online:
			return
		self.is_online = False
		now = datetime.now()
		session_time = round(datetime.timestamp(now) - self.online_start)
		del self.online_start
		stamp = now.strftime(DATETIME_FORMAT)
		append_file(f"{self.name}, {stamp}, {session_time}")
		text = f"{stamp}: {self.name} went offline. Session time: {session_time}"
		if config["TRACK_LOG_PM"]:
			bot.notify_admins(f"{self.link} went offline. Session time: {session_time}")
		logger.info(text)

	def remove(self):
		del self.userbot.targets[self.id]
		config.del_user(self.search_info)
