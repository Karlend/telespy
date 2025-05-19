import asyncio
import logging

from telespy.config import Config
from telespy.dispatcher import bot
from telespy.userbot import userbot_manager

logger = logging.getLogger(__name__)
config = Config()


def main():
    bot.client.run_until_disconnected()