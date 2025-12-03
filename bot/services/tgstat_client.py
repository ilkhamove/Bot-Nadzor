from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class TgstatError(Exception):
    """Base exception for Tgstat client errors."""


class TgstatAPIError(TgstatError):
    pass


class TgstatClient:
    BASE_URL = "https://api.tgstat.ru"

    def __init__(self, api_key: str, session: aiohttp.ClientSession | None = None) -> None:
        self.api_key = api_key
        self._session = session

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_channel_stats(self, channel: str) -> dict[str, Any]:
        session = await self._ensure_session()
        url = f"{self.BASE_URL}/channels/get"
        params = {"token": self.api_key, "channelId": channel}
        try:
            async with session.get(url, params=params) as response:
                if response.status >= 500:
                    raise TgstatAPIError("Tgstat service unavailable")
                if response.status == 404:
                    raise TgstatAPIError("Channel not found")
                if response.status == 401:
                    raise TgstatAPIError("Invalid API key")

                data = await response.json()
                if not data.get("ok"):
                    message = data.get("error", {}).get("message") or "Unknown error"
                    raise TgstatAPIError(message)
                return data.get("result", {})
        except asyncio.TimeoutError as exc:
            raise TgstatAPIError("Request timed out") from exc
        except aiohttp.ClientError as exc:
            raise TgstatAPIError("Network error") from exc


__all__ = ["TgstatClient", "TgstatError", "TgstatAPIError"]
