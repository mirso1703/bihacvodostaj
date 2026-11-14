"""Alarm state sensors for selected stations."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import WaterConfigEntry
from .entity import StationEntity
from .const import *

async def async_setup_entry(hass: HomeAssistant, entry: WaterConfigEntry, add: AddEntitiesCallback) -> None:
    ids = entry.options.get(CONF_STATIONS, entry.data[CONF_STATIONS])
    entities = [WaterAlarmSensor(entry.runtime_data, sid, key) for sid in ids for key in ("official_warning","rapid_rise")]
    if DEFAULT_STATION in ids:
        entities += [WaterAlarmSensor(entry.runtime_data, DEFAULT_STATION, "approaching_threshold"),
                     WaterAlarmSensor(entry.runtime_data, DEFAULT_STATION, "threshold_reached")]
    add(entities)

class WaterAlarmSensor(StationEntity, BinarySensorEntity):
    def __init__(self, coordinator, station, key):
        super().__init__(coordinator, station, key)
        self._attr_translation_key = key
        self._attr_device_class = BinarySensorDeviceClass.SAFETY

    @property
    def is_on(self):
        r = self._reading
        if self.key == "official_warning": return int(r.get("severity",0)) >= 2
        if self.key == "rapid_rise": return (r.get("rise_3h_cm") or 0) >= float({**self.coordinator.entry.data, **self.coordinator.entry.options}.get(CONF_RISE, DEFAULT_RISE))
        level = r.get("level_cm")
        if level is None: return None
        threshold = float({**self.coordinator.entry.data, **self.coordinator.entry.options}.get(CONF_THRESHOLD, DEFAULT_THRESHOLD))
        if self.key == "approaching_threshold": return threshold-max(DEFAULT_WARN_BEFORE) <= level < threshold
        return level >= threshold
