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
    def __init__(self):
        super().__init__(
            user_data={},
            bot=SimpleNamespace(send_chat_action=AsyncMock()),
        )


def test_set_language_fa():
    update = DummyUpdate(messages.get_message("btn_lang_fa"))
    context = DummyContext()
    asyncio.run(telegram_bot.set_language_fa(update, context))
    expected = escape_markdown(messages.get_message("language_set_fa", "fa"), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._back_menu("fa"),
    )
    assert context.user_data["lang"] == "fa"


def test_set_language_en():
    update = DummyUpdate(messages.get_message("btn_lang_en"))
    context = DummyContext()
    asyncio.run(telegram_bot.set_language_en(update, context))
    expected = escape_markdown(messages.get_message("language_set_en", "en"), version=2)
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._back_menu("en"),
    )
    assert context.user_data["lang"] == "en"

