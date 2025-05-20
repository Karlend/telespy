from __future__ import annotations

import logging
import asyncio
import json
import os
import time
from typing import Dict, TYPE_CHECKING

from telethon import TelegramClient, events, functions
import time
from telethon.sessions import StringSession
from telethon.tl.types import InputPhoneContact, UserStatusRecently

from telespy.config import Config
from telespy.tracked import TrackedUser

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from telespy.dispatcher import BotDispatcher


logger = logging.getLogger(__name__)
config = Config()


class UserDispatcher:
    """User dispatcher handling accounts for a single userbot."""

    def __init__(
        self: "UserDispatcher",
        client: TelegramClient,
        name: str,
        bot: "BotDispatcher",
    ) -> None:
        self.client = client
        self.session_name = name
        self.bot = bot
        self.targets: Dict[int, TrackedUser] = {}
        self.last_used = 0.0
        self._me = None
        self.contacts_created = 0
        asyncio.ensure_future(self.async_init())

    async def async_init(self: "UserDispatcher") -> None:
        """Initialize the dispatcher."""
        self._me = await self.client.get_me()
        contacts = await self.client(functions.contacts.GetContactsRequest(hash=0))
        self.contacts_created = len(contacts.contacts)
        
    async def delete_all_contacts(self: "UserDispatcher") -> None:
        """Delete all contacts."""
        contacts = await self.client(functions.contacts.GetContactsRequest(hash=0))
        for contact in contacts.contacts:
            try:
                await self.client(functions.contacts.DeleteContactsRequest(id=[contact.user_id]))
            except Exception:
                logger.exception("Failed to delete contact %s", contact.user_id)
                continue
            await asyncio.sleep(1)
        self.contacts_created = 0
        await self.create_tracked_contracts()
        
    async def create_tracked_contracts(self: "UserDispatcher") -> None:
        """Create tracked contacts."""
        for user in self.targets.values():
            if not user.contact:
                try:
                    await self.create_contact(user.id, user.first_name, user.last_name or "")
                except Exception:
                    logger.exception("Failed to create contact for %s", user.id)
                    continue

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
        self.contacts_created += 1

    async def import_contact(self: "UserDispatcher", phone: str) -> None:
        contact = InputPhoneContact(client_id=0, phone=phone, first_name=phone, last_name="")
        await self.client(functions.contacts.ImportContactsRequest([contact]))
        self.last_used = time.time()

    async def delete_contact(self: "UserDispatcher", user_id: int) -> None:
        try:
            input_user = await self.client.get_input_entity(user_id)
            await self.client(functions.contacts.DeleteContactsRequest(id=[input_user]))
        except Exception:
            pass

    async def untrack(self: "UserDispatcher", user_id: int, watcher: int) -> bool:
        user = self.targets.get(user_id)
        if not user:
            return False
        user.remove_watcher(watcher)
        if not user.all_watchers:
            await user.remove()
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
        user = TrackedUser(info, self.bot)
        user.search_info = search_info
        user.userbot = self
        user.add_watcher(watcher)
        if not info.contact:
            await self.create_contact(user.id, user.first_name, user.last_name or "")
        self.targets[id] = user
        return True, user


class UserbotManager:
    """Manage multiple userbot instances."""

    def __init__(
        self: "UserbotManager",
        loop: asyncio.AbstractEventLoop,
        bot: "BotDispatcher",
    ) -> None:
        self.bots: Dict[str, UserDispatcher] = {}
        self.sessions: Dict[str, str] = {}
        self.bot = bot
        self.load_sessions()
        loop.create_task(self.async_init())
        
    async def async_init(self: "UserbotManager") -> None:
        """Initialize the userbot manager."""
        for name, session in self.sessions.items():
            await self.add_userbot(name, session, save=False)
        await self.load_users()

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
        client = TelegramClient(
            StringSession(session),
            config["TRACK_APP_ID"],
            config["TRACK_APP_HASH"],
        )
        await client.start()
        ub = UserDispatcher(client, name, self.bot)
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

        chosen_bot = None
        for ub in self.bots.values():
            try:
                ent = await ub.client.get_entity(entity.id)
                ub.last_used = time.time()
                if ent.contact:
                    chosen_bot = ub
                    break
            except Exception:
                continue

        has_contact = chosen_bot is not None
        if not has_contact:
            chosen_bot = request_bot

        if not entity.status or isinstance(entity.status, UserStatusRecently):
            return False, "Онлайн скрыт"

        user = TrackedUser(entity, self.bot)
        user.search_info = info
        user.userbot = chosen_bot
        user.add_watcher(watcher)
        if not has_contact:
            await chosen_bot.create_contact(user.id, user.first_name, user.last_name or "")
        chosen_bot.targets[user.id] = user
        return True, user
    
    async def load_users(self: "UserbotManager"):
        users = config.get_users()
        for owner in list(users.keys()):  # Create a copy of the keys to avoid modification issues
            infos = users.get(owner, [])
            for info in infos:
                ok, user = await self.track(info, int(owner))
                if not ok or not hasattr(user, "id"):
                    logger.exception(f"Invalid user - {info} | {user}")
                    config.del_watch(int(owner), info)  # Modify the dictionary safely
                    continue
                logger.info(f"Tracking {user} - {user.id}")
                await asyncio.sleep(1)
        logger.info("Loaded all users")

