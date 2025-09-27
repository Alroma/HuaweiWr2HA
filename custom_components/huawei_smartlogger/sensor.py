"""Sensor platform for Huawei SmartLogger PV string data."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_NAME, CONF_SCAN_INTERVAL, CONF_STRINGS, DOMAIN, SENSOR_TYPES

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from . import HuaweiSmartLoggerHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the Huawei SmartLogger sensors."""
    if discovery_info is None:
        return

    data = hass.data[DOMAIN]
    hub = data["hub"]
    strings = data[CONF_STRINGS]
    scan_interval: timedelta = data[CONF_SCAN_INTERVAL]

    coordinator = HuaweiSmartLoggerCoordinator(
        hass,
        hub=hub,
        strings=strings,
        update_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    entities: list[HuaweiStringSensor] = []
    for index, string in enumerate(strings):
        for sensor_type in SENSOR_TYPES:
            entities.append(
                HuaweiStringSensor(
                    coordinator=coordinator,
                    string_index=index,
                    string_config=string,
                    sensor_type=sensor_type,
                )
            )

    async_add_entities(entities)


class HuaweiSmartLoggerCoordinator(DataUpdateCoordinator[dict[str, dict[str, float]]]):
    """Coordinator for polling Huawei SmartLogger PV strings."""

    def __init__(
        self,
        hass: HomeAssistant,
        hub: "HuaweiSmartLoggerHub",
        strings: list[dict[str, Any]],
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Huawei SmartLogger",
            update_interval=update_interval,
        )
        self._hub = hub
        self._strings = strings

    async def _async_update_data(self) -> dict[str, dict[str, float]]:
        data: dict[str, dict[str, float]] = {}

        for string in self._strings:
            string_name = string[CONF_NAME]
            measurements: dict[str, float] = {}

            for measurement, meta in SENSOR_TYPES.items():
                address = string[meta["register_key"]]
                scale = string.get(meta["scale_key"], 1.0)

                try:
                    raw_value = await self._hub.async_read_input_register(address)
                except Exception as err:  # pylint: disable=broad-except
                    raise UpdateFailed(
                        f"Failed to read register {address} for {string_name}: {err}"
                    ) from err

                measurements[measurement] = raw_value * scale

            data[string_name] = measurements

        return data

    @property
    def hub(self) -> "HuaweiSmartLoggerHub":
        """Return the Modbus hub instance."""
        return self._hub


class HuaweiStringSensor(CoordinatorEntity[HuaweiSmartLoggerCoordinator], SensorEntity):
    """Representation of a Huawei SmartLogger string sensor."""

    def __init__(
        self,
        coordinator: HuaweiSmartLoggerCoordinator,
        string_index: int,
        string_config: dict[str, Any],
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        meta = SENSOR_TYPES[sensor_type]
        self._string_index = string_index
        self._string_name = string_config[CONF_NAME]
        self._sensor_type = sensor_type
        self._hub = coordinator.hub
        self._attr_name = f"{self._string_name} {meta['name']}"
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_device_class = meta["device_class"]
        self._attr_state_class = meta["state_class"]
        self._attr_unique_id = (
            f"{self._hub.host}_slave_{self._hub.slave_id}_string_{string_index}_{sensor_type}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._hub.host}:{self._hub.port}")},
            name=f"Huawei SmartLogger ({self._hub.host})",
            manufacturer="Huawei",
            model="SmartLogger Modbus",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        measurements = self.coordinator.data.get(self._string_name)
        if measurements is None:
            return None
        return measurements.get(self._sensor_type)
