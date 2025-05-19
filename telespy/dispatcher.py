"""Bot dispatcher."""

import logging
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import (  # type: ignore
    Message,
)
from telethon.tl.custom import Button
from telespy.config import Config
from types import SimpleNamespace
from telespy.utils import is_admin, is_private_message, parse_cmd

logger = logging.getLogger(__name__)
config = Config()

commands = SimpleNamespace(
    start="start",
    add="add"
)

class BotDispatcher:
    """
    Bot dispatcher
    """

    def __init__(
        self: "BotDispatcher", client: TelegramClient
    ):
        client.parse_mode = "html"
        self.client = client
        self._me = None
        asyncio.ensure_future(self.async_init())

    async def async_init(self: "BotDispatcher"):
        """
        Initialize the dispatcher.
        """
        self._me = await self.client.get_me()

        def notify_admins(self: "BotDispatcher", text: str):
                for id in config["TRACK_ADMINS"]:
                        asyncio.ensure_future(self.client.send_message(id, text))

        def notify_watchers(self: "BotDispatcher", users: set[int], text: str):
                for uid in users:
                        asyncio.ensure_future(self.client.send_message(uid, text))

        async def add_account(self: "BotDispatcher", info: str, owner: int):
                ok, account = await self.userbot.track(info, owner)
                if not ok:
                        return False, account
                config.add_watch(owner, info)
                return True, account

    def setup_handlers(self: "BotDispatcher"):
        """
        Setup the handlers.
        """
        self.client.add_event_handler(self.handle_message, events.NewMessage)  # type: ignore
        self.client.add_event_handler(self.handle_buttons, events.CallbackQuery)  # type: ignore

    async def _start_handler(self: "BotDispatcher", message: Message):
        buttons = [
            [Button.inline("📄 Информация", data="info")],
            [Button.inline("💁 Аккаунты", data="accounts")],
            [Button.inline("📂 Файл", data="file")]
        ]
        await message.reply("👋 Добро пожаловать", buttons=buttons)

    async def _add_handler(self: "BotDispatcher", message: Message):
        text = message.text
        try:
            args = text.split(" ", 1)[1]
        except:
            await message.reply("Введите Имя/Логин/Номер")
            return
        if args[0] == "+": # phone
            print("Checking phone")
            try:
                phone = args.replace(" ", "")
                int(phone) # trigger error
                print("Creating contact")
                self.userbot.import_contact(phone)
            except:
                pass
                try:
                        ok, acc = await self.add_account(args, message.sender_id)
                except Exception as e:
                        logger.exception(e)
                        return await message.reply("Цель не найдена")
                if not ok:
                        return await message.reply(str(acc))
                await message.reply(f"{acc} теперь отслеживается\nID: <code>{acc.id}</code>")


    async def on_message(
        self: "BotDispatcher", event: events.newmessage.NewMessage.Event
    ):
        """
        Handle message event.
        """
        message = event.message
        if not is_private_message(message):
            return


        match self._parse_command(message):
            case [commands.start, *_]:
                await self._start_handler(message)
                return
            case [commands.add, *_]:
                await self._add_handler(message)
                return

    async def handle_message(self: "BotDispatcher", event: events.newmessage.NewMessage.Event
    ):
        if not self._me:
            await self.async_init()

        try:
            await self.on_message(event)
        except Exception as err:  # pylint: disable=broad-except
            logger.exception(err)
            await event.message.reply(str(err))

    async def handle_buttons(self: "BotDispatcher", query: events.callbackquery.CallbackQuery):
        """Buttons handler."""
        data = query.data.decode("utf-8")
        match data:
            case "info":
                users = len(config.get_users())
                admins = len(config["TRACK_ADMINS"])
                await query.edit(
                    f"🦹‍♂️ Отслеживаемые пользователи: {users}\n👮 Администраторов: {admins}"
                )
                return
            case "accounts":
                buttons = []
                watchlist = config.get_watchlist(query.sender_id)
                for info in watchlist:
                    for user in self.userbot.targets.values():
                        if user.search_info == info or str(user.id) == info:
                            buttons.append([Button.inline("🧑‍🚀 " + user.name, data=user.id)])
                            break
                await query.edit("🗄️ Список отслеживаемых аккаунтов:", buttons=buttons)
                return
            case "file":
                await query.edit("📂 Отправляю файл")
                await client.send_file(query.chat.id, "online.csv")
                return
            case "remove":
                msg = await query.get_message()
                if not msg:
                    return await query.edit("Failed to fetch message")
                id = int(msg.message.split("\n")[1].rsplit(" ", 1)[1])
                user = self.userbot.targets.get(id)
                if not user:
                    return await query.edit("Аккаунт не найден в списке")
                await self.userbot.untrack(user.id, query.sender_id)
                config.del_watch(query.sender_id, user.search_info)
                await query.edit(f"🙄 {user.name} был удален из списка трекинга")
                return
            case _:
                try:
                    user_id = int(data)
                except Exception:
                    await query.edit("Invalid")
                    return
                user = self.userbot.targets.get(user_id)
                if not user:
                    await query.edit("User not found")
                    return
                buttons = [[Button.inline("❌ Удалить", data="remove")]]
                status = "📲 <b>Online</b>" if user.is_online else "📱 <b>Offline</b>"
                await query.edit(
                    f"🤵‍♂️ {user.link}\n🪪 <code>{user.id}</code>\n{status}", buttons=buttons
                )


    def _parse_command(self: "BotDispatcher", message: Message) -> list[str]:
        splitted = parse_cmd(message)
        if splitted[0][0] != "/":
            return []
        splitted[0] = splitted[0][1:]
        if len(splitted) == 0:
            return []
        if "@" in splitted[0]:
            cmd, _, username = splitted[0].partition("@")
            if username != self._me.username:
                return []
            splitted[0] = cmd
        return splitted

client = TelegramClient('telespybot', config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
client.start(bot_token=config["TRACK_BOT_TOKEN"])

bot = BotDispatcher(client)
bot.setup_handlers()
