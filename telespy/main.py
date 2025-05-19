import logging
from telethon import TelegramClient

from telespy.config import Config
from telespy.dispatcher import BotDispatcher
from telespy.userbot import UserbotManager


logger = logging.getLogger(__name__)


def main(config: Config) -> None:
    """Run the bot until it is disconnected."""
    client = TelegramClient(
        "telespybot",
        config["TRACK_APP_ID"],
        config["TRACK_APP_HASH"],
    )
    client.start(bot_token=config["TRACK_BOT_TOKEN"])

    bot = BotDispatcher(client)
    bot.setup_handlers()

    userbot_manager = UserbotManager(client.loop, bot)
    bot.userbot_manager = userbot_manager

    client.run_until_disconnected()
