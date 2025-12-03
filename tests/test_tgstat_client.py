import asyncio
import pytest

from bot.services.tgstat_client import TgstatClient, TgstatAPIError


class FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response: FakeResponse):
        self._response = response
        self.closed = False

    def get(self, *args, **kwargs):  # noqa: D401
        return self._response


@pytest.mark.asyncio
async def test_get_channel_stats_success(monkeypatch):
    response = FakeResponse(200, {"ok": True, "result": {"title": "Test"}})

    async def fake_ensure(self):
        return FakeSession(response)

    client = TgstatClient("key")
    monkeypatch.setattr(TgstatClient, "_ensure_session", fake_ensure)

    data = await client.get_channel_stats("test")
    assert data["title"] == "Test"


@pytest.mark.asyncio
async def test_get_channel_stats_error(monkeypatch):
    response = FakeResponse(404, {"ok": False, "error": {"message": "Not found"}})

    async def fake_ensure(self):
        return FakeSession(response)

    client = TgstatClient("key")
    monkeypatch.setattr(TgstatClient, "_ensure_session", fake_ensure)

    with pytest.raises(TgstatAPIError):
        await client.get_channel_stats("unknown")
