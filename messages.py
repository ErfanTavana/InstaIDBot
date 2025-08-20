"""Load and provide translated messages for the Telegram bot."""

import json
from pathlib import Path
from typing import Any


DEFAULT_LANG = "fa"

# Load all available translations from ``translations`` directory once at import.
_translations = {}
for lang_file in (Path(__file__).parent / "translations").glob("*.json"):
    lang = lang_file.stem
    with lang_file.open(encoding="utf-8") as f:
        _translations[lang] = json.load(f)


def get_message(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Return the message for ``key`` in the given ``lang``.

    Falls back to the default language when a translation is missing and formats
    the message with any provided keyword arguments.
    """

    data = _translations.get(lang) or _translations[DEFAULT_LANG]
    text = data.get(key, "")
    return text.format(**kwargs)
