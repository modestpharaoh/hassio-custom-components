# WordPress Daily Prayer Time Integration

This is a custom Home Assistant integration for fetching and displaying daily prayer times from a WordPress-based website with [Daily Prayer Time - Plugin](https://wordpress.org/plugins/daily-prayer-time-for-mosques/)

## Features

- Fetches daily prayer times from a WordPress - Daily Prayer Time - API.
- Displays prayer times in Home Assistant.
- Supports automation refresh everyday after midnight.
- Support fetching the full year by default and save it to Home Assistant config directory. In case you site wasn't reachable by the time of the update, it will fallback to the saved prayer of the year.

## Installation

1. Clone this repository into your Home Assistant.
2. Move the `wordpress_daily_prayer_time` directory to Home Assistant `custom_components` directory. 
3. Ensure the directory structure is as follows:
  ```
  custom_components/
  └── wordpress_daily_prayer_time/
     ├── __init__.py
     ├── manifest.json
     ├── sensor.py
     └── ...
  ```
4. Restart Home Assistant.

## Configuration

1. Open `Device & Services` Dashboard.
2. ADD INTEGRATION: `WordPress Daily Prayer Time`, and fill the following parameters:

   a. `Endpoint URL`: Enter a valid http/https masjid Wordpress site. e.g. `https://masjid-wp.com`

   b. `API Path`: API path for full year, default `wp-json/dpt/v1/prayertime?filter=year`


## Usage

Once configured, the integration will create sensors for each prayer Athan/Iqamah. You can use these sensors in your automations or display them in your dashboard.

## Troubleshooting

- Ensure the API URL is correct and accessible.
- Check the Home Assistant logs for any errors.

## Disclamation
* There is no guarantee that the component will get the correct one, I always try my best to update, whenever there is a bug show up. 