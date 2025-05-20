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
from telespy.globals import DATETIME_FORMAT
from telespy.tracked import log_path, LOG_DIR
from os import path
import os
import time
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
        self.userbot_manager = None
        self.pending_userbots: dict[int, dict[str, any]] = {}
        self.last_messages = {}
        asyncio.ensure_future(self.async_init())

    async def _show_account(self, entity, event_func, sender_id):
        is_enabled = entity.is_notified(sender_id) if sender_id else False
        notify_text = "🔔 Оповещения" if sender_id and is_enabled else "🔕 Оповещения"
        buttons = [
            [Button.inline("❌ Удалить", data=f"remove:{entity.id}")],
            [Button.inline("📄 CSV", data=f"csv:{entity.id}")],
            [Button.inline(notify_text, data=f"toggle:{entity.id}")],
            [Button.inline("🔙 Назад", data="accounts")],
        ]
        status = "📲 <b>Online</b>" if entity.is_online else "📱 <b>Offline</b>"
        username = f"@{entity.username}" if entity.username else "-"
        phone = entity.phone or "-"
        last_seen = entity.last_online.strftime(DATETIME_FORMAT) if entity.last_online else "-"
        text = (
            f"🤵‍♂️ {entity.link}\n"
            f"🪪 <code>{entity.id}</code>\n"
            f"🔖 {username}\n"
            f"📞 {phone}\n"
            f"🕒 {last_seen}\n"
            f"{status}"
        )
        await event_func(text, buttons=buttons)
        
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

    def notify_watchers(self: "BotDispatcher", users: set[int], text: str, id: int = None) -> None:
        for uid in users:
            asyncio.ensure_future(self.client.send_message(uid, text))
            
    async def send_or_edit_message(self: "BotDispatcher", user: int, text: str, id: int = None) -> Message:
        now = time.time()
        last_messages = self.last_messages.get(user, {})
        last_message = last_messages.get(id, {}) if id else {}
    
        if id and last_message.get("time", 0) > now - 600:
            old_text = last_message.get("text")
            new_text = old_text + "\n" + text
            try:
                message = await self.client.edit_message(user, last_message["id"], new_text)
                text = new_text
            except Exception:
                message = await self._send_new_message(user, text, now, id)
        else:
            message = await self._send_new_message(user, text, now, id)    
        return message
    
    def _update_last_message(self, user: int, id: int, message: Message, text: str, now: float):
        if id:
            self.last_messages.setdefault(user, {})[id] = {
                "id": message.id,
                "time": now,
                "text": text,
            }
    
    async def _send_new_message(self, user: int, text: str, now: float, id: int = None) -> Message:
        message = await self.client.send_message(user, text)
        self._update_last_message(user, id, message, text, now)
        return message

    async def add_account(self: "BotDispatcher", info: str, owner: int):
        if not self.userbot_manager:
            return False, "No userbots"
        ok, account = await self.userbot_manager.track(info, owner)
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
        ]
        if is_admin(message.sender_id):
            buttons.append([Button.inline("🛠️ Управление юзерботами", data="ublist")])
            buttons.append([Button.inline("📥 Выкачать лог", data="admin_logs")])
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
                if ok:
                    config.add_watch(message.sender_id, acc.id)
                    await self._show_account(acc, message.reply, message.sender_id)
                else:
                    await message.reply(str(acc))
        else:
            user = await self.client.get_entity(args)
            if not user:
                return await message.reply("Цель не найдена")
            if self.userbot_manager:
                ok, acc = await self.add_account(args, message.sender_id)
            else:
                return await message.reply("No userbots")
            if not ok:
                return await message.reply(str(acc))
            if ok:
                config.add_watch(message.sender_id, acc.id)
                await self._show_account(acc, message.reply, message.sender_id)

    async def _ubadd_handler(self: "BotDispatcher", phone: str, owner: int):
        client = TelegramClient(StringSession(), config["TRACK_APP_ID"], config["TRACK_APP_HASH"])
        await client.connect()
        code = await client.send_code_request(phone)
        self.pending_userbots[owner] = {
            "client": client,
            "phone": phone,
            "code_hash": code.phone_code_hash,
            "stage": "code",
        }
        await self.client.send_message(owner, "📨 Код отправлен, введите его следующим сообщением")

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
        buttons = []
        for name in self.userbot_manager.bots.keys():
            buttons.append([Button.inline(name, data=f"ubinfo:{name}")])
        if not buttons:
            buttons = [[Button.inline("🔙 Назад", data="back")]]
            await message.reply("🤖 Юзерботы не запущены", buttons=buttons)
            return
        buttons.append([Button.inline("🔙 Назад", data="back")])
        await message.reply("🤖 Список юзерботов:", buttons=buttons)

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
        success = await self.userbot_manager.add_userbot(str(me.id), session)
        if success:
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

        pending = self.pending_userbots.get(message.sender_id)
        if pending:
            stage = pending.get("stage")
            if stage == "phone":
                await self._ubadd_handler(message.text.strip(), message.sender_id)
                return
            if stage == "code" and message.text.isdigit():
                await self._ubcode_handler(message)
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
                    f"🦹‍♂️ Отслеживаемые пользователи: {users}\n👮 Администраторов: {admins}",
                    buttons=[
                        [Button.inline("🔙 Назад", data="back")],
                    ],
                )
                return
            case "accounts":
                buttons = []
                watchlist = config.get_watchlist(query.sender_id)
                for info in watchlist:
                    for ub in self.userbot_manager.iter_bots():
                        for user in ub.targets.values():
                            if user.id == info or user.search_info == info:
                                buttons.append([Button.inline("🧑‍🚀 " + str(user.name), data=str(user.id))])
                                break
                if buttons:
                    buttons.append([Button.inline("🔙 Назад", data="back")])
                    await query.edit("🗄️ Список отслеживаемых аккаунтов:", buttons=buttons)
                else:
                    await query.edit("🗄️ Список отслеживаемых аккаунтов пуст", buttons=[[Button.inline("🔙 Назад", data="back")]])
                return
            case "admin_logs":
                if not is_admin(query.sender_id):
                    return
                buttons = []
                if path.exists(LOG_DIR):
                    for fname in os.listdir(LOG_DIR):
                        buttons.append([Button.inline(fname, data=f"log:{fname}")])
                if not buttons:
                    buttons = [[Button.inline("🔙 Назад", data="back")]]
                    await query.edit("Логи не найдены", buttons=buttons)
                else:
                    buttons.append([Button.inline("🔙 Назад", data="back")])
                    await query.edit("Доступные логи:", buttons=buttons)
                return
            case "back":
                buttons = [
                    [Button.inline("📄 Информация", data="info")],
                    [Button.inline("💁 Аккаунты", data="accounts")],
                ]
                if is_admin(query.sender_id):
                    buttons.append([Button.inline("🛠️ Управление юзерботами", data="ublist")])
                    buttons.append([Button.inline("📥 Выкачать лог", data="admin_logs")])
                await query.edit("👋 Добро пожаловать", buttons=buttons)
                return
            case data if data.startswith("ubinfo:"):
                name = data.split(":", 1)[1]
                ub = self.userbot_manager.bots.get(name)
                if not ub:
                    return await query.edit("Userbot not found")
                me = ub._me
                id = me.id if me else "-"
                username = f"@{me.username}" if me and me.username else "-"
                name = f"{me.first_name} {me.last_name}" if me and me.last_name else me.first_name if me else "-"
                text = (
                    f"🆔 <code>{id}" + "</code>\n"
                    f"👤 {name}\n"
                    f"🔖 {username}\n"
                    f"📇 Контаков: <code>{ub.contacts_created}</code>\n"
                    f"📌 Таргетов: <code>{len(ub.targets)}</code>"
                )
                buttons = [
                    [Button.inline("❌ Удалить", data=f"ubremove:{id}")],
                    [Button.inline("🗑️ Очистить контакты", data=f"ubclear:{id}")],
                    [Button.inline("🔙 Назад", data="ublist")],
                ]
                await query.edit(text, buttons=buttons)
                return
            case data if data == "ublist":
                buttons = []
                for nm in self.userbot_manager.bots.keys():
                    buttons.append([Button.inline(nm, data=f"ubinfo:{nm}")])
                buttons.append([Button.inline("➕ Добавить", data="ubadd")])
                if not self.userbot_manager.bots:
                    await query.edit(
                        "🤖 Юзерботы не запущены",
                        buttons=[[Button.inline("🔙 Назад", data="back"),]],
                    )
                else:
                    buttons.append([Button.inline("🔙 Назад", data="back")])
                    await query.edit("🤖 Список юзерботов:", buttons=buttons)
                return
            case data if data == "ubadd":
                if not is_admin(query.sender_id):
                    return
                self.pending_userbots[query.sender_id] = {"stage": "phone"}
                await query.edit("Введите номер телефона")
                return
            case data if data.startswith("ubremove:"):
                name = data.split(":", 1)[1]
                if self.userbot_manager.remove_userbot(name):
                    await query.edit(f"Userbot {name} removed")
                else:
                    await query.edit("Userbot not found")
                return
            case data if data.startswith("ubclear:"):
                name = data.split(":", 1)[1]
                ub = self.userbot_manager.bots.get(name)
                if not ub:
                    return await query.edit("Userbot not found")
                await ub.delete_all_contacts()
                await query.edit(f"Userbot {name} contacts cleared")
            case data if data.startswith("log:"):
                if not is_admin(query.sender_id):
                    return
                fname = data.split(":", 1)[1]
                file_path = path.join(LOG_DIR, fname)
                if not path.exists(file_path):
                    return await query.edit("Файл не найден")
                await self.client.send_file(query.chat.id, file_path)
                return
            case data if data.startswith("toggle:"):
                uid = int(data.split(":", 1)[1])
                user = None
                for ub in self.userbot_manager.iter_bots():
                    if uid in ub.targets:
                        user = ub.targets[uid]
                        break
                if not user:
                    return await query.edit("User not found")
                enabled = user.is_notified(query.sender_id)
                user.set_notify(query.sender_id, not enabled)
                await query.edit(
                    "Уведомления " + ("включены" if not enabled else "выключены"),
                    buttons=[[Button.inline("🔙 Назад", data=str(uid))]],
                )
                return
            case data if data.startswith("csv:"):
                uid = int(data.split(":", 1)[1])
                file_name = log_path(uid)
                if not path.exists(file_name):
                    return await query.edit("Лог отсутствует", buttons=[[Button.inline("🔙 Назад", data=str(uid))]])
                await self.client.send_file(query.chat.id, file_name)
                return
            case data if data.startswith("remove:"):
                try:
                    id = int(data.split(":", 1)[1])
                except Exception:
                    return await query.edit("Invalid")
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
                config.del_watch(query.sender_id, user.id)
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
                await self._show_account(user, query.edit, query.sender_id)


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
