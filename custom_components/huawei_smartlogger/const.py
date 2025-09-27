"""Constants for the Huawei SmartLogger integration."""

DOMAIN = "huawei_smartlogger"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 30
PLATFORM = "sensor"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE_ID = "slave_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_STRINGS = "strings"
CONF_NAME = "name"
CONF_VOLTAGE_REGISTER = "voltage_register"
CONF_CURRENT_REGISTER = "current_register"
CONF_POWER_REGISTER = "power_register"
CONF_VOLTAGE_SCALE = "voltage_scale"
CONF_CURRENT_SCALE = "current_scale"
CONF_POWER_SCALE = "power_scale"

SENSOR_TYPES = {
    "voltage": {
        "name": "Voltage",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement",
        "register_key": CONF_VOLTAGE_REGISTER,
        "scale_key": CONF_VOLTAGE_SCALE,
    },
    "current": {
        "name": "Current",
        "unit": "A",
        "device_class": "current",
        "state_class": "measurement",
        "register_key": CONF_CURRENT_REGISTER,
        "scale_key": CONF_CURRENT_SCALE,
    },
    "power": {
        "name": "Power",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "register_key": CONF_POWER_REGISTER,
        "scale_key": CONF_POWER_SCALE,
    },
}
