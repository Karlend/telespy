from __future__ import annotations

from telespy.config import Config

LOCALES = {
    "en": {
        "commands_start": "🙌 Menu",
        "commands_add": "➕ Add account",
        "welcome": "👋 Welcome!\n📊 Accounts tracked: {tracked}\n🟢 Online: {online}",
        "button_info": "📄 Info",
        "button_accounts": "💁 Accounts",
        "button_manage_bots": "🛠️ Manage userbots",
        "button_download_log": "📥 Download log",
        "button_notifications": "Notifications",
        "button_remove": "❌ Remove",
        "button_clear_contacts": "🗑️ Clear contacts",
        "button_create_plot": "📈 Create plot",
        "button_back": "🔙 Back",
        "enter_user": "Enter Name/Login/Phone",
        "target_not_found": "Target not found",
        "code_sent": "📨 Code sent, please enter it in the next message",
        "userbots_not_running": "🤖 Userbots not running",
        "userbot_list": "🤖 Userbots list:",
        "userbot_not_found": "Userbot not found",
        "userbot_id_required": "Userbot ID is required",
        "userbot_removed": "Userbot {name} removed",
        "userbot_added": "Userbot <b>{name}</b> added with ID <code>{id}</code>",
        "userbot_already_exists": "Userbot <b>{name}</b> already exists with ID <code>{id}</code>",
        "userbot_contacts_cleared": "Contacts cleared for userbot <b>{name}</b>",
        "csv": "📄 CSV",
        "offline": "📱 <b>Offline</b>",
        "online": "📲 <b>Online</b>",
        "user": "🧑‍🚀 {name}",
        "stats": "🦹‍♂️ Tracked users: {users}\n👮 Admins: {admins}",
        "watchlist": "🗄️ Watched accounts:",
        "watchlist_empty": "🗄️ Watched accounts list is empty",
        "logs_not_found": "Logs not found",
        "available_logs": "Available logs:",
        "file_not_found": "File not found",
        "notifications_enabled": "Notifications enabled",
        "notifications_disabled": "Notifications disabled",
        "building_graphs": "Building graphs",
        "enter_days": "Enter number of days",
        "choose_period": "Choose period:",
        "log_empty": "📥 Log is empty",
        "log_sending": "📥 Sending log",
        "account_removed": "🙄 {name} was removed from tracking list",
        "account_not_found": "Account not found in list",
        "userbot_phone": "Enter phone number",
        "plot_caption": "Activity graphs for {days} d.\nUser: <a href='tg://user?id={uid}'>{name}</a> (<code>{uid}</code>)",
        "log_file_not_found": "Log file not found",
        "user_not_found": "User not found",
        "online_hidden": "Online status hidden",
        "no_userbots": "No userbots",
        "ubadd": "➕ Add",
        "plot_1d": "📅 1 day",
        "plot_1w": "📆 1 week",
        "plot_1m": "🗓️ 1 month",
        "plot_6m": "📊 6 months",
        "plot_1y": "📈 1 year",
        "plot_custom": "⚙️ Custom",
        "contacts": "📇 Contacts:",
        "targets": "📌 Targets:",
        "online_log_caption": "Online log\nUser: <a href='tg://user?id={uid}'>{name}</a> (<code>{uid}</code>)",
    },
    "ru": {
        "commands_start": "🙌 Меню",
        "commands_add": "➕ Отслеживать",
        "welcome": "👋 Добро пожаловать!\n📊 Аккаунтов отслеживается: {tracked}\n🟢 Онлайн: {online}",
        "button_info": "📄 Информация",
        "button_accounts": "💁 Аккаунты",
        "button_manage_bots": "🛠️ Управление юзерботами",
        "button_download_log": "📥 Выкачать лог",
        "button_notifications": "Оповещения",
        "button_remove": "❌ Удалить",
        "button_clear_contacts": "🗑️ Очистить контакты",
        "button_create_plot": "📈 Создать график",
        "button_back": "🔙 Назад",
        "enter_user": "Введите Имя/Логин/Номер",
        "target_not_found": "Цель не найдена",
        "code_sent": "📨 Код отправлен, введите его следующим сообщением",
        "userbots_not_running": "🤖 Юзерботы не запущены",
        "userbot_list": "🤖 Список юзерботов:",
        "userbot_not_found": "Юзербот не найден",
        "userbot_id_required": "ID юзербота не указан",
        "userbot_removed": "Юзербот {name} удалён",
        "userbot_added": "Юзербот <b>{name}</b> добавлен с ID <code>{id}</code>",
        "userbot_already_exists": "Юзербот <b>{name}</b> уже существует с айди <code>{id}</code>",
        "userbot_contacts_cleared": "Контакты очищены для <b>{name}</b>",
        "csv": "📄 CSV",
        "offline": "📱 <b>Не в сети</b>",
        "online": "📲 <b>В сети</b>",
        "user": "🧑‍🚀 {name}",
        "stats": "🦹‍♂️ Отслеживаемые пользователи: {users}\n👮 Администраторов: {admins}",
        "watchlist": "🗄️ Список отслеживаемых аккаунтов:",
        "watchlist_empty": "🗄️ Список отслеживаемых аккаунтов пуст",
        "logs_not_found": "Логи не найдены",
        "available_logs": "Доступные логи:",
        "file_not_found": "Файл не найден",
        "notifications_enabled": "🔔 Оповещения включены",
        "notifications_disabled": "🔔 Оповещения выключены",
        "building_graphs": "Графики строятся",
        "enter_days": "Введите количество дней",
        "choose_period": "Выберите период:",
        "log_empty": "📥 Лог пустой",
        "log_sending": "📥 Лог отправляется",
        "account_removed": "🙄 {name} был удален из списка трекинга",
        "account_not_found": "Аккаунт не найден в списке",
        "userbot_phone": "Введите номер телефона",
        "plot_caption": "Графики активности за {days} дн.\nПользователь: <a href='tg://user?id={uid}'>{name}</a> (<code>{uid}</code>)",
        "log_file_not_found": "Файл лога не найден",
        "user_not_found": "Пользователь не найден",
        "online_hidden": "Онлайн скрыт",
        "no_userbots": "🤖 Юзерботы не запущены",
        "ubadd": "➕ Добавить",
        "plot_1d": "📅 1 день",
        "plot_1w": "📆 1 неделя",
        "plot_1m": "🗓️ 1 месяц",
        "plot_6m": "📊 6 месяцев",
        "plot_1y": "📈 1 год",
        "plot_custom": "⚙️ Кастом",
        "contacts": "📇 Контаков",
        "targets": "📌 Целей",
        "online_log_caption": "Онлайн лог\nПользователь: <a href='tg://user?id={uid}'>{name}</a> (<code>{uid}</code>)",
    },
}


class Localizer:
    """Simple localization helper"""

    def __init__(self) -> None:
        self.config = Config()

    def resolve_lang(self, lang_code: str | None) -> str:
        default_lang = self.config.get("DEFAULT_LANGUAGE", "en")
        if lang_code and lang_code in LOCALES:
            return lang_code
        return default_lang if default_lang in LOCALES else "en"

    def get(self, lang_code: str | None, key: str, **kwargs) -> str:
        lang = self.resolve_lang(lang_code)
        data = LOCALES.get(lang, {})
        if key not in data:
            data = LOCALES.get(self.config.get("DEFAULT_LANGUAGE", "en"), {})
        template = data.get(key, key)
        return template.format(**kwargs)

localizer = Localizer()
