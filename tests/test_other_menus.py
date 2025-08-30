from types import SimpleNamespace
from unittest.mock import AsyncMock
import asyncio

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

import messages
import telegram_bot


class DummyMessage(SimpleNamespace):
    def __init__(self, text):
        super().__init__(text=text, reply_text=AsyncMock())


class DummyUpdate(SimpleNamespace):
    def __init__(self, text):
        super().__init__(message=DummyMessage(text), effective_chat=SimpleNamespace(id=1))


class DummyContext(SimpleNamespace):
    def __init__(self, user_data=None):
        super().__init__(
            user_data=user_data or {},
            bot=SimpleNamespace(send_chat_action=AsyncMock()),
        )


def test_help_shows_main_menu():
    update = DummyUpdate(messages.get_message("btn_help"))
    context = DummyContext()
    asyncio.run(telegram_bot.help_command(update, context))
    expected = escape_markdown(messages.get_message("help", messages.DEFAULT_LANG), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._main_menu(messages.DEFAULT_LANG),
    )
    assert context.user_data["menu"] == "main"


def test_back_to_menu_shows_main_menu():
    update = DummyUpdate(messages.get_message("btn_back"))
    context = DummyContext()
    asyncio.run(telegram_bot.back_to_menu(update, context))
    expected = escape_markdown(messages.get_message("start", messages.DEFAULT_LANG), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._main_menu(messages.DEFAULT_LANG),
    )
    assert context.user_data["menu"] == "main"


def test_language_command_shows_language_menu():
    update = DummyUpdate(messages.get_message("btn_language"))
    context = DummyContext({"menu": "main"})
    asyncio.run(telegram_bot.language_command(update, context))
    expected = escape_markdown(messages.get_message("language_prompt", messages.DEFAULT_LANG), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._language_menu(messages.DEFAULT_LANG),
    )
    assert context.user_data["language_prev_menu"] == "main"
