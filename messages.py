"""Load and provide translated messages for the Telegram bot."""

import json
from pathlib import Path
from typing import Any

from telegram.helpers import escape_markdown


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


# Labels used for formatting profile information in different languages.
_PROFILE_LABELS = {
    "fa": {
        "id": "آیدی عددی",
        "full_name": "نام کامل",
        "bio": "بیوگرافی",
        "followers": "فالوورها",
        "following": "دنبال‌شوندگان",
        "media_count": "تعداد پست‌ها",
        "is_private": "خصوصی",
    },
    "en": {
        "id": "ID",
        "full_name": "Full name",
        "bio": "Bio",
        "followers": "Followers",
        "following": "Following",
        "media_count": "Posts",
        "is_private": "Private",
    },
}


def format_profile_info(user: dict, lang: str = DEFAULT_LANG) -> str:
    """Return a formatted list of user profile information.

    All user-supplied values are escaped for safe usage with
    :class:`telegram.constants.ParseMode.MARKDOWN_V2`.
    """

    labels = _PROFILE_LABELS.get(lang, _PROFILE_LABELS[DEFAULT_LANG])

    def esc(value: Any) -> str:
        return escape_markdown(str(value), version=2)

    is_private = (
        get_message("yes", lang) if user.get("is_private") else get_message("no", lang)
    )

    lines = [
        f"• 👤 *{labels['id']}:* `{esc(user.get('id', '—'))}`",
        f"• 📛 *{labels['full_name']}:* {esc(user.get('full_name', '') or '—')}",
        f"• 📝 *{labels['bio']}:* {esc(user.get('biography', '') or '—')}",
        f"• 👥 *{labels['followers']}:* `{esc(user.get('follower_count') or 0)}`",
        f"• 🤝 *{labels['following']}:* `{esc(user.get('following_count') or 0)}`",
        f"• 📸 *{labels['media_count']}:* `{esc(user.get('media_count') or 0)}`",
        f"• 🔒 *{labels['is_private']}:* {esc(is_private)}",
    ]
    return "\n".join(lines)
