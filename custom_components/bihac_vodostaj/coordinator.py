"""Poll stations, derive trends and emit urgent alert events."""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import WaterApi, WaterApiError, number, timestamp
from .const import *

_LOGGER = logging.getLogger(__name__)

def _history(payload: Any) -> list[list[float]]:
    rows = payload[0].get("data", []) if isinstance(payload, list) and payload and isinstance(payload[0], dict) else (payload.get("data", []) if isinstance(payload, dict) else [])
    result = []
    for point in rows if isinstance(rows, list) else []:
        if isinstance(point, list) and len(point) > 1:
            ts, val = timestamp(point[0]), number(point[1])
            if ts is not None and val is not None:
                result.append([ts, val])
    return sorted(result)

def _window(reading: dict[str, Any], hours: int) -> tuple[float | None, float | None]:
    end, level = reading.get("measured_at"), reading.get("level_cm")
    history = reading.get("history", [])
    if end is None or level is None:
        return None, None
    start = end - hours * 3600
    points = [p for p in history if start <= p[0] < end]
    if len(points) < 1 or points[0][0] > start + 1800:
        return None, None
    elapsed = (end - points[0][0]) / 3600
    rate = round((level - points[0][1]) / elapsed, 1) if elapsed > 0 else None
    rise = round(level - min([p[1] for p in points] + [level]), 1)
    return rate, rise

class WaterCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: WaterApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=timedelta(minutes=UPDATE_MINUTES))
        self.api, self.entry = api, entry
        self._previous: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            levels = await self.api.levels()
        except WaterApiError as err:
            raise UpdateFailed(str(err)) from err
        try:
            flows = await self.api.flows()
        except WaterApiError:
            flows = []
        selected = self.entry.options.get(CONF_STATIONS, self.entry.data[CONF_STATIONS])
        rows = {str(r.get("metadata_station_no")): r for r in levels if str(r.get("metadata_station_no", "")).isdigit()}
        flow_rows = {str(r.get("metadata_station_no")): number(r.get("L1_ts_value")) for r in flows}
        sem = asyncio.Semaphore(5)
        async def read_one(station: str) -> dict[str, Any]:
            row = rows.get(station)
            if row is None:
                return {"station_no":station, "available":False}
            site = str(row.get("metadata_site_no", ""))
            hist = []
            if site.isdigit():
                try:
                    async with sem:
                        hist = _history(await self.api.history(site, station))
                except WaterApiError:
                    pass
            level, measured = number(row.get("L1_ts_value")), timestamp(row.get("L1_timestamp"))
            code = str(row.get("L1_web_waterlevel_class", ""))
            severity, label = CLASSES.get(code, (0, "Granične vrijednosti nisu definisane"))
            reading = {
                "station_no":station, "station":str(row.get("metadata_station_name") or f"Stanica {station}"),
                "river":str(row.get("metadata_river_name") or ""), "site_no":site,
                "level_cm":round(level,1) if level is not None else None,
                "flow_m3s":flow_rows.get(station), "measured_at":measured,
                "class_code":code, "severity":severity, "official_class":label,
                "history":hist, "available":level is not None and measured is not None,
            }
            reading["rate_cm_h"], reading["rise_3h_cm"] = _window(reading, 3)
            _, reading["rise_24h_cm"] = _window(reading, 24)
            reading["stale"] = measured is None or datetime.now().timestamp() - measured > STALE_SECONDS
            return reading
        data = {sid: r for sid, r in zip(selected, await asyncio.gather(*(read_one(s) for s in selected)))}
        self._emit_alerts(data)
        self._previous = data
        return data

    def _emit_alerts(self, data: dict[str, Any]) -> None:
        opts = {**self.entry.data, **self.entry.options}
        threshold = float(opts.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))
        before = [float(x) for x in opts.get(CONF_WARN_BEFORE, DEFAULT_WARN_BEFORE)]
        rise_cm = float(opts.get(CONF_RISE, DEFAULT_RISE))
        rise_hours = int(opts.get(CONF_RISE_HOURS, DEFAULT_RISE_HOURS))
        for station, current in data.items():
            old = self._previous.get(station)
            if not current.get("available") or current.get("measured_at") == (old or {}).get("measured_at"):
                continue
            if old and current["level_cm"] >= threshold > old.get("level_cm", threshold):
                self._fire(station, current, "threshold", f"Vodostaj je prešao prag od {threshold:g} cm.")
            for margin in before:
                if current["level_cm"] >= threshold - margin and current["level_cm"] < threshold and (old is None or old["level_cm"] < threshold - margin):
                    self._fire(station, current, "approach", f"Vodostaj je na {current['level_cm']:.1f} cm, {threshold-current['level_cm']:.1f} cm do praga {threshold:g} cm.")
            rise = current.get(f"rise_{rise_hours}h_cm")
            if rise is None and rise_hours == 3:
                rise = current.get("rise_3h_cm")
            if rise is not None and rise >= rise_cm:
                self._fire(station, current, "rapid_rise", f"Voda je porasla {rise:.1f} cm za {rise_hours} sata.")
    def _fire(self, station: str, r: dict[str, Any], kind: str, message: str) -> None:
        self.hass.bus.async_fire(EVENT_ALERT, {"severity":"urgent","kind":kind,"station":r["station"],"station_no":station,"river":r["river"],"level_cm":r["level_cm"],"measured_at":r["measured_at"],"title":f"🚨 Vodostaj · {r['station']}","message":message})
