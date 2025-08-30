from types import SimpleNamespace
from unittest.mock import AsyncMock
import asyncio

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

import messages
import telegram_bot


class DummyMessage(SimpleNamespace):
    def __init__(self):
        super().__init__(text="/start", reply_text=AsyncMock())


class DummyUpdate(SimpleNamespace):
    def __init__(self):
        super().__init__(message=DummyMessage(), effective_chat=SimpleNamespace(id=1))


class DummyContext(SimpleNamespace):
    def __init__(self):
        super().__init__(
            user_data={"started": True},
            bot=SimpleNamespace(send_chat_action=AsyncMock()),
        )


def test_start_shows_main_menu():
    update = DummyUpdate()
    context = DummyContext()
    asyncio.run(telegram_bot.start(update, context))
    expected = escape_markdown(
        messages.get_message("start", messages.DEFAULT_LANG), version=2
    )
    update.message.reply_text.assert_awaited_with(
        expected,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=telegram_bot._main_menu(messages.DEFAULT_LANG),
    )
    assert context.user_data["menu"] == "main"

