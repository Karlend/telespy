# telespy

This script allows to track your friends' online status.
It's using update event from contacts to prevent flood waits for fetching accounts.
Example output from `online.csv`:

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

- Install [Python3.10](https://www.python.org/downloads/)
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

- `TRACK_ONLY_ADMINS` – when `true` only administrators can use the bot.
- `TRACK_GRAPH_ADMINS` – restricts building graphs to admins.
- `TRACK_CSV_ADMINS` – restricts log file retrieval to admins.
- `TRACK_NOTIFY_ADMINS` – send online/offline notifications only to admins.
