"""Shared station device information."""
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, SOURCE

class StationEntity:
    def __init__(self, coordinator, station: str, key: str) -> None:
        self.coordinator, self.station_no, self.key = coordinator, station, key
        self._attr_unique_id = f"{station}_{key}"
        self._attr_has_entity_name = True

    @property
    def _reading(self):
        return (self.coordinator.data or {}).get(self.station_no, {})

    @property
    def available(self) -> bool:
        return super().available and bool(self._reading.get("available"))

    @property
    def device_info(self) -> DeviceInfo:
        r = self._reading
        return DeviceInfo(identifiers={(DOMAIN, self.station_no)}, name=r.get("station", f"Stanica {self.station_no}"), manufacturer="Agencija za vodno područje rijeke Save", model=f"{r.get('river','')} · {self.station_no}", configuration_url=SOURCE)
