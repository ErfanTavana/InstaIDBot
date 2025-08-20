import os
import logging
from typing import Optional

import instaloader
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
LOGGER = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = ReplyKeyboardMarkup([["راهنما"]], resize_keyboard=True)
    text = escape_markdown(
        "سلام!\nنام کاربری اینستاگرام را ارسال کنید تا اطلاعات عمومی آن نمایش داده شود.",
        version=2,
    )
    await update.message.reply_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = escape_markdown(
        "برای دریافت اطلاعات، تنها کافی است نام کاربری اینستاگرام را بدون @ ارسال کنید.",
        version=2,
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


def _fetch_instagram_info(username: str) -> Optional[dict]:
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
    except Exception:
        LOGGER.exception("Failed to fetch profile %s", username)
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
    return {"data": {"user": user}}


async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.text.strip().lstrip("@")
    data = _fetch_instagram_info(username)
    if data is None:
        text = escape_markdown(
            "خطا در برقراری ارتباط با اینستاگرام. لطفاً دوباره تلاش کنید.",
            version=2,
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    if data.get("error") == "not_found":
        text = escape_markdown(
            "کاربر یافت نشد. نام کاربری را بررسی کنید.",
            version=2,
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    if data.get("error") == "private":
        text = escape_markdown(
            "این پروفایل خصوصی است و نمی‌توان اطلاعات آن را نمایش داد.",
            version=2,
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    try:
        user = data["data"]["user"]
    except (KeyError, TypeError):
        text = escape_markdown(
            "ساختار داده‌های دریافتی از اینستاگرام تغییر کرده است.",
            version=2,
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    id_ = escape_markdown(str(user.get("id", "نامشخص")), version=2)
    full_name_raw = user.get("full_name", "")
    full_name = escape_markdown(full_name_raw, version=2)
    biography_raw = (user.get("biography", "") or "—").replace("\n", " ")
    biography = escape_markdown(biography_raw, version=2)
    followers = escape_markdown(
        str(
            user.get("follower_count")
            or user.get("edge_followed_by", {}).get("count")
            or 0
        ),
        version=2,
    )
    following = escape_markdown(
        str(
            user.get("following_count")
            or user.get("edge_follow", {}).get("count")
            or 0
        ),
        version=2,
    )
    is_private = escape_markdown(
        "بله" if user.get("is_private") else "خیر", version=2
    )
    media_count = escape_markdown(
        str(
            user.get("media_count")
            or user.get("edge_owner_to_timeline_media", {}).get("count")
            or 0
        ),
        version=2,
    )

    text = (
        f"**آید عددی:** `{id_}`\n"
        f"**نام کامل:** `{full_name}`\n"
        f"**بیوگرافی:** `{biography}`\n"
        f"**فالوورها:** `{followers}`\n"
        f"**دنبال‌شوندگان:** `{following}`\n"
        f"**تعداد پست‌ها:** `{media_count}`\n"
        f"**خصوصی:** `{is_private}`"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده است.")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex("^راهنما$"), help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
