import shlex
from telethon.tl.types import Message, PeerUser, User
from telethon.tl.custom import Button

class SingletonMeta(type):
	"""Metaclass for singletons"""

	_instance = None

	def __call__(cls: "SingletonMeta", *args: any, **kwargs: any) -> "SingletonMeta":
		if cls._instance is None:
			cls._instance = super().__call__()
		return cls._instance

class Singleton(metaclass=SingletonMeta):
	"""Singleton base class"""

def is_private_message(message: Message) -> bool:
	"""Check if a message is a private message"""
	return isinstance(message.peer_id, PeerUser)


def parse_cmd(message: Message) -> list[str]:
	"""Parse a message as a command"""
	return shlex.split(message.message)


def is_admin(user: int | PeerUser | User | None) -> bool:
	"""Check if a user is an admin"""
	if user is None:
		return False
	if isinstance(user, PeerUser):
		user = user.user_id
	if isinstance(user, User):
		user = user.id

	from telespy.config import Config

	return user in Config().get("TRACK_ADMINS")
