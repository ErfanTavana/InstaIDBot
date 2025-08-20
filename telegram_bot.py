import os
import logging
from typing import Optional

import instaloader
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


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
    text = (
        "سلام!\n"
        "نام کاربری اینستاگرام را ارسال کنید تا اطلاعات عمومی آن نمایش داده شود."
    )
    await update.message.reply_text(text, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "برای دریافت اطلاعات، تنها کافی است نام کاربری اینستاگرام را بدون @ ارسال کنید."
    )
    await update.message.reply_text(text)


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
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id, action=ChatAction.TYPING)
    username = update.message.text.strip().lstrip("@")
    data = _fetch_instagram_info(username)
    if data is None:
        await update.message.reply_text(
            "خطا در برقراری ارتباط با اینستاگرام. لطفاً دوباره تلاش کنید."
        )
        return
    if data.get("error") == "not_found":
        await update.message.reply_text("کاربر یافت نشد. نام کاربری را بررسی کنید.")
        return
    if data.get("error") == "private":
        await update.message.reply_text(
            "این پروفایل خصوصی است و نمی‌توان اطلاعات آن را نمایش داد."
        )
        return
    try:
        user = data["data"]["user"]
    except (KeyError, TypeError):
        await update.message.reply_text(
            "ساختار داده‌های دریافتی از اینستاگرام تغییر کرده است."
        )
        return
    id_ = user.get("id", "نامشخص")
    full_name = user.get("full_name", "")
    biography = user.get("biography", "") or "—"
    followers = (
        user.get("follower_count")
        or user.get("edge_followed_by", {}).get("count")
        or 0
    )
    following = (
        user.get("following_count")
        or user.get("edge_follow", {}).get("count")
        or 0
    )
    is_private = "بله" if user.get("is_private") else "خیر"
    media_count = user.get("media_count") or user.get("edge_owner_to_timeline_media", {}).get("count")

    text = (
        f"آیدی عددی: {id_}\n"
        f"نام کامل: {full_name}\n"
        f"بیوگرافی: {biography}\n"
        f"فالوورها: {followers}\n"
        f"دنبال‌شوندگان: {following}\n"
        f"تعداد پست‌ها: {media_count}\n"
        f"خصوصی: {is_private}"
    )

    profile_pic_url = user.get("profile_pic_url")
    if profile_pic_url:
        await context.bot.send_chat_action(chat_id, action=ChatAction.UPLOAD_PHOTO)
        await context.bot.send_photo(chat_id, profile_pic_url)
    await context.bot.send_chat_action(chat_id, action=ChatAction.TYPING)
    await update.message.reply_text(text)


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
