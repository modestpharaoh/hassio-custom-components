"""Constants for the WordPress Daily Prayer Time integration."""

from typing import Final


DOMAIN: Final = "wordpress_daily_prayer_time"
NAME: Final = "WordPress Daily Prayer Time"

# Sensor keys for prayer times
PRAYER_TIME_KEYS: Final = [
    "fajr_begins",
    "fajr_jamah",
    "sunrise",
    "zuhr_begins",
    "zuhr_jamah",
    "asr_mithl_1",
    "asr_jamah",
    "maghrib_begins",
    "maghrib_jamah",
    "isha_begins",
    "isha_jamah",
]

CONF_ENDPOINT: Final = "endpoint"
CONF_API_PATH: Final = "api_path"
DEFAULT_API_PATH: Final = "wp-json/dpt/v1/prayertime?filter=year"

# Additional sensor key for Hijri date
HIJRI_DATE_KEY: Final = "hijri_date"

# Timeout for querying the endpoint
QUERY_TIMEOUT = 10  # seconds
