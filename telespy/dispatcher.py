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
from telespy.plot import create_plots
from telespy.localization import localizer

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
        self.pending_plots: dict[int, dict[str, any]] = {}
        self.last_messages = {}
        self._lang_cache: dict[int, str] = {}
        asyncio.ensure_future(self.async_init())

    async def _get_lang(self, user_id: int) -> str:
        if not config.get("USE_USER_LANGUAGE", True):
            return config.get("DEFAULT_LANGUAGE", "en")
        if user_id in self._lang_cache:
            return self._lang_cache[user_id]
        try:
            user = await self.client.get_entity(user_id)
            lang = getattr(user, "lang_code", None)
        except Exception:
            lang = None
        lang = localizer.resolve_lang(lang)
        self._lang_cache[user_id] = lang
        return lang

    async def _t(self, user_id: int, key: str, **kwargs) -> str:
        lang = await self._get_lang(user_id)
        return localizer.get(lang, key, **kwargs)

    async def _show_account(self, entity, event_func, sender_id):
        is_enabled = entity.is_notified(sender_id) if sender_id else False
        notify_text = ("🔔 " if sender_id and is_enabled else "🔕 ") + await self._t(sender_id or 0, "button_notifications")
        buttons = [
            [Button.inline(await self._t(sender_id or 0, "button_remove"), data=f"remove:{entity.id}")],
            [Button.inline(await self._t(sender_id or 0, "csv"), data=f"csv:{entity.id}")],
            [Button.inline(await self._t(sender_id or 0, "button_create_plot"), data=f"plot:{entity.id}")],
            [Button.inline(notify_text, data=f"toggle:{entity.id}")],
            [Button.inline(await self._t(sender_id or 0, "button_back"), data="accounts")],
        ]
        status = await self._t(sender_id or 0, "online") if entity.is_online else await self._t(sender_id or 0, "offline")
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
            types.BotCommand(command="start", description=await self._t(0, "commands_start")),
            types.BotCommand(command="add", description=await self._t(0, "commands_add")),
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
            if config["TRACK_NOTIFY_ADMINS"] and not is_admin(uid):
                continue
            asyncio.ensure_future(self.send_or_edit_message(uid, text, id=id))
            
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

    async def _send_plot(self: "BotDispatcher", chat_id: int, user, days: int):
        uid = user.id
        try:
            plots = create_plots(uid, days)
        except FileNotFoundError:
            await self.client.send_message(chat_id, await self._t(chat_id, "log_file_not_found"))
            return

        caption = await self._t(chat_id, "plot_caption", days=days, uid=uid, name=user.name)
        await self.client.send_file(chat_id, plots, caption=caption)

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
    
    async def _start_handler(self: "BotDispatcher", message: Message = None, query: events.callbackquery.CallbackQuery = None):
        sender = message.sender_id if message else query.sender_id
        buttons = [
            [Button.inline(await self._t(sender, "button_info"), data="info")],
            [Button.inline(await self._t(sender, "button_accounts"), data="accounts")],
        ]
        if is_admin(sender):
            buttons.append([Button.inline(await self._t(sender, "button_manage_bots"), data="ublist")])
            buttons.append([Button.inline(await self._t(sender, "button_download_log"), data="admin_logs")])
        user_tracked_accounts = self.userbot_manager.get_tracked_users(sender)
        user_tracked_online = [
            account for account in user_tracked_accounts if account.is_online
        ]
        if message:
            await message.reply(await self._t(sender, "welcome", tracked=len(user_tracked_accounts), online=len(user_tracked_online)), buttons=buttons)
        elif query:
            await query.edit(await self._t(sender, "welcome", tracked=len(user_tracked_accounts), online=len(user_tracked_online)), buttons=buttons)

    async def _add_handler(self: "BotDispatcher", message: Message):
        try:
            args = message.text.split(" ", 1)[1]
        except IndexError:
            await message.reply(await self._t(message.sender_id, "enter_user"))
            return

        if args.startswith("+") and self.userbot_manager:
            phone = args.replace(" ", "")
            if phone.isdigit():
                try:
                    self.userbot_manager.choose_bot().import_contact(phone)
                except Exception:
                    logger.exception("Failed to import contact")

        try:
            ok, acc = await self.add_account(args, message.sender_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception(exc)
            return await message.reply(await self._t(message.sender_id, "target_not_found"))

        if ok:
            config.add_watch(message.sender_id, acc.id)
            await self._show_account(acc, message.reply, message.sender_id)
        else:
            if isinstance(acc, str):
                await message.reply(await self._t(message.sender_id, acc))
            else:
                await message.reply(str(acc))

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
        await self.client.send_message(owner, await self._t(owner, "code_sent"))

    async def _ubremove_handler(self: "BotDispatcher", message: Message):
        if not is_admin(message.sender_id):
            return
        try:
            name = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply(await self._t(message.sender_id, "userbot_id_required"))
        if self.userbot_manager.remove_userbot(name):
            await message.reply(await self._t(message.sender_id, "userbot_removed", name=name))
        else:
            await message.reply(await self._t(message.sender_id, "userbot_not_found"))

    async def _ublist_handler(self: "BotDispatcher", message: Message):
        if not is_admin(message.sender_id):
            return
        buttons = []
        for name in self.userbot_manager.bots.keys():
            buttons.append([Button.inline(name, data=f"ubinfo:{name}")])
        if not buttons:
            buttons = [[Button.inline(await self._t(message.sender_id, "button_back"), data="back")]]
            await message.reply(await self._t(message.sender_id, "userbots_not_running"), buttons=buttons)
            return
        buttons.append([Button.inline(await self._t(message.sender_id, "button_back"), data="back")])
        await message.reply(await self._t(message.sender_id, "userbot_list"), buttons=buttons)

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
            await message.reply(await self._t(message.sender_id, "userbot_added", id=me.id, name=me.first_name))
        else:
            await message.reply(await self._t(message.sender_id, "userbot_already_exists", id=me.id, name=me.first_name))


    async def on_message(
        self: "BotDispatcher", event: events.newmessage.NewMessage.Event
    ):
        """
        Handle message event.
        """
        message = event.message
        if not is_private_message(message):
            return

        if config["TRACK_ONLY_ADMINS"] and not is_admin(message.sender_id):
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

        pending_plot = self.pending_plots.get(message.sender_id)
        if pending_plot and pending_plot.get("stage") == "days":
            if message.text.isdigit():
                days = int(message.text)
                uid = pending_plot["uid"]
                del self.pending_plots[message.sender_id]
                user, _ = self.userbot_manager.find_user(uid)
                if not user:
                    return await message.reply(await self._t(message.sender_id, "user_not_found"))
                await self._send_plot(message.chat.id, user, days)
            else:
                await message.reply(await self._t(message.sender_id, "enter_days"))
            return

        match self._parse_command(message):
            case [commands.start, *_]:
                await self._start_handler(message=message)
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
        if config["TRACK_ONLY_ADMINS"] and not is_admin(query.sender_id):
            return
        data = query.data.decode("utf-8")
        match data:
            case "info":
                users = len(config.get_users())
                admins = len(config["TRACK_ADMINS"])
                await query.edit(
                    await self._t(query.sender_id, "stats", users=users, admins=admins),
                    buttons=[[Button.inline(await self._t(query.sender_id, "button_back"), data="back")]],
                )
                return
            case "accounts":
                buttons = []
                watchlist = config.get_watchlist(query.sender_id)
                for info in watchlist:
                    user = self.userbot_manager.find_user_by_info(info)
                    if user:
                        user_text = await self._t(query.sender_id, "user", name=user.name)
                        buttons.append([Button.inline(user_text, data=str(user.id))])
                if buttons:
                    buttons.append([Button.inline(await self._t(query.sender_id, "button_back"), data="back")])
                    await query.edit(await self._t(query.sender_id, "watchlist"), buttons=buttons)
                else:
                    await query.edit(await self._t(query.sender_id, "watchlist_empty"), buttons=[[Button.inline(await self._t(query.sender_id, "button_back"), data="back")]])
                return
            case "admin_logs":
                if not is_admin(query.sender_id):
                    return
                buttons = []
                if path.exists(LOG_DIR):
                    for fname in os.listdir(LOG_DIR):
                        buttons.append([Button.inline(fname, data=f"log:{fname}")])
                if not buttons:
                    buttons = [[Button.inline(await self._t(query.sender_id, "button_back"), data="back")]]
                    await query.edit(await self._t(query.sender_id, "logs_not_found"), buttons=buttons)
                else:
                    buttons.append([Button.inline(await self._t(query.sender_id, "button_back"), data="back")])
                    await query.edit(await self._t(query.sender_id, "available_logs"), buttons=buttons)
                return
            case "back":
                await self._start_handler(query=query)
                return
            case data if data.startswith("ubinfo:"):
                name = data.split(":", 1)[1]
                ub = self.userbot_manager.bots.get(name)
                if not ub:
                    return await query.edit(await self._t(query.sender_id, "userbot_not_found"))
                me = ub._me
                id = me.id if me else "-"
                username = f"@{me.username}" if me and me.username else "-"
                name = f"{me.first_name} {me.last_name}" if me and me.last_name else me.first_name if me else "-"
                contacts_text = await self._t(query.sender_id, "contacts")
                targets_text = await self._t(query.sender_id, "targets")
                text = (
                    f"🆔 <code>{id}" + "</code>\n"
                    f"👤 {name}\n"
                    f"🔖 {username}\n"
                    f"{contacts_text}: <code>{ub.contacts_created}</code>\n"
                    f"{targets_text}: <code>{len(ub.targets)}</code>"
                )
                buttons = [
                    [Button.inline(await self._t(query.sender_id, "button_remove"), data=f"ubremove:{id}")],
                    [Button.inline(await self._t(query.sender_id, "button_clear_contacts"), data=f"ubclear:{id}")],
                    [Button.inline(await self._t(query.sender_id, "button_back"), data="ublist")],
                ]
                await query.edit(text, buttons=buttons)
                return
            case data if data == "ublist":
                buttons = []
                for nm in self.userbot_manager.bots.keys():
                    buttons.append([Button.inline(nm, data=f"ubinfo:{nm}")])
                buttons.append([Button.inline(await self._t(query.sender_id, "ubadd"), data="ubadd")])
                if not self.userbot_manager.bots:
                    await query.edit(
                        await self._t(query.sender_id, "no_userbots"),
                        buttons=[[Button.inline(await self._t(query.sender_id, "button_back"), data="back")]]
                    )
                else:
                    buttons.append([Button.inline(await self._t(query.sender_id, "button_back"), data="back")])
                    await query.edit(
                        await self._t(query.sender_id, "userbot_list"),
                        buttons=buttons
                    )
                return
            case data if data == "ubadd":
                if not is_admin(query.sender_id):
                    return
                self.pending_userbots[query.sender_id] = {"stage": "phone"}
                await query.edit(await self._t(query.sender_id, "userbot_phone"))
                return
            case data if data.startswith("ubremove:"):
                name = data.split(":", 1)[1]
                if self.userbot_manager.remove_userbot(name):
                    await query.edit(
                        await self._t(query.sender_id, "userbot_removed", name=name)
                    )
                else:
                    await query.edit(await self._t(query.sender_id, "userbot_not_found"))
                return
            case data if data.startswith("ubclear:"):
                name = data.split(":", 1)[1]
                ub = self.userbot_manager.bots.get(name)
                if not ub:
                    return await query.edit(await self._t(query.sender_id, "userbot_not_found"))
                await ub.delete_all_contacts()
                await query.edit(
                    await self._t(query.sender_id, "userbot_contacts_cleared", name=name)
                )
            case data if data.startswith("log:"):
                if not is_admin(query.sender_id):
                    return
                fname = data.split(":", 1)[1]
                file_path = path.join(LOG_DIR, fname)
                if not path.exists(file_path):
                    return await query.edit(await self._t(query.sender_id, "file_not_found"))
                await self.client.send_file(query.chat.id, file_path)
                return
            case data if data.startswith("toggle:"):
                uid = int(data.split(":", 1)[1])
                user, _ = self.userbot_manager.find_user(uid)
                if not user:
                    return await query.edit(await self._t(query.sender_id, "account_not_found"))
                enabled = user.is_notified(query.sender_id)
                user.set_notify(query.sender_id, not enabled)
                await query.answer(
                    await self._t(query.sender_id, 'notifications_enabled' if not enabled else 'notifications_disabled')
                )
                await self._show_account(user, query.edit, query.sender_id)
                return
            case data if data.startswith("plotdays:"):
                if config["TRACK_GRAPH_ADMINS"] and not is_admin(query.sender_id):
                    return
                _, uid, days = data.split(":")
                user, _ = self.userbot_manager.find_user(int(uid))
                if not user:
                    return await query.answer(await self._t(query.sender_id, "user_not_found"))
                await query.answer(await self._t(query.sender_id, "building_graphs"))
                await self._send_plot(query.chat.id, user, int(days))
                return
            case data if data.startswith("plotcustom:"):
                if config["TRACK_GRAPH_ADMINS"] and not is_admin(query.sender_id):
                    return
                uid = int(data.split(":", 1)[1])
                self.pending_plots[query.sender_id] = {"uid": uid, "stage": "days"}
                await query.edit(await self._t(query.sender_id, "enter_days"))
                return
            case data if data.startswith("plot:"):
                if config["TRACK_GRAPH_ADMINS"] and not is_admin(query.sender_id):
                    return
                uid = int(data.split(":", 1)[1])
                buttons = [
                    [Button.inline(await self._t(query.sender_id, "plot_1d"), data=f"plotdays:{uid}:1")],
                    [Button.inline(await self._t(query.sender_id, "plot_1w"), data=f"plotdays:{uid}:7")],
                    [Button.inline(await self._t(query.sender_id, "plot_1m"), data=f"plotdays:{uid}:30")],
                    [Button.inline(await self._t(query.sender_id, "plot_6m"), data=f"plotdays:{uid}:180")],
                    [Button.inline(await self._t(query.sender_id, "plot_1y"), data=f"plotdays:{uid}:365")],
                    [Button.inline(await self._t(query.sender_id, "plot_custom"), data=f"plotcustom:{uid}")],
                    [Button.inline(await self._t(query.sender_id, "button_back"), data=str(uid))],
                ]
                await query.edit(await self._t(query.sender_id, "choose_period"), buttons=buttons)
                return
            case data if data.startswith("csv:"):
                if config["TRACK_CSV_ADMINS"] and not is_admin(query.sender_id):
                    return
                uid = int(data.split(":", 1)[1])
                file_name = log_path(uid)
                if not path.exists(file_name):
                    return await query.answer(await self._t(query.sender_id, "log_empty"))
                await query.answer(await self._t(query.sender_id, "log_sending"))
                user, _ = self.userbot_manager.find_user(uid)
                if not user:
                    return await query.answer(await self._t(query.sender_id, "user_not_found"))
                text = await self._t(query.sender_id, "online_log_caption", uid=user.id, name=user.name)
                await self.client.send_file(query.chat.id, file_name, caption=text, force_document=True)
                return
            case data if data.startswith("remove:"):
                try:
                    id = int(data.split(":", 1)[1])
                except Exception:
                    return await query.edit("Invalid")
                user, ub = self.userbot_manager.find_user(id)
                if not user or not ub:
                    return await query.edit(await self._t(query.sender_id, "account_not_found"))
                await ub.untrack(user.id, query.sender_id)
                config.del_watch(query.sender_id, user.id)
                await query.edit(await self._t(query.sender_id, "account_removed", name=user.name))
                return
            case _:
                try:
                    user_id = int(data)
                except Exception:
                    await query.edit("Invalid")
                    return
                user, _ = self.userbot_manager.find_user(user_id)
                if not user:
                    await query.edit(await self._t(query.sender_id, "user_not_found"))
                    return
                await self._show_account(user, query.edit, query.sender_id)


    def _parse_command(self: "BotDispatcher", message: Message) -> list[str]:
            splitted = parse_cmd(message)
            if not splitted:
                return []
            if not splitted[0].startswith("/"):
                return []
            splitted[0] = splitted[0][1:]
            if "@" in splitted[0]:
                cmd, _, username = splitted[0].partition("@")
                if username != self._me.username:
                    return []
                splitted[0] = cmd
            return splitted
