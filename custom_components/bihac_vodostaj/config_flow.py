"""Station selection and alarm options."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig
from .api import WaterApi, WaterApiError
from .const import *

def _choices(rows: list[dict[str, Any]], keep: list[str] | None = None) -> list[dict[str, str]]:
    found = {}
    for row in rows:
        sid = str(row.get("metadata_station_no", ""))
        if not sid.isdigit(): continue
        name = str(row.get("metadata_station_name") or f"Stanica {sid}").removeprefix("HS ").strip()
        river = str(row.get("metadata_river_name") or "").strip()
        found[sid] = {"value":sid, "label":f"{name} — {river} ({sid})" if river else f"{name} ({sid})"}
    for sid in keep or []:
        found.setdefault(str(sid), {"value":str(sid), "label":f"Stanica {sid}"})
    return sorted(found.values(), key=lambda item: item["label"].casefold())

def _schema(choices, selected, options=None):
    opts = options or {}
    return vol.Schema({
        vol.Required(CONF_STATIONS, default=selected): SelectSelector(SelectSelectorConfig(options=choices, multiple=True)),
        vol.Required(CONF_THRESHOLD, default=opts.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)): vol.All(vol.Coerce(float), vol.Range(min=1, max=3000)),
        vol.Required(CONF_WARN_BEFORE, default=opts.get(CONF_WARN_BEFORE, DEFAULT_WARN_BEFORE)): vol.All(vol.Coerce(float), vol.Range(min=1, max=500)),
        vol.Required(CONF_RISE, default=opts.get(CONF_RISE, DEFAULT_RISE)): vol.All(vol.Coerce(float), vol.Range(min=1, max=500)),
        vol.Required(CONF_RISE_HOURS, default=opts.get(CONF_RISE_HOURS, DEFAULT_RISE_HOURS)): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
    })

class BihacVodostajFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BihacVodostajOptionsFlow()

    async def _form(self, user_input=None, errors=None):
        try:
            rows = await WaterApi(async_get_clientsession(self.hass)).levels()
        except WaterApiError:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}), errors={"base":"cannot_connect"})
        opts = user_input or {}
        choices = _choices(rows)
        selected = opts.get(CONF_STATIONS, [DEFAULT_STATION] if any(x["value"] == DEFAULT_STATION for x in choices) else [])
        return self.async_show_form(step_id="user", data_schema=_schema(choices, selected, opts), errors=errors or {})

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        if user_input is None:
            return await self._form()
        selected = list(dict.fromkeys(user_input.get(CONF_STATIONS, [])))
        if not selected:
            return await self._form(user_input, {"base":"select_station"})
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Bihać Vodostaj", data={CONF_STATIONS:selected}, options={k:v for k,v in user_input.items() if k != CONF_STATIONS})

class BihacVodostajOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            selected = list(dict.fromkeys(user_input.get(CONF_STATIONS, [])))
            if not selected:
                return await self.async_step_init()
            return self.async_create_entry(title="", data={**user_input, CONF_STATIONS:selected})
        try:
            rows = await WaterApi(async_get_clientsession(self.hass)).levels()
        except WaterApiError:
            return self.async_show_form(step_id="init", data_schema=vol.Schema({}), errors={"base":"cannot_connect"})
        current = self.config_entry.options.get(CONF_STATIONS, self.config_entry.data[CONF_STATIONS])
        return self.async_show_form(step_id="init", data_schema=_schema(_choices(rows, current), current, self.config_entry.options))
