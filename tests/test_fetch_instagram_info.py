"""Tests for fetching Instagram info without login."""

from types import ModuleType, SimpleNamespace
import sys
from pathlib import Path


# Create a minimal stub of the ``instaloader`` module so tests do not require
# network access or the real package.
class _Instaloader:
    def __init__(self) -> None:
        self.context = object()


class _Profile:
    @staticmethod
    def from_username(context, username):  # pragma: no cover - monkeypatched in tests
        raise NotImplementedError


class _Exceptions(SimpleNamespace):
    class ProfileNotExistsException(Exception):
        pass

    class PrivateProfileNotFollowedException(Exception):
        pass

    class HTTPError(Exception):
        def __init__(self, status_code):
            self.status_code = status_code


instaloader_stub = ModuleType("instaloader")
instaloader_stub.Instaloader = _Instaloader
instaloader_stub.Profile = _Profile
instaloader_stub.exceptions = _Exceptions()
sys.modules["instaloader"] = instaloader_stub

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import instaloader  # type: ignore  # noqa: E402  (stub inserted above)

import telegram_bot  # noqa: E402


def _profile(**kwargs):
    return SimpleNamespace(**kwargs)


def test_fetch_instagram_info_success(monkeypatch):
    telegram_bot._fetch_instagram_info.cache_clear()
    profile = _profile(
        userid=123,
        username="user",
        full_name="Full Name",
        biography="Bio",
        followers=10,
        followees=5,
        is_private=False,
        mediacount=7,
        profile_pic_url="http://example.com/pic.jpg",
    )

    def fake_from_username(context, username):
        assert username == "user"
        return profile

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_from_username)
    )

    data = telegram_bot._fetch_instagram_info("user")
    assert data["data"]["user"]["id"] == 123
    assert (
        data["data"]["user"]["profile_pic_url"] == "http://example.com/pic.jpg"
    )


def test_fetch_instagram_info_not_found(monkeypatch):
    telegram_bot._fetch_instagram_info.cache_clear()

    def fake_from_username(context, username):
        raise instaloader.exceptions.ProfileNotExistsException()

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_from_username)
    )

    data = telegram_bot._fetch_instagram_info("missing")
    assert data == {"error": "not_found"}


def test_fetch_instagram_info_private(monkeypatch):
    telegram_bot._fetch_instagram_info.cache_clear()

    def fake_from_username(context, username):
        raise instaloader.exceptions.PrivateProfileNotFollowedException()

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_from_username)
    )

    data = telegram_bot._fetch_instagram_info("private")
    assert data == {"error": "private"}


def test_fetch_instagram_info_http_errors(monkeypatch):
    telegram_bot._fetch_instagram_info.cache_clear()

    def fake_429(context, username):
        raise instaloader.exceptions.HTTPError(429)

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_429)
    )
    data = telegram_bot._fetch_instagram_info("rate")
    assert data == {"error": "status_429"}

    telegram_bot._fetch_instagram_info.cache_clear()

    def fake_500(context, username):
        raise instaloader.exceptions.HTTPError(500)

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_500)
    )
    data = telegram_bot._fetch_instagram_info("server")
    assert data == {"error": "status_500"}


def test_fetch_instagram_info_network_error(monkeypatch):
    telegram_bot._fetch_instagram_info.cache_clear()

    def fake_exception(context, username):
        raise Exception("network")

    monkeypatch.setattr(
        instaloader.Profile, "from_username", staticmethod(fake_exception)
    )
    data = telegram_bot._fetch_instagram_info("net")
    assert data is None
