"""Bot dispatcher."""

import logging
import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
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
    add="add",
    ubadd="ubadd",
    ubremove="ubremove",
    ublist="ublist"
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
        self.userbot_manager = None
        self.pending_userbots: dict[int, dict[str, any]] = {}
        asyncio.ensure_future(self.async_init())
        
    async def async_init(self: "BotDispatcher"):
        """
        Initialize the dispatcher.
        """
        self._me = await self.client.get_me()
        await self._set_commands()

    async def _set_commands(self: "BotDispatcher") -> None:
        commands_list = [
            types.BotCommand(command="start", description="🙌 Меню"),
            types.BotCommand(command="add", description="➕ Отслеживать"),
            types.BotCommand(command="ubadd", description="🤖 Добавить юзербот"),
            types.BotCommand(command="ubremove", description="❌ Удалить юзербот"),
            types.BotCommand(command="ublist", description="📄 Список юзерботов"),
        ]
        await self.client(
            functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code="",
                commands=commands_list,
            )
        )

    def notify_admins(self: "BotDispatcher", text: str) -> None:
        for admin in config["TRACK_ADMINS"]:
            asyncio.ensure_future(self.client.send_message(admin, text))

    def notify_watchers(self: "BotDispatcher", users: set[int], text: str) -> None:
        for uid in users:
            asyncio.ensure_future(self.client.send_message(uid, text))

    async def add_account(self: "BotDispatcher", info: str, owner: int):
        if not self.userbot_manager:
            return False, "No userbots"
        ok, account = await self.userbot_manager.track(info, owner)
        if ok:
            config.add_watch(owner, info)
        return ok, account

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
                if self.userbot_manager:
                    self.userbot_manager.choose_bot().import_contact(phone)
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

    async def _ubadd_handler(self: "BotDispatcher", message: Message):
        if not is_admin(message.sender_id):
            return
        try:
            _, phone = message.text.split(" ", 1)
        except ValueError:
            return await message.reply("Usage: /ubadd &lt;phone&gt;")
        client = TelegramClient(StringSession(), config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
        await client.connect()
        code = await client.send_code_request(phone)
        self.pending_userbots[message.sender_id] = {"client": client, "phone": phone, "code_hash": code.phone_code_hash}
        await message.reply("📨 Код отправлен, введите его следующим сообщением")

    async def _ubremove_handler(self: "BotDispatcher", message: Message):
        if not is_admin(message.sender_id):
            return
        try:
            name = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply("Userbot id required")
        if self.userbot_manager.remove_userbot(name):
            await message.reply(f"Userbot {name} removed")
        else:
            await message.reply("Userbot not found")

    async def _ublist_handler(self: "BotDispatcher", message: Message):
        if not is_admin(message.sender_id):
            return
        names = ", ".join(self.userbot_manager.bots.keys()) or "none"
        await message.reply(f"Running userbots: {names}")

    async def _ubcode_handler(self: "BotDispatcher", message: Message):
        data = self.pending_userbots.pop(message.sender_id, None)
        if not data:
            return
        client: TelegramClient = data["client"]
        phone = data["phone"]
        code = message.text.strip()
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=data["code_hash"])
        except Exception as exc:  # pylint: disable=broad-except
            await message.reply(str(exc))
            await client.disconnect()
            return
        me = await client.get_me()
        session = client.session.save()
        await client.disconnect()
        if self.userbot_manager.add_userbot(str(me.id), session):
            await message.reply(f"Userbot {me.id} added")
        else:
            await message.reply("Already running")


    async def on_message(
        self: "BotDispatcher", event: events.newmessage.NewMessage.Event
    ):
        """
        Handle message event.
        """
        message = event.message
        if not is_private_message(message):
            return

        if message.sender_id in self.pending_userbots and message.text.isdigit():
            await self._ubcode_handler(message)
            return

        match self._parse_command(message):
            case [commands.start, *_]:
                await self._start_handler(message)
                return
            case [commands.add, *_]:
                await self._add_handler(message)
                return
            case [commands.ubadd, *_]:
                await self._ubadd_handler(message)
                return
            case [commands.ubremove, *_]:
                await self._ubremove_handler(message)
                return
            case [commands.ublist, *_]:
                await self._ublist_handler(message)
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
                    for ub in self.userbot_manager.iter_bots():
                        for user in ub.targets.values():
                            if user.search_info == info or str(user.id) == info:
                                buttons.append([Button.inline("🧑‍🚀 " + str(user.id), data=user.id)])
                                break
                if buttons:
                    await query.edit("🗄️ Список отслеживаемых аккаунтов:", buttons=buttons)
                else:
                    await query.edit("🗄️ Список отслеживаемых аккаунтов пуст")
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
                user = None
                ub = None
                for bot_inst in self.userbot_manager.iter_bots():
                    if id in bot_inst.targets:
                        user = bot_inst.targets.get(id)
                        ub = bot_inst
                        break
                if not user:
                    return await query.edit("Аккаунт не найден в списке")
                await ub.untrack(user.id, query.sender_id)
                config.del_watch(query.sender_id, user.search_info)
                await query.edit(f"🙄 {user.name} был удален из списка трекинга")
                return
            case _:
                try:
                    user_id = int(data)
                except Exception:
                    await query.edit("Invalid")
                    return
                user = None
                for ub in self.userbot_manager.iter_bots():
                    if user_id in ub.targets:
                        user = ub.targets[user_id]
                        break
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
