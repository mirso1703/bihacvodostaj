"""Water level, flow, trend and official status sensors."""
from datetime import UTC, datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfLength, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import WaterConfigEntry
from .entity import StationEntity
from .const import *

SENSORS = [
 ("level_cm","level",UnitOfLength.CENTIMETERS,SensorDeviceClass.DISTANCE,SensorStateClass.MEASUREMENT),
 ("flow_m3s","flow",UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,SensorDeviceClass.VOLUME_FLOW_RATE,SensorStateClass.MEASUREMENT),
 ("rate_cm_h","rate","cm/h",None,SensorStateClass.MEASUREMENT),
 ("rise_3h_cm","rise_3h",UnitOfLength.CENTIMETERS,SensorDeviceClass.DISTANCE,SensorStateClass.MEASUREMENT),
 ("rise_24h_cm","rise_24h",UnitOfLength.CENTIMETERS,SensorDeviceClass.DISTANCE,SensorStateClass.MEASUREMENT),
 ("official_class","official_status",None,None,None),
 ("measured_at","measured_at",None,SensorDeviceClass.TIMESTAMP,None),
]
async def async_setup_entry(hass: HomeAssistant, entry: WaterConfigEntry, add: AddEntitiesCallback) -> None:
    ids = entry.options.get(CONF_STATIONS, entry.data[CONF_STATIONS])
    entities = [WaterSensor(entry.runtime_data, sid, key, unit, device, state, tkey) for sid in ids for key, tkey, unit, device, state in SENSORS]
    if DEFAULT_STATION in ids:
        entities += [WaterSensor(entry.runtime_data, DEFAULT_STATION, "local_status", None, None, None),
                     WaterSensor(entry.runtime_data, DEFAULT_STATION, "to_first_level_cm", UnitOfLength.CENTIMETERS, SensorDeviceClass.DISTANCE, SensorStateClass.MEASUREMENT)]
    add(entities)

class WaterSensor(StationEntity, SensorEntity):
    def __init__(self, coordinator, station, key, unit=None, device=None, state=None, translation_key=None):
        super().__init__(coordinator, station, key)
        self._attr_translation_key = translation_key or key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device
        self._attr_state_class = state
        # Precision only for numeric sensors; text/timestamp sensors with a precision fail to be added.
        if state is not None:
            self._attr_suggested_display_precision = 1

    @property
    def native_value(self):
        r = self._reading
        if self.key == "measured_at":
            ts = r.get("measured_at")
            return datetime.fromtimestamp(ts, UTC) if ts else None
        if self.key == "local_status":
            level = r.get("level_cm")
            if level is None: return None
            levels = [(180,"Dijelovi puta"),(200,"Put poplavljen"),(250,"Voda na parcelama")]
            return next((label for cm,label in reversed(levels) if level >= cm), "Ispod 180 cm")
        if self.key == "to_first_level_cm":
            level = r.get("level_cm")
            return round(max(0, 180-level),1) if level is not None else None
        return r.get(self.key)

    @property
    def extra_state_attributes(self):
        r = self._reading
        ts = r.get("measured_at")
        stale = ts is None or datetime.now(UTC).timestamp() - ts > STALE_SECONDS
        if self.key != "level_cm": return {"stale":stale, "station_no":self.station_no}
        return {"station_no":self.station_no, "river":r.get("river"), "site_no":r.get("site_no"),
                "official_class":r.get("official_class"), "official_severity":r.get("severity"),
                "measured_at":r.get("measured_at"), "stale":stale,
                "threshold_cm":180 if self.station_no == DEFAULT_STATION else None,
                "source":SOURCE}
