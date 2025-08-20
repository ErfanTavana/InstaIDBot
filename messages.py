import json
from pathlib import Path
from typing import Any

DEFAULT_LANG = "fa"

_translations = {}
for lang_file in (Path(__file__).parent / "translations").glob("*.json"):
    lang = lang_file.stem
    with lang_file.open(encoding="utf-8") as f:
        _translations[lang] = json.load(f)


def get_message(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    data = _translations.get(lang) or _translations[DEFAULT_LANG]
    text = data.get(key, "")
    return text.format(**kwargs)
