import logging
import asyncio
from typing import Dict

from telethon import TelegramClient, events, functions
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

    async def import_contact(self: "UserDispatcher", phone: str) -> None:
        contact = InputPhoneContact(client_id=0, phone=phone, first_name=phone, last_name="")
        await self.client(functions.contacts.ImportContactsRequest([contact]))

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
        for name in config.get("TRACK_USERBOTS", []):
            self.add_userbot(name)

    def add_userbot(self: "UserbotManager", name: str) -> bool:
        if name in self.bots:
            return False
        client = TelegramClient(name, config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
        client.start()
        ub = UserDispatcher(client, name)
        ub.setup_handlers()
        self.bots[name] = ub
        return True

    def remove_userbot(self: "UserbotManager", name: str) -> bool:
        ub = self.bots.get(name)
        if not ub:
            return False
        asyncio.ensure_future(ub.client.disconnect())
        del self.bots[name]
        return True

    def iter_bots(self: "UserbotManager"):
        return self.bots.values()

    def choose_bot(self: "UserbotManager") -> UserDispatcher:
        return min(self.bots.values(), key=lambda b: len(b.targets))

    async def track(self: "UserbotManager", info: str, watcher: int):
        first = next(iter(self.bots.values()))
        entity = await first.client.get_entity(info)
        if not entity:
            return False, "Пользователь не найден"
        for ub in self.bots.values():
            user = ub.targets.get(entity.id)
            if user:
                user.add_watcher(watcher)
                return True, user
        if not entity.status or isinstance(entity.status, UserStatusRecently):
            return False, "Онлайн скрыт"
        ub = self.choose_bot()
        user = TrackedUser(entity)
        user.search_info = info
        user.userbot = ub
        user.add_watcher(watcher)
        if not entity.contact:
            await ub.create_contact(user.id, user.first_name, user.last_name or "")
        ub.targets[user.id] = user
        return True, user


userbot_manager = UserbotManager()
bot.userbot_manager = userbot_manager
