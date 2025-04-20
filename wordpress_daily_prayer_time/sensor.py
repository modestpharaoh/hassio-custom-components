"""Sensor platform for WordPress Daily Prayer Time integration."""
import logging
from datetime import datetime
from typing import Union

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, HIJRI_DATE_KEY
from .coordinator import (
    PrayerTimeCoordinator,
    WordpressPrayerTimeConfigEntry,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="fajr_begins",
        name="Fajr Prayer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="fajr_jamah",
        name="Fajr Iqamah",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="sunrise",
        name="Sunrise",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="zuhr_begins",
        name="Dhuhr Prayer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="zuhr_jamah",
        name="Dhuhr Iqamah",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="asr_mithl_1",
        name="Asr Prayer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="asr_jamah",
        name="Asr Iqamah",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="maghrib_begins",
        name="Maghrib Prayer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="maghrib_jamah",
        name="Maghrib Iqamah",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="isha_begins",
        name="Isha Prayer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="isha_jamah",
        name="Isha Iqamah",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key=HIJRI_DATE_KEY,
        name="Hijri Date",
        device_class=None,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WordpressPrayerTimeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = config_entry.runtime_data
    _LOGGER.debug("Setting up sensor with coordinator: %s", coordinator)
    async_add_entities(
        PrayerTimeSensor(coordinator, description)
        for description in SENSOR_TYPES
    )


class PrayerTimeSensor(
    CoordinatorEntity[PrayerTimeCoordinator], SensorEntity
):
    """Representation of an Islamic prayer time sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrayerTimeCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the Wordpress Daily Prayer Time sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.website_name,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> Union[datetime, str]:
        """Return the state of the sensor."""
        return self.coordinator.data[self.entity_description.key]
