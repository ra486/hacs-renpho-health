"""Config flow for Renpho Health integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers.storage import Store

from .api import RenphoApi, RenphoAuthError
from .const import CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL, DOMAIN

CONF_TOKEN = "token"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.tokens"

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = RenphoApi(data[CONF_EMAIL], data[CONF_PASSWORD])

    try:
        await hass.async_add_executor_job(api.login)
    except RenphoAuthError as err:
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception during validation")
        raise CannotConnect from err

    return {
        "title": f"Renpho ({data[CONF_EMAIL]})",
        "user_id": api.user_id,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renpho Health."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(str(info["user_id"]))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Renpho Health."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Handle token update if provided
            new_token = user_input.pop(CONF_TOKEN, None)
            if new_token and new_token.strip():
                new_token = new_token.strip()
                if new_token.startswith("eyJ"):
                    # Valid JWT token - save it
                    await self._update_token(new_token)
                    _LOGGER.info("Token updated via options flow")
                else:
                    errors["base"] = "invalid_token"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_REFRESH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
                    vol.Optional(CONF_TOKEN, default=""): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "token_help": "Paste a token from the mobile app to share the session (optional)"
            },
        )

    async def _update_token(self, token: str) -> None:
        """Update the token in storage."""
        store = Store(self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.config_entry.entry_id}")

        # Load existing data to get user_id
        existing = await store.async_load()
        user_id = existing.get("user_id") if existing else None

        if not user_id:
            # Try to extract from token (JWT payload contains userId)
            try:
                import base64
                import json
                payload = token.split('.')[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))
                user_id = decoded.get("userId")
            except Exception:
                _LOGGER.warning("Could not extract user_id from token")

        # Save the new token
        await store.async_save({
            "token": token,
            "user_id": user_id,
        })


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
