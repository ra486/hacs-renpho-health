"""Sensor platform for Renpho Health integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Renpho Health sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    user_id = hass.data[DOMAIN][config_entry.entry_id]["user_id"]

    sensors = []
    for sensor_type, sensor_config in SENSOR_TYPES.items():
        sensors.append(
            RenphoHealthSensor(
                coordinator=coordinator,
                config_entry=config_entry,
                sensor_type=sensor_type,
                sensor_config=sensor_config,
                user_id=user_id,
            )
        )

    async_add_entities(sensors, True)


class RenphoHealthSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Renpho Health sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        sensor_config: dict[str, Any],
        user_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config
        self._user_id = user_id

        self._attr_name = f"Renpho {sensor_config['name']}"
        self._attr_unique_id = f"renpho_{user_id}_{sensor_type}"
        self._attr_icon = sensor_config.get("icon")
        self._attr_native_unit_of_measurement = sensor_config.get("unit")

        # Set device class if available
        if sensor_config.get("device_class"):
            self._attr_device_class = sensor_config["device_class"]

        # Set state class if available
        if sensor_config.get("state_class"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._user_id))},
            name="Renpho Scale",
            manufacturer="Renpho",
            model="Smart Scale",
            sw_version="1.0",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_type)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self._sensor_type == "weight_kg" and self.coordinator.data:
            return {
                "last_measurement": self.coordinator.data.get("last_measurement"),
                "scale_name": self.coordinator.data.get("scale_name"),
            }
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
