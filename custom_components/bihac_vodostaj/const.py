DOMAIN = "bihac_vodostaj"
CONF_STATIONS = "stations"
CONF_THRESHOLD = "threshold_cm"
CONF_WARN_BEFORE = "warn_before_cm"
CONF_RISE = "rise_cm"
CONF_RISE_HOURS = "rise_hours"
DEFAULT_STATION = "2035"
DEFAULT_THRESHOLD = 180.0
DEFAULT_WARN_BEFORE = [15.0, 10.0]
DEFAULT_RISE = 15.0
DEFAULT_RISE_HOURS = 3
BASE = "https://vodostaji.voda.ba/data/internet/"
SOURCE = "https://vodostaji.voda.ba/"
UPDATE_MINUTES = 15
STALE_SECONDS = 21600
CLASSES = {
    "#MIN#": (1, "Normalno stanje"),
    "#TH1#": (2, "Pripremno stanje"),
    "#TH2#": (3, "Izlijevanje iz korita"),
    "#TH3#": (4, "Poplave"),
    "#TH4#": (5, "Značajne poplave"),
}
PLATFORMS = ["sensor", "binary_sensor"]
EVENT_ALERT = "bihac_vodostaj_alert"
