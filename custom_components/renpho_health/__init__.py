"""The Renpho Health integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RenphoApi, RenphoApiError, RenphoAuthError
from .const import CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.tokens"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renpho Health from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    refresh_interval = entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)

    api = RenphoApi(email, password)

    # Set up token storage
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}")

    # Try to load cached token
    cached_data = await store.async_load()
    token_loaded = False
    if cached_data and cached_data.get("token") and cached_data.get("user_id"):
        _LOGGER.info("Loading cached token for Renpho API (avoiding fresh login)")
        api.set_cached_token(
            cached_data["token"],
            cached_data["user_id"],
            cached_data.get("user_info"),
        )
        token_loaded = True

    # Only do fresh login if no cached token
    if not token_loaded:
        try:
            _LOGGER.info("No cached token, performing fresh login")
            await hass.async_add_executor_job(api.login)
            # Save the new token
            token_data = api.get_token_data()
            if token_data:
                await store.async_save(token_data)
                _LOGGER.debug("Saved new token to cache")
        except RenphoApiError as err:
            _LOGGER.error("Failed to authenticate with Renpho: %s", err)
            return False

    async def async_update_data():
        """Fetch data from API."""
        try:
            data = await hass.async_add_executor_job(api.get_measurements)
            # Save token after successful call (in case it was refreshed)
            token_data = api.get_token_data()
            if token_data:
                await store.async_save(token_data)
            return data
        except RenphoAuthError as err:
            # Auth failed even after re-auth attempt in api.get_measurements
            _LOGGER.error("Authentication failed: %s", err)
            raise UpdateFailed(f"Authentication error: {err}") from err
        except RenphoApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=refresh_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "user_id": api.user_id,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
