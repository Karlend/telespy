"""run bot"""
import logging
import asyncio

from telespy.config import Config
from telespy.dispatcher import bot
from telespy.userbot import userbot

logger = logging.getLogger(__name__)
config = Config()

async def load_users():
	users = config.get_users()
	for info in users:
		user = await userbot.track(info)
		if not user or not hasattr(user, "id"):
			logger.exception(f"Invalid user - {info}")
			config.del_user(info)
			continue
		logger.info(f"Tracking {user} - {user.id}")
		await asyncio.sleep(10)
	logger.info("Loaded all users")

def main():
	userbot.client.loop.create_task(load_users())
	bot.client.run_until_disconnected()
