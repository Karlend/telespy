"""Tracked users and sessions."""

import logging
from os import path
from datetime import datetime
from telethon.tl.types import UserStatusOnline
from telespy.config import Config
from telespy.dispatcher import bot
from telespy.globals import DATETIME_FORMAT

logger = logging.getLogger(__name__)
config = Config()

FILE_NAME = "online.csv"


def append_file(text: str) -> None:
    if not config["TRACK_LOG_FILE"]:
        return
    with open(FILE_NAME, "a") as f:
        f.write("\n" + text)


def check_file() -> None:
    if not path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as f:
            f.write("\"user\", \"date_start\", \"session_time\"")


check_file()


class TrackedUser:
    id: int
    name: str
    first_name: str
    last_name: str
    is_online: bool
    online_start: int
    watchers: set[int]
    username: str | None
    phone: str | None
    last_online: datetime | None

    def __init__(self, client) -> None:
        self.id = client.id
        self.first_name = client.first_name
        self.last_name = client.last_name or ""
        name = client.first_name
        if client.last_name:
            name = f"{name} {client.last_name}"
        self.name = name
        self.link = f"<a href=\"tg://user?id={self.id}\">{self.name}</a>"
        self.is_online = False
        self.watchers = set()
        self.username = getattr(client, "username", None)
        self.phone = getattr(client, "phone", None)
        if hasattr(client.status, "was_online"):
            self.last_online = client.status.was_online
        else:
            self.last_online = None

        logger.info("Added account - %s, %s", self.id, self.name)

        if isinstance(client.status, UserStatusOnline):
            self.online()

    def __str__(self) -> str:
        return self.name

    def add_watcher(self, user_id: int) -> None:
        self.watchers.add(user_id)

    def remove_watcher(self, user_id: int) -> None:
        self.watchers.discard(user_id)

    def online(self) -> None:
        if self.is_online:
            return
        self.is_online = True
        now = datetime.now()
        self.online_start = int(datetime.timestamp(now))
        text = f"{now.strftime(DATETIME_FORMAT)}: {self.name} went online."
        logger.info(text)
        if config["TRACK_LOG_PM"]:
            bot.notify_watchers(self.watchers, f"{self.link} went online")

    def offline(self) -> None:
        if not self.is_online:
            return
        self.is_online = False
        now = datetime.now()
        self.last_online = now
        session_time = int(datetime.timestamp(now) - self.online_start)
        stamp = now.strftime(DATETIME_FORMAT)
        append_file(f"{self.name}, {stamp}, {session_time}")
        text = f"{stamp}: {self.name} went offline. Session time: {session_time}"
        if config["TRACK_LOG_PM"]:
            bot.notify_watchers(self.watchers, f"{self.link} went offline. Session time: {session_time}")
        logger.info(text)

    async def remove(self) -> None:
        del self.userbot.targets[self.id]
        await self.userbot.delete_contact(self.id)
