"""Constants for the Islamic Prayer component."""
from typing import Final

from prayer_times_calculator import PrayerTimesCalculator

DOMAIN: Final = "islamic_prayer_times_ie"
NAME: Final = "Islamic Prayer Times - IE"
PRAYER_TIMES_ICON = "mdi:calendar-clock"

CONF_CALC_METHOD: Final = "calculation_method"

CALC_METHODS = ["jafari", "karachi", "isna", "mwl", "makkah", "egypt", "tehran", "gulf", "kuwait", "qatar", "singapore", "france", "turkey", "russia", "ie-icci", "ie-mcnd", "ie-hicc"]

DEFAULT_CALC_METHOD: Final = "ie-mcnd"

DATA_UPDATED = "Islamic_prayer_data_updated"
