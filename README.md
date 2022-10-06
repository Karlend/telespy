telespy
================

This script allows to track your friends' online status.
It's using update event from contacts to prevent flood waits for fetching accounts.
Example output from `online.csv`:
```
"user", "date_start", "session_time"
@user1, 2022-10-06 08:13:12, 14
@user2, 2022-10-06 08:30:44, 71
@user3, 2022-10-06 08:40:48, 155
@user1, 2022-10-06 08:44:36, 59
@user1, 2022-10-06 08:46:27, 80
```
How to run
----------

- Install [Python](https://www.python.org/downloads/)
- Install dependencies - `pip3 install -r requirements.txt`.
- Navigate to [Telegram app creation](https://my.telegram.org/apps) and create app
- Copy and replace `api_id` and `api_hash` in `.env`. Change track targets to your ( you can use logins, names and phone numbers )
- Run app with `python3 -m telespy` ( you can add `--log-level INFO` to see more info )
- Enter your accounts data ( phone number and code )