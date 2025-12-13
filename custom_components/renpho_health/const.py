"""Constants for Renpho Health integration."""
from homeassistant.const import (
    PERCENTAGE,
    UnitOfMass,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfTime,
)

DOMAIN = "renpho_health"

# API Configuration
API_BASE_URL = "https://cloud.renpho.com"
ENCRYPTION_KEY = "ed*wijdi$h6fe3ew"
APP_VERSION = "7.5.0"

# API Endpoints
ENDPOINT_LOGIN = "renpho-aggregation/user/login"
ENDPOINT_DAILY_CALORIES = "RenphoHealth/healthManage/dailyCalories"

# Device types for body weight scales
DEVICE_TYPES = ["02D3", "02D5", "0B18", "0B38", "0B58", "0B78", "0BA6"]

# Configuration keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REFRESH_INTERVAL = "refresh_interval"

# Default values
DEFAULT_REFRESH_INTERVAL = 3600  # 1 hour

# Sensor definitions
SENSOR_TYPES = {
    "weight_kg": {
        "name": "Weight",
        "unit": UnitOfMass.KILOGRAMS,
        "icon": "mdi:scale-bathroom",
        "device_class": "weight",
        "state_class": "measurement",
    },
    "weight_lbs": {
        "name": "Weight (lbs)",
        "unit": "lbs",
        "icon": "mdi:scale-bathroom",
        "device_class": None,
        "state_class": "measurement",
    },
    "bodyfat": {
        "name": "Body Fat",
        "unit": PERCENTAGE,
        "icon": "mdi:percent",
        "device_class": None,
        "state_class": "measurement",
    },
    "bmi": {
        "name": "BMI",
        "unit": None,
        "icon": "mdi:human",
        "device_class": None,
        "state_class": "measurement",
    },
    "muscle": {
        "name": "Muscle Mass",
        "unit": PERCENTAGE,
        "icon": "mdi:arm-flex",
        "device_class": None,
        "state_class": "measurement",
    },
    "water": {
        "name": "Body Water",
        "unit": PERCENTAGE,
        "icon": "mdi:water-percent",
        "device_class": None,
        "state_class": "measurement",
    },
    "bone": {
        "name": "Bone Mass",
        "unit": UnitOfMass.KILOGRAMS,
        "icon": "mdi:bone",
        "device_class": None,
        "state_class": "measurement",
    },
    "bmr": {
        "name": "BMR",
        "unit": "kcal",
        "icon": "mdi:fire",
        "device_class": None,
        "state_class": "measurement",
    },
    "bodyage": {
        "name": "Body Age",
        "unit": "years",
        "icon": "mdi:account-clock",
        "device_class": None,
        "state_class": "measurement",
    },
    "visfat": {
        "name": "Visceral Fat",
        "unit": None,
        "icon": "mdi:stomach",
        "device_class": None,
        "state_class": "measurement",
    },
    "subfat": {
        "name": "Subcutaneous Fat",
        "unit": PERCENTAGE,
        "icon": "mdi:circle-outline",
        "device_class": None,
        "state_class": "measurement",
    },
    "protein": {
        "name": "Protein",
        "unit": PERCENTAGE,
        "icon": "mdi:food-steak",
        "device_class": None,
        "state_class": "measurement",
    },
    "sinew": {
        "name": "Lean Body Mass",
        "unit": UnitOfMass.KILOGRAMS,
        "icon": "mdi:human-handsup",
        "device_class": None,
        "state_class": "measurement",
    },
    "fat_free_weight": {
        "name": "Fat Free Weight",
        "unit": UnitOfMass.KILOGRAMS,
        "icon": "mdi:weight-lifter",
        "device_class": None,
        "state_class": "measurement",
    },
    "heart_rate": {
        "name": "Heart Rate",
        "unit": "bpm",
        "icon": "mdi:heart-pulse",
        "device_class": None,
        "state_class": "measurement",
    },
    "height_cm": {
        "name": "Height",
        "unit": UnitOfLength.CENTIMETERS,
        "icon": "mdi:human-male-height",
        "device_class": None,
        "state_class": "measurement",
    },
    "weight_goal_kg": {
        "name": "Weight Goal",
        "unit": UnitOfMass.KILOGRAMS,
        "icon": "mdi:target",
        "device_class": None,
        "state_class": None,
    },
    "bodyfat_goal": {
        "name": "Body Fat Goal",
        "unit": PERCENTAGE,
        "icon": "mdi:target",
        "device_class": None,
        "state_class": None,
    },
}
