from types import SimpleNamespace
from unittest.mock import AsyncMock
import asyncio

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

import messages
import telegram_bot


class DummyMessage(SimpleNamespace):
    def __init__(self, text):
        super().__init__(
            text=text,
            reply_text=AsyncMock(),
            reply_photo=AsyncMock(),
        )


class DummyUpdate(SimpleNamespace):
    def __init__(self, text):
        message = DummyMessage(text)
        super().__init__(message=message, effective_chat=SimpleNamespace(id=1))


class DummyContext(SimpleNamespace):
    def __init__(self):
        super().__init__(
            user_data={},
            bot=SimpleNamespace(send_chat_action=AsyncMock()),
        )


def test_handle_username_success(monkeypatch):
    user = {
        "id": 1,
        "full_name": "Full",
        "biography": "Bio",
        "follower_count": 1,
        "following_count": 2,
        "media_count": 3,
        "is_private": False,
        "profile_pic_url": "http://pic",
    }
    monkeypatch.setattr(
        telegram_bot, "_fetch_instagram_info", lambda u: {"data": {"user": user}}
    )
    update = DummyUpdate("user")
    context = DummyContext()
    asyncio.run(telegram_bot.handle_username(update, context))
    expected_caption = messages.format_profile_info(user, messages.DEFAULT_LANG)
    update.message.reply_photo.assert_awaited_with(
        "http://pic",
        caption=expected_caption,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._back_menu(messages.DEFAULT_LANG),
    )
    assert context.user_data["profile_pic_url"] == "http://pic"


def test_handle_username_http_error(monkeypatch):
    monkeypatch.setattr(
        telegram_bot, "_fetch_instagram_info", lambda u: {"error": "status_429"}
    )
    update = DummyUpdate("user")
    context = DummyContext()
    asyncio.run(telegram_bot.handle_username(update, context))
    expected = escape_markdown(messages.get_message("error_429"), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._back_menu(messages.DEFAULT_LANG),
    )


def test_handle_username_network_error(monkeypatch):
    monkeypatch.setattr(telegram_bot, "_fetch_instagram_info", lambda u: None)
    update = DummyUpdate("user")
    context = DummyContext()
    asyncio.run(telegram_bot.handle_username(update, context))
    expected = escape_markdown(messages.get_message("error_connection"), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._back_menu(messages.DEFAULT_LANG),
    )
