"""Coordinator for the Islamic prayer times integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import requests

from prayer_times_calculator import PrayerTimesCalculator, exceptions
from requests.exceptions import ConnectionError as ConnError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import CONF_CALC_METHOD, DEFAULT_CALC_METHOD, DOMAIN

_LOGGER = logging.getLogger(__name__)


# Convert a list of hour/minutes of a prayer to time in format 01:07.
# Inputs:
#   timelist: [hour Integer, Minutes Integer]
#   offset: +/- Integer of hour offset correction
def formatTime(timeList, offset):
    return str(timeList[0] + offset).zfill(2) + ':' + str(timeList[1]).zfill(2)


class IslamicPrayerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, datetime]]):
    """Islamic Prayer Client Object."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Islamic Prayer client."""
        self.event_unsub: CALLBACK_TYPE | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )

    @property
    def calc_method(self) -> str:
        """Return the calculation method."""
        return self.config_entry.options.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

    def get_new_prayer_times(self) -> dict[str, str]:
        """Fetch prayer times for today."""
        # calc = PrayerTimesCalculator(
        #     latitude=self.hass.config.latitude,
        #     longitude=self.hass.config.longitude,
        #     calculation_method=self.calc_method,
        #     date=str(dt_util.now().date()),
        # )
        # return calc.fetch_prayer_times()

        calc_method = self.calc_method
        _LOGGER.debug(calc_method)
        
        # For standard calculation methods, we use fetch_prayer_times library
        # resp is Dict, sample: {'Fajr': '06:47', 'Sunrise': '08:37', 'Dhuhr': '12:22', 'Asr': '13:53', 'Sunset': '16:07', 'Maghrib': '16:07', 'Isha': '17:57', 'Imsak': '06:37', 'Midnight': '00:22'}
        if calc_method != 'icci':
            calc = PrayerTimesCalculator(
                latitude=self.hass.config.latitude,
                longitude=self.hass.config.longitude,
                calculation_method=self.calc_method,
                date=str(dt_util.now().date()),
            )
            return calc.fetch_prayer_times()
        # For Irish ICC calculation, we get the fill timetable of the year from
        # https://islamireland.ie/api/timetable/ , and parse JSON
        else:
            # Only set midnight to 00:00, if failed to get the value via ISNA
            # standard calculation
            midnight = '00:00'
            try:
                calc = PrayerTimesCalculator(
                    latitude=self.hass.config.latitude,
                    longitude=self.hass.config.longitude,
                    calculation_method='isna',
                    date=str(dt_util.now().date()),
                )
                isna_prayers = calc.fetch_prayer_times()
                #_LOGGER.info("ISNA Prayers: " + str(isna_prayers) + " " + str(type(isna_prayers)))
                midnight = isna_prayers['Midnight']
                _LOGGER.info('Midnight from ISNA calculation: ' + midnight)

                # As ICCI timetable may consider DST time from 1st of April to
                # end of October, and it supposed to start of last Sunday in
                # March, and end last Sunday of October. There is a few days
                # at end of March/October will be shift +/-1 hour.
                # Maghrib is consider same for all calculation, so will try to
                # compare ICCI with ISNA ones, and use that offset to fix all.
                # Prayers.
                isna_maghrib = isna_prayers['Maghrib']
                _LOGGER.info('Maghrib from ISNA calculation: ' + isna_maghrib)
            except Exception as e:
                _LOGGER.info('Failed to extract midnight/maghrib from ISNA calculation: ' + str(e))
            
            current_month = datetime.today().strftime("%-m")
            current_day = datetime.today().strftime("%-d")
            url = 'https://islamireland.ie/api/timetable/'
            json_resp = None
            try:
                resp = requests.get(url=url, params = {})
                if resp.status_code != requests.codes.ok:
                    _LOGGER.debug('islamireland request failed')
                else:
                    _LOGGER.debug('islamireland was successful')
                json_resp = resp.json()
            except Exception as e:
                _LOGGER.info('islamireland request exception raised, got error: ' + str(e))
            if json_resp is not None:
                try:
                    prayers = json_resp['timetable'][current_month][current_day]
                    icci_maghrib = formatTime(prayers[4], 0)
                    _LOGGER.info('Maghrib from ICCI calculation: ' + icci_maghrib)

                    # Get different between ISNA/ICCI Maghrib in seconds
                    icci = datetime.strptime(icci_maghrib, '%H:%M')
                    isna = datetime.strptime(isna_maghrib, '%H:%M')
                    
                    hr_offset = 0
                    maghrib_delta = 0
                    # if you subtract the bigger timestamp from smaller, you will get one day of seconds
                    if icci > isna:
                        maghrib_delta = ( icci - isna ).seconds
                        if maghrib_delta > 900 :
                            hr_offset = -1
                    if icci <= isna:
                        maghrib_delta = ( isna - icci ).seconds
                        if maghrib_delta > 900 :
                            hr_offset = 1
                    _LOGGER.info('Seconds different between ISNA and ICCI: ' + str(maghrib_delta))
                    _LOGGER.info('Offset for ICCI: ' + str(hr_offset))

                    prayer_times_info = {'Fajr': formatTime(prayers[0], hr_offset), 
                    'Sunrise': formatTime(prayers[1], hr_offset),
                    'Dhuhr': formatTime(prayers[2], hr_offset),
                    'Asr': formatTime(prayers[3], hr_offset), 
                    'Sunset': formatTime(prayers[4], hr_offset),
                    'Maghrib': formatTime(prayers[4], hr_offset),
                    'Isha': formatTime(prayers[5], hr_offset),
                    'Imsak': formatTime(prayers[4], hr_offset), 
                    'Midnight': midnight}

                    _LOGGER.debug(prayer_times_info)
                    return prayer_times_info
                except Exception as e:
                    _LOGGER.info('Failed to retrive prayer from ICCI, failed to parse prayers from JSON: ' + str(e))
                    return isna_prayers
            else:
                _LOGGER.info('Failed to retrive prayer from ICCI, JSON response is None.')
                return isna_prayers


    @callback
    def async_schedule_future_update(self, midnight_dt: datetime) -> None:
        """Schedule future update for sensors.
        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.
        Calculated Midnight: The Islamic midnight.
        Traditional Midnight: 12:00AM
        Update logic for prayer times:
        If the Calculated Midnight is before the traditional midnight then wait
        until the traditional midnight to run the update.  This way the day
        will have changed over and we don't need to do any fancy calculations.
        If the Calculated Midnight is after the traditional midnight, then wait
        until after the calculated Midnight.  We don't want to update the prayer
        times too early or else the timings might be incorrect.
        Example:
        calculated midnight = 11:23PM (before traditional midnight)
        Update time: 12:00AM
        calculated midnight = 1:35AM (after traditional midnight)
        update time: 1:36AM.
        """
        _LOGGER.debug("Scheduling next update for Islamic prayer times")

        now = dt_util.utcnow()

        if now > midnight_dt:
            next_update_at = midnight_dt + timedelta(days=1, minutes=1)
            _LOGGER.debug(
                "Midnight is after the day changes so schedule update for after Midnight the next day"
            )
        else:
            _LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))

        _LOGGER.debug("Next update scheduled for: %s", next_update_at)

        self.event_unsub = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

    async def async_request_update(self, *_) -> None:
        """Request update from coordinator."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, datetime]:
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.hass.async_add_executor_job(
                self.get_new_prayer_times
            )
        except (exceptions.InvalidResponseError, ConnError) as err:
            async_call_later(self.hass, 60, self.async_request_update)
            raise UpdateFailed from err

        prayer_times_info: dict[str, datetime] = {}
        for prayer, time in prayer_times.items():
            if prayer_time := dt_util.parse_datetime(f"{dt_util.now().date()} {time}"):
                prayer_times_info[prayer] = dt_util.as_utc(prayer_time)

        self.async_schedule_future_update(prayer_times_info["Midnight"])
        return prayer_times_info
