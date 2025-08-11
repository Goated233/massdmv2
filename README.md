# Staff Reminder Bot

Discord bot that DMs staff members a configurable reminder message. Built with `discord.py` 2.x and slash commands only.

## Features
- Per‑guild configuration stored in SQLite
- Rate limited DM sending (2s per DM) with retry on 429
- `/staff` commands for admins or manager role to manage reminders
- Optional cron scheduling using APScheduler

## Setup
1. **Python 3.11+** recommended.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (optional):
   ```env
   TOKEN=your_bot_token  # optional if `HARDCODED_TOKEN` in `main.py` is set
   MANAGER_ROLE_ID=1234567890  # optional manager role
   ```
   If you prefer, set `HARDCODED_TOKEN` in `main.py` to bypass `.env` usage.
4. Enable **Guild Members Intent** in the [Discord developer portal](https://discord.com/developers/applications) for your bot.
5. Invite the bot using a URL with `bot` and `applications.commands` scopes. Example:
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot%20applications.commands&permissions=274877908992
   ```
   The permission integer grants the bot ability to read members and send DMs; adjust as needed.
6. Run the bot:
   ```bash
   python main.py
   ```

## Testing
Unit tests use `pytest`:
```bash
pytest
```

## Commands
All commands are under `/staff`:
- `/staff setrole <role>` – set staff role
- `/staff setmessage <text>` – set DM message (supports `{guild}`, `{user}`, `{now_iso}`)
- `/staff remind now` – send reminders immediately
- `/staff remind user <member>` – DM a specific user
- `/staff remind channel <channel>` – post reminder in a channel
- `/staff remind preview` – preview the reminder message
- `/staff status` – show current configuration
- `/staff test` – DM caller preview
- `/staff ping` – show bot latency
- `/staff setmanager <role>` – set manager role
- `/staff getmanager` – show manager role
- `/staff showrole` – show staff role
- `/staff liststaff` – list staff members
- `/staff stats` – show reminder statistics
- `/staff version` – show bot version
- `/staff schedule set <cron>` – schedule daily reminders
- `/staff schedule clear` – remove schedule

Only Administrators or members with the manager role (from `.env`) may use the management commands.
