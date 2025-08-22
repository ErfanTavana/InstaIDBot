import os
import logging
import asyncio
import time
from typing import Optional
import re

import instaloader
from telegram import (
    InlineQueryResultPhoto,
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.constants import ChatAction
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

import messages

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
LOGGER = logging.getLogger(__name__)


def _get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", messages.DEFAULT_LANG)


_ALL_LANGS = list(messages._translations.keys())


def _button_regex(key: str) -> str:
    texts = [messages.get_message(key, lang) for lang in _ALL_LANGS]
    pattern = "^(" + "|".join(re.escape(t) for t in texts) + ")$"
    return pattern


def _main_menu(lang: str = messages.DEFAULT_LANG) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(messages.get_message("btn_start", lang))],
        [KeyboardButton(messages.get_message("btn_help", lang))],
        [KeyboardButton(messages.get_message("btn_about", lang))],
        [KeyboardButton(messages.get_message("btn_language", lang))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


_CACHE_TTL = 300  # 5 minutes


def _fetch_instagram_info(username: str) -> Optional[dict]:
    """Fetch Instagram profile data with a short-lived cache."""
    now = time.time()
    cached = _fetch_instagram_info._cache.get(username)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    L = instaloader.Instaloader()
    LOGGER.debug("Fetching Instagram profile for %s", username)
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        LOGGER.warning("Profile %s does not exist", username)
        return {"error": "not_found"}
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        LOGGER.warning("Profile %s is private", username)
        return {"error": "private"}
    except Exception as err:  # pragma: no cover - network/HTTP errors
        status = getattr(err, "status_code", None)
        if status == 429:
            LOGGER.warning("HTTP 429 for profile %s", username)
            return {"error": "status_429"}
        if status == 500:
            LOGGER.warning("HTTP 500 for profile %s", username)
            return {"error": "status_500"}
        LOGGER.error("Failed to fetch profile %s", username, exc_info=err)
        return None
    user = {
        "id": profile.userid,
        "username": profile.username,
        "full_name": profile.full_name,
        "biography": profile.biography,
        "follower_count": profile.followers,
        "following_count": profile.followees,
        "is_private": profile.is_private,
        "media_count": profile.mediacount,
        "profile_pic_url": profile.profile_pic_url,
    }
    data = {"data": {"user": user}}
    _fetch_instagram_info._cache[username] = (now, data)
    return data


_fetch_instagram_info._cache = {}


def _fetch_instagram_info_cache_clear() -> None:
    _fetch_instagram_info._cache.clear()


_fetch_instagram_info.cache_clear = _fetch_instagram_info_cache_clear


async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a friendly Persian welcome message explaining the bot."""
    lang = _get_lang(context)
    text = escape_markdown(
        "👋 به InstaIDBot خوش آمدی! این ربات اطلاعات عمومی حساب‌های اینستاگرام را می‌گیرد و به صورت خلاصه برات می‌فرسته. کافی هست نام کاربری رو بفرستی 😊",
        version=2,
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    if not context.user_data.get("started"):
        await send_welcome_message(update, context)
        context.user_data["started"] = True
        return
    lang = _get_lang(context)
    text = escape_markdown(messages.get_message("start", lang), version=2)
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    lang = _get_lang(context)
    text = escape_markdown(messages.get_message("help", lang), version=2)
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    lang = _get_lang(context)
    text = escape_markdown(messages.get_message("about", lang), version=2)
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    lang = _get_lang(context)
    keyboard = [
        [
            KeyboardButton(messages.get_message("btn_lang_fa", lang)),
            KeyboardButton(messages.get_message("btn_lang_en", lang)),
        ]
    ]
    text = escape_markdown(messages.get_message("language_prompt", lang), version=2)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    context.user_data["lang"] = lang
    text = escape_markdown(
        messages.get_message(f"language_set_{lang}", lang), version=2
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
    )


async def set_language_fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language(update, context, "fa")


async def set_language_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language(update, context, "en")


async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    lang = _get_lang(context)
    username = update.message.text.strip().lstrip("@")
    data = await asyncio.to_thread(_fetch_instagram_info, username)
    if data is None:
        text = escape_markdown(messages.get_message("error_connection", lang), version=2)
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
        )
        return
    err = data.get("error")
    if err:
        key = {
            "not_found": "error_not_found",
            "private": "error_private",
            "status_429": "error_429",
            "status_500": "error_500",
        }.get(err)
        if key:
            text = escape_markdown(messages.get_message(key, lang), version=2)
            await update.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
            )
            return
    try:
        user = data["data"]["user"]
    except (KeyError, TypeError):
        text = escape_markdown(messages.get_message("error_data", lang), version=2)
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
        )
        return
    context.user_data["profile_pic_url"] = user.get("profile_pic_url")
    text = messages.format_profile_info(user, lang)
    caption = text
    photo_url = user.get("profile_pic_url")
    if photo_url:
        await context.bot.send_chat_action(
            update.effective_chat.id, ChatAction.UPLOAD_PHOTO
        )
        await update.message.reply_photo(
            photo_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=_main_menu(lang),
        )
    else:
        await update.message.reply_text(
            caption, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=_main_menu(lang)
        )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query.strip().lstrip("@")
    if not query:
        await update.inline_query.answer([])
        return
    data = _fetch_instagram_info(query)
    results = []
    if data and not data.get("error"):
        user = data["data"]["user"]
        caption = f"{user.get('full_name', '')} (@{user['username']})"
        results.append(
            InlineQueryResultPhoto(
                id=user["username"],
                photo_url=user["profile_pic_url"],
                thumb_url=user["profile_pic_url"],
                caption=caption,
            )
        )
    await update.inline_query.answer(results, cache_time=60)


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده است.")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_start")), start)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_help")), help_command)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_about")), about_command)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_language")), language_command)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_lang_fa")), set_language_fa)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(_button_regex("btn_lang_en")), set_language_en)
    )
    application.add_handler(
        InlineQueryHandler(inline_query)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)
    )

    await application.initialize()
    await application.start()
    await application.bot.set_my_commands([("start", "شروع ربات")])
    await application.updater.start_polling()
    await application.wait_until_closed()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
