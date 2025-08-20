import os
import logging
from typing import Optional

import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
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
    url = (
        "https://i.instagram.com/api/v1/users/web_profile_info/?username="
        f"{username}"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:  # type: ignore[name-defined]
        LOGGER.error("Request failed: %s", exc)
        return None
    if response.status_code != 200:
        LOGGER.warning("Non-success status code %s", response.status_code)
        return {"status_code": response.status_code}
    try:
        return response.json()
    except ValueError:
        LOGGER.error("Invalid JSON response")
        return None


async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.text.strip().lstrip("@")
    data = _fetch_instagram_info(username)
    if data is None:
        await update.message.reply_text(
            "خطا در برقراری ارتباط با اینستاگرام. لطفاً دوباره تلاش کنید."
        )
        return
    if "status_code" in data:
        status = data["status_code"]
        if status == 404:
            await update.message.reply_text("کاربر یافت نشد. نام کاربری را بررسی کنید.")
        else:
            await update.message.reply_text(
                "پاسخی از اینستاگرام دریافت نشد. لطفاً بعداً دوباره تلاش کنید."
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
