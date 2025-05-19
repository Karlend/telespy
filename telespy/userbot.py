import logging
import asyncio
from telethon import TelegramClient, events, functions
from telespy.config import Config
from telespy.tracked import TrackedUser
from telespy.dispatcher import bot
from telethon.tl.types import InputPhoneContact, UserStatusRecently

logger = logging.getLogger(__name__)
config = Config()


class UserDispatcher:
    """User dispatcher"""

    def __init__(self: "UserDispatcher", client: TelegramClient) -> None:
        self.client = client
        self.targets: dict[int, TrackedUser] = {}
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
        info = await client.get_entity(search_info)
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


def _create_client() -> TelegramClient:
    client = TelegramClient("telespy", config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
    client.start()
    return client


client = _create_client()
userbot = UserDispatcher(client)
userbot.setup_handlers()
bot.userbot = userbot
userbot.bot = bot
