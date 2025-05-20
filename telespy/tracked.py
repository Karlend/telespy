"""Tracked users and sessions."""

from __future__ import annotations

import logging
import os
from os import path
from datetime import datetime
from telethon.tl.types import UserStatusOnline
from telespy.config import Config
from telespy.globals import DATETIME_FORMAT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telespy.dispatcher import BotDispatcher

logger = logging.getLogger(__name__)
config = Config()

LOG_DIR = "online_logs"

def log_path(user_id: int) -> str:
    return path.join(LOG_DIR, f"{user_id}.log")


def append_file(user_id: int, text: str) -> None:
    if not config["TRACK_LOG_FILE"]:
        return
    if not path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    file_name = log_path(user_id)
    if not path.exists(file_name):
        with open(file_name, "w") as f:
            f.write('"user", "date_start", "session_time"')
    with open(file_name, "a", encoding="utf-8") as f:
        f.write("\n" + text)


def format_duration(seconds: int) -> str:
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"





class TrackedUser:
    id: int
    name: str
    first_name: str
    last_name: str
    is_online: bool
    online_start: int
    watchers: set[int]
    all_watchers: set[int]
    username: str | None
    phone: str | None
    last_online: datetime | None

    def __init__(self, client, bot: "BotDispatcher") -> None:
        self.bot = bot
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
        self.all_watchers = set()
        self.username = getattr(client, "username", None)
        self.phone = getattr(client, "phone", None)
        if hasattr(client.status, "was_online"):
            self.last_online = client.status.was_online
        else:
            self.last_online = None
        self.last_message = None

        logger.info("Added account - %s, %s", self.id, self.name)

        if isinstance(client.status, UserStatusOnline):
            self.online()

    def __str__(self) -> str:
        return self.name

    def add_watcher(self, user_id: int, notify: bool = True) -> None:
        self.all_watchers.add(user_id)
        if notify:
            self.watchers.add(user_id)

    def remove_watcher(self, user_id: int) -> None:
        self.watchers.discard(user_id)
        self.all_watchers.discard(user_id)

    def set_notify(self, user_id: int, enable: bool) -> None:
        if enable:
            if user_id in self.all_watchers:
                self.watchers.add(user_id)
        else:
            self.watchers.discard(user_id)
            
    def is_notified(self, user_id: int) -> bool:
        return user_id in self.watchers

    def online(self) -> None:
        if self.is_online:
            return
        self.is_online = True
        now = datetime.now()
        self.online_start = int(datetime.timestamp(now))
        logger.info(f"{self.name}({self.id}) went online.")
        if config["TRACK_LOG_PM"]:
            self.bot.notify_watchers(self.watchers, f"🟢 {self.link}", self.id)

    def offline(self) -> None:
        if not self.is_online:
            return
        self.is_online = False
        now = datetime.now()
        self.last_online = now
        session_time = int(datetime.timestamp(now) - self.online_start)
        stamp = now.strftime(DATETIME_FORMAT)
        append_file(self.id, f"{self.name}, {stamp}, {session_time}")
        duration = format_duration(session_time)
        logger.info(f"{self.name}({self.id}) went offline. Session time: {duration}")
        if config["TRACK_LOG_PM"]:
            msg = f"🔴 {self.link} | {duration}"
            self.bot.notify_watchers(self.watchers, msg, self.id)

    async def remove(self) -> None:
        del self.userbot.targets[self.id]
        await self.userbot.delete_contact(self.id)
