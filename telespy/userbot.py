"""Userbot"""

import logging
import asyncio
from telethon import TelegramClient, events, functions
from telespy.config import Config
from telespy.tracked import User
from telespy.dispatcher import bot
from telethon.tl.types import InputPhoneContact, UserStatusRecently

logger = logging.getLogger(__name__)
config = Config()


class UserDispatcher:
	"""
	User dispatcher
	"""

	def __init__(
		self: "UserDispatcher", client: TelegramClient
	):
		self.client = client
		self.targets = {}
		self._me = None
		asyncio.ensure_future(self.async_init())

	async def async_init(self: "UserDispatcher"):
		"""
		Initialize the dispatcher.
		"""
		self._me = await self.client.get_me()

	def setup_handlers(self: "UserDispatcher"):
		"""
		Setup the handlers.
		"""
		self.client.add_event_handler(self.user_update, events.UserUpdate)  # type: ignore

	async def user_update(self: "UserDispatcher", event):
		user = self.targets.get(event.user_id)
		if user is None:
			return
		logger.debug(f"Received update for {user.name} - {user.id}")
		if event.online:
			user.online()
		else:
			user.offline()

	async def create_contact(self: "UserDispatcher", id: int, first_name: str, last_name: str, phone: str=""):
		await self.client(functions.contacts.AddContactRequest(
			id = id,
			first_name = first_name,
			last_name = last_name,
			phone = phone,
			add_phone_privacy_exception = False
	))

	async def import_contact(self: "UserDispatcher", phone: str):
		contact = InputPhoneContact(client_id=0, phone=phone, first_name=phone, last_name="")
		await self.client(functions.contacts.ImportContactsRequest([contact]))


	async def track(self: "UserDispatcher", search_info: str):
		info = await client.get_entity(search_info)
		if not info:
			return False, "Пользователь не найден"
		id = info.id
		if self.targets.get(id):
			return False, "Уже существует"
		if not info.status or isinstance(info.status, UserStatusRecently):
			return False, "Онлайн скрыт"
		user = User(info)
		user.search_info = search_info
		user.userbot = self
		if not info.contact:
			await self.create_contact(user.id, user.first_name, user.last_name or "")
		self.targets[id] = user
		return user

client = TelegramClient('telespy', config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
client.start()

userbot = UserDispatcher(client)
userbot.setup_handlers()
bot.userbot = userbot
userbot.bot = bot
