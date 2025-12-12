# InstaIDBot

Telegram bot that returns public Instagram profile details without logging in. It uses the Telegram Bot API (via `python-telegram-bot`) and Instaloader to fetch profile metadata, supports Persian and English responses, and handles inline queries for quick lookups from any chat.

## Features
- `/start` menu with quick buttons for help, about, language selection, and returning to the main menu.
- Fetches public Instagram profile info (ID, full name, bio, followers, following, post count, privacy flag, profile picture).
- Sends the profile photo with a caption formatted for MarkdownV2 when available; falls back to text-only responses otherwise.
- Inline query support: typing `@YourBotUsername username` returns the profile photo and name when found.
- Bilingual interface (Persian default, English optional) with on-the-fly language switching.
- Simple in-memory cache (5 minutes) to avoid repeated Instaloader requests.
- Friendly error messages for private/missing profiles, rate limits (429), server errors (500), and generic connectivity issues.
- Logs to stdout and to `bot.log` using a configurable log level.

## Repository layout
- `telegram_bot.py` — main entry point; sets up handlers, menus, caching, and Instaloader integration.
- `messages.py` — loads translations and formats profile captions safely for MarkdownV2.
- `translations/` — Persian (`fa.json`) and English (`en.json`) strings for menus, errors, and buttons.
- `tests/` — pytest suite covering menu flows, language switching, username handling, and Instaloader fetch logic (with stubs).
- `.env.example` — template for required environment variable.

## Requirements
- Python 3 with dependencies from `requirements.txt` (`python-telegram-bot`, `instaloader`, `requests`, `python-dotenv`).
- Telegram Bot token with inline mode enabled.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Export your bot token (or set it in your process manager):
   ```bash
   export TELEGRAM_BOT_TOKEN="<your_token>"
   ```

## Running the bot
```bash
python telegram_bot.py
```
The bot starts long polling the Telegram Bot API. Logs are written to stdout and `bot.log`. Use the on-screen buttons to navigate between start/help/about/language menus.

### Configuration
- `TELEGRAM_BOT_TOKEN` (required): token issued by BotFather.
- `LOG_LEVEL` (optional): logging level (e.g., `DEBUG`, `INFO`, `WARNING`). Default is `INFO`.

## Usage
- **Send a username:** share `username` or `@username` in a private chat with the bot. The bot fetches the profile and replies with the profile photo (if public) and a caption similar to:
  ```
  • 👤 *آیدی عددی:* `123456789`
  • 📛 *نام کامل:* Example User
  • 📝 *بیوگرافی:* —
  • 👥 *فالوورها:* `10`
  • 🤝 *دنبال‌شوندگان:* `5`
  • 📸 *تعداد پست‌ها:* `7`
  • 🔒 *خصوصی:* خیر
  ```
- **Inline search:** in any chat, type `@<your_bot_username> username`. If found and public, the bot returns the profile photo with the full name and handle as caption.
- **Language:** tap the language button to switch between فارسی and English. The choice is stored per-user in `user_data`.

## Error handling
- Private accounts return a polite warning and no profile details.
- Missing users, HTTP 429/500, and network/parse errors each yield distinct localized messages.
- Requests are cached for 5 minutes to avoid redundant Instaloader calls.

## Testing
Run the pytest suite (Instaloader is stubbed; no network access required):
```bash
pytest
```

## License
No explicit license file is included in this repository.
