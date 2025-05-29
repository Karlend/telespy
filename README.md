# telespy

This script allows to track your friends' online status.
It's uses update event from contacts to prevent flood waits for fetching accounts.
Example output from `online_logs/user_id.log`:

```csv
"user", "date_start", "session_time"
@user1, 2022-10-06 08:13:12, 14
@user2, 2022-10-06 08:30:44, 71
@user3, 2022-10-06 08:40:48, 155
@user1, 2022-10-06 08:44:36, 59
@user1, 2022-10-06 08:46:27, 80
```

## Features

- Multiple users can manage their own watch lists and receive notifications.
- Inline buttons provide quick file retrieval and account management.
- Administrators have access to statistics about users and tracked accounts.
- Several userbots can be controlled directly from Telegram.


## How to run

- Install [Python3.10](https://www.python.org/downloads/) or newer
- Install dependencies - `pip3 install -r requirements.txt`.
- Navigate to [Telegram app creation](https://my.telegram.org/apps) and create app
- Open the .env file inside the telespy folder and change existing settings.
- Run app with `python3 -m telespy` ( you can add `--log-level INFO` to see more info )
- Add userbots with `/ubadd <phone>` from an admin account and send auth code

### Docker

```bash
# build docker image
docker build -t telespy:latest .

# run telespy
docker run -it -v $PWD:/app telespy
```

## Configuration

The bot uses environment variables defined in `.env`:

- `TRACK_APP_ID` - The Telegram App ID. You can obtain it from [my.telegram.org/apps](https://my.telegram.org/apps).
- `TRACK_APP_HASH` - The Telegram App Hash. You can obtain it from [my.telegram.org/apps](https://my.telegram.org/apps).
- `TRACK_BOT_TOKEN` - The Telegram bot token provided by [BotFather](https://t.me/BotFather).
- `TRACK_ADMINS` - A list of Telegram user IDs with admin privileges.
- `TRACK_LOG_FILE` - Enables logging of online/offline events to files.
- `TRACK_LOG_PM` - Sends online/offline notifications via private messages.
- `TRACK_ONLY_ADMINS` - When set to `true`, only administrators can use the bot.
- `TRACK_GRAPH_ADMINS` - Restricts the ability to generate graphs to administrators.
- `TRACK_CSV_ADMINS` - Restricts access to log file downloads (CSV) to administrators.
- `TRACK_NOTIFY_ADMINS` - Sends online/offline notifications only to administrators.
- `DEFAULT_LANGUAGE` - Default interface language (e.g. `en`).
- `USE_USER_LANGUAGE` - When `true`, uses `user.lang_code` if a localization for that language exists or falls back to `DEFAULT_LANGUAGE`.
