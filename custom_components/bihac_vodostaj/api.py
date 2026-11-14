"""Client for the public KISTERS WISKI hydrology feed."""
from __future__ import annotations
from datetime import datetime
from typing import Any
import aiohttp
from .const import BASE

class WaterApiError(Exception):
    """Public station service is unavailable or returned invalid data."""

class WaterApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    async def json(self, url: str) -> Any:
        try:
            async with self.session.get(url, headers={"Accept":"application/json","User-Agent":"BihacVodostaj Home Assistant"}, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status != 200:
                    raise WaterApiError(f"HTTP {response.status}")
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise WaterApiError(str(err)) from err
        return data

    async def levels(self) -> list[dict[str, Any]]:
        return _rows(await self.json(BASE + "layers/10/index.json"))

    async def flows(self) -> list[dict[str, Any]]:
        return _rows(await self.json(BASE + "layers/20/index.json"))

    async def history(self, site: str, station: str) -> Any:
        return await self.json(BASE + f"stations/{site}/{station}/H/week.json")

def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "features"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x.get("properties", x) for x in value if isinstance(x, dict)]
    raise WaterApiError("Unexpected station data")

def timestamp(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            from zoneinfo import ZoneInfo
            parsed = parsed.replace(tzinfo=ZoneInfo("Europe/Sarajevo"))
        return int(parsed.timestamp())
    except (ValueError, OverflowError):
        return None

def number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if result == result and abs(result) != float("inf") else None
    except (TypeError, ValueError):
        return None
