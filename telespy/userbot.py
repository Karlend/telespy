import logging
import asyncio
import json
import os
import time
from typing import Dict

from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telethon.tl.types import InputPhoneContact, UserStatusRecently

from telespy.config import Config
from telespy.tracked import TrackedUser
from telespy.dispatcher import bot

logger = logging.getLogger(__name__)
config = Config()


class UserDispatcher:
    """User dispatcher handling accounts for a single userbot."""

    def __init__(self: "UserDispatcher", client: TelegramClient, name: str) -> None:
        self.client = client
        self.session_name = name
        self.targets: Dict[int, TrackedUser] = {}
        self.last_used = 0.0
        self._me = None
        asyncio.ensure_future(self.async_init())

    async def async_init(self: "UserDispatcher") -> None:
        """Initialize the dispatcher."""
        self._me = await self.client.get_me()

    def setup_handlers(self: "UserDispatcher") -> None:
        """Setup the handlers."""
        self.client.add_event_handler(self.user_update, events.UserUpdate)  # type: ignore

    async def user_update(self: "UserDispatcher", event) -> None:
        user = self.targets.get(event.user_id)
        if user is None:
            return
        logger.debug("Received update for %s - %s", user.name, user.id)
        if event.online:
            user.online()
        else:
            user.offline()

    async def create_contact(self: "UserDispatcher", id: int, first_name: str, last_name: str, phone: str = "") -> None:
        await self.client(
            functions.contacts.AddContactRequest(
                id=id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                add_phone_privacy_exception=False,
            )
        )
        self.last_used = time.time()

    async def import_contact(self: "UserDispatcher", phone: str) -> None:
        contact = InputPhoneContact(client_id=0, phone=phone, first_name=phone, last_name="")
        await self.client(functions.contacts.ImportContactsRequest([contact]))
        self.last_used = time.time()

    async def untrack(self: "UserDispatcher", user_id: int, watcher: int) -> bool:
        user = self.targets.get(user_id)
        if not user:
            return False
        user.remove_watcher(watcher)
        if not user.watchers:
            user.remove()
        return True

    async def track(self: "UserDispatcher", search_info: str, watcher: int):
        info = await self.client.get_entity(search_info)
        self.last_used = time.time()
        if not info:
            return False, "Пользователь не найден"
        id = info.id
        user = self.targets.get(id)
        if user:
            user.add_watcher(watcher)
            return True, user
        if not info.status or isinstance(info.status, UserStatusRecently):
            return False, "Онлайн скрыт"
        user = TrackedUser(info)
        user.search_info = search_info
        user.userbot = self
        user.add_watcher(watcher)
        if not info.contact:
            await self.create_contact(user.id, user.first_name, user.last_name or "")
        self.targets[id] = user
        return True, user


class UserbotManager:
    """Manage multiple userbot instances."""

    def __init__(self: "UserbotManager") -> None:
        self.bots: Dict[str, UserDispatcher] = {}
        self.sessions: Dict[str, str] = {}
        self.load_sessions()
        for name, session in self.sessions.items():
            asyncio.ensure_future(self.add_userbot(name, session, save=False))

    def load_sessions(self: "UserbotManager") -> None:
        if os.path.exists("userbots.json"):
            with open("userbots.json", "r", encoding="utf-8") as f:
                self.sessions = json.loads(f.read())

    def save_sessions(self: "UserbotManager") -> None:
        with open("userbots.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.sessions))

    async def add_userbot(self: "UserbotManager", name: str, session: str, save: bool = True) -> bool:
        if name in self.bots:
            return False
        client = TelegramClient(StringSession(session), config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
        await client.start()
        ub = UserDispatcher(client, name)
        await ub.async_init()
        ub.setup_handlers()
        self.bots[name] = ub
        self.sessions[name] = session
        if save:
            self.save_sessions()
        return True

    def remove_userbot(self: "UserbotManager", name: str) -> bool:
        ub = self.bots.get(name)
        if not ub:
            return False
        asyncio.ensure_future(ub.client.disconnect())
        del self.bots[name]
        if name in self.sessions:
            del self.sessions[name]
            self.save_sessions()
        return True

    def iter_bots(self: "UserbotManager"):
        return self.bots.values()

    def choose_bot(self: "UserbotManager") -> UserDispatcher:
        return min(self.bots.values(), key=lambda b: b.last_used)

    async def track(self: "UserbotManager", info: str, watcher: int):
        if not self.bots:
            return False, "No userbots"

        entity = None
        request_bot = None
        for ub in sorted(self.bots.values(), key=lambda b: b.last_used):
            try:
                entity = await ub.client.get_entity(info)
                ub.last_used = time.time()
                request_bot = ub
                break
            except Exception:
                continue

        if not entity:
            return False, "Пользователь не найден"

        for ub in self.bots.values():
            user = ub.targets.get(entity.id)
            if user:
                user.add_watcher(watcher)
                return True, user

        chosen_bot = request_bot
        has_contact = entity.contact

        if not has_contact:
            for ub in self.bots.values():
                if ub is request_bot:
                    continue
                try:
                    ent = await ub.client.get_entity(entity.id)
                    ub.last_used = time.time()
                    if ent.contact:
                        chosen_bot = ub
                        has_contact = True
                        break
                except Exception:
                    continue

        if not has_contact:
            chosen_bot = self.choose_bot()

        if not entity.status or isinstance(entity.status, UserStatusRecently):
            return False, "Онлайн скрыт"

        user = TrackedUser(entity)
        user.search_info = info
        user.userbot = chosen_bot
        user.add_watcher(watcher)
        if not has_contact:
            await chosen_bot.create_contact(user.id, user.first_name, user.last_name or "")
        chosen_bot.targets[user.id] = user
        return True, user


userbot_manager = UserbotManager()
bot.userbot_manager = userbot_manager
