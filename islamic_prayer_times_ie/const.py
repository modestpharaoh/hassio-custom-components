"""Constants for the Islamic Prayer component."""
DOMAIN = "islamic_prayer_times_ie"
NAME = "Islamic Prayer Times - IE"
PRAYER_TIMES_ICON = "mdi:calendar-clock"

SENSOR_TYPES = {
    "Fajr": "prayer",
    "Sunrise": "time",
    "Dhuhr": "prayer",
    "Asr": "prayer",
    "Maghrib": "prayer",
    "Isha": "prayer",
    "Midnight": "time",
}

CONF_CALC_METHOD = "calculation_method"

#CALC_METHODS = ["isna", "karachi", "mwl", "makkah", "icci"]

CALC_METHODS = ["jafari", "karachi", "isna", "mwl", "makkah", "egypt", "tehran", "gulf", "kuwait", "qatar", "singapore", "france", "turkey", "russia", "icci"]

DEFAULT_CALC_METHOD = "icci"

DATA_UPDATED = "Islamic_prayer_data_updated"
