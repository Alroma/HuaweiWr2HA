"""The Huawei SmartLogger integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import voluptuous as vol

from homeassistant.const import CONF_SCAN_INTERVAL, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery

from .const import (
    CONF_CURRENT_REGISTER,
    CONF_CURRENT_SCALE,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_POWER_REGISTER,
    CONF_POWER_SCALE,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    CONF_STRINGS,
    CONF_VOLTAGE_REGISTER,
    CONF_VOLTAGE_SCALE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    PLATFORM,
)

_LOGGER = logging.getLogger(__name__)


STRING_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_VOLTAGE_REGISTER): cv.positive_int,
        vol.Required(CONF_CURRENT_REGISTER): cv.positive_int,
        vol.Required(CONF_POWER_REGISTER): cv.positive_int,
        vol.Optional(CONF_VOLTAGE_SCALE, default=0.1): vol.Coerce(float),
        vol.Optional(CONF_CURRENT_SCALE, default=0.1): vol.Coerce(float),
        vol.Optional(CONF_POWER_SCALE, default=1.0): vol.Coerce(float),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): cv.positive_int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
                vol.Required(CONF_STRINGS): vol.All(cv.ensure_list, [STRING_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration from configuration.yaml."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    hub = HuaweiSmartLoggerHub(
        hass,
        host=conf[CONF_HOST],
        port=conf[CONF_PORT],
        slave_id=conf[CONF_SLAVE_ID],
    )
    strings = conf[CONF_STRINGS]
    scan_interval = timedelta(seconds=conf[CONF_SCAN_INTERVAL])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["hub"] = hub
    hass.data[DOMAIN][CONF_STRINGS] = strings
    hass.data[DOMAIN][CONF_SCAN_INTERVAL] = scan_interval

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP,
        lambda event: hass.async_create_task(hub.async_close()),
    )

    await hass.async_add_executor_job(hub.ensure_connection)

    hass.async_create_task(
        discovery.async_load_platform(hass, PLATFORM, DOMAIN, {}, config)
    )

    return True


class HuaweiSmartLoggerHub:
    """Handle communication with the SmartLogger Modbus interface."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, slave_id: int) -> None:
        """Initialize the hub."""
        self._hass = hass
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._client = ModbusTcpClient(host=self._host, port=self._port)
        self._lock = asyncio.Lock()

    def ensure_connection(self) -> None:
        """Ensure that we can reach the SmartLogger."""
        if not self._client.connect():
            raise ConnectionError(
                "Unable to connect to Huawei SmartLogger at %s:%s"
                % (self._host, self._port)
            )
        self._client.close()

    @property
    def host(self) -> str:
        """Return the host of the SmartLogger."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port of the SmartLogger."""
        return self._port

    @property
    def slave_id(self) -> int:
        """Return the Modbus slave ID."""
        return self._slave_id

    async def async_close(self) -> None:
        """Close the Modbus connection."""
        def _close() -> None:
            self._client.close()

        await self._hass.async_add_executor_job(_close)

    async def async_read_input_register(self, address: int) -> int:
        """Read a single input register."""
        async with self._lock:
            result = await self._hass.async_add_executor_job(
                self._read_input_registers, address, 1
            )
        return result[0]

    def _read_input_registers(self, address: int, count: int) -> list[int]:
        """Read input registers synchronously in an executor."""
        if not self._client.connect():
            raise ConnectionError(
                "Unable to connect to Huawei SmartLogger at %s:%s"
                % (self._host, self._port)
            )

        try:
            response = self._client.read_input_registers(address, count, unit=self._slave_id)
        finally:
            self._client.close()

        if response.isError():
            raise ModbusException(str(response))

        if not hasattr(response, "registers"):
            raise ModbusException("No register data returned")

        return response.registers
