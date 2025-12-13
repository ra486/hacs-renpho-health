"""Renpho Health API Client."""
from __future__ import annotations

import base64
import json
import logging
import ssl
from datetime import datetime
from typing import Any
from urllib.request import Request, urlopen

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .const import (
    API_BASE_URL,
    APP_VERSION,
    DEVICE_TYPES,
    ENCRYPTION_KEY,
    ENDPOINT_DAILY_CALORIES,
    ENDPOINT_LOGIN,
)

_LOGGER = logging.getLogger(__name__)

# API error codes that indicate authentication failure
AUTH_ERROR_CODES = [102, 103, 104, 401, 403]  # Common auth error codes (including 403 Forbidden)
AUTH_ERROR_MESSAGES = ["token", "login", "unauthorized", "expired", "invalid", "forbidden"]


class RenphoApiError(Exception):
    """Exception for Renpho API errors."""


class RenphoAuthError(RenphoApiError):
    """Exception for authentication errors."""


class RenphoApi:
    """Renpho Health API Client."""

    def __init__(self, email: str, password: str) -> None:
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._token: str | None = None
        self._user_id: int | None = None
        self._user_info: dict[str, Any] = {}
        self._token_validated: bool = False
        self._disable_auto_reauth: bool = False  # When True, don't auto re-login

        # SSL context that doesn't verify certificates
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE

    @staticmethod
    def _aes_encrypt(plaintext: str) -> str:
        """Encrypt data using AES-128 ECB."""
        cipher = AES.new(ENCRYPTION_KEY.encode("utf-8"), AES.MODE_ECB)
        padded = pad(plaintext.encode("utf-8"), AES.block_size)
        return base64.b64encode(cipher.encrypt(padded)).decode("utf-8")

    @staticmethod
    def _aes_decrypt(ciphertext: str) -> str:
        """Decrypt data using AES-128 ECB."""
        cipher = AES.new(ENCRYPTION_KEY.encode("utf-8"), AES.MODE_ECB)
        decrypted = cipher.decrypt(base64.b64decode(ciphertext))
        return unpad(decrypted, AES.block_size).decode("utf-8")

    def _get_headers(self) -> dict[str, str]:
        """Get standard API headers."""
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "language": "en",
            "appVersion": APP_VERSION,
            "platform": "android",
            "area": "US",
            "timeZone": "-6",
            "systemVersion": "16",
            "languageCode": "en",
            "userArea": "US",
        }
        if self._token:
            headers["token"] = self._token
        if self._user_id:
            headers["userId"] = str(self._user_id)
        return headers

    def _is_auth_error(self, code: int, message: str) -> bool:
        """Check if the error indicates an authentication failure."""
        if code in AUTH_ERROR_CODES:
            return True
        msg_lower = message.lower()
        return any(keyword in msg_lower for keyword in AUTH_ERROR_MESSAGES)

    def _api_call(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an API call to Renpho."""
        url = f"{API_BASE_URL}/{endpoint}"

        # Encrypt request data
        if data:
            encrypted = self._aes_encrypt(json.dumps(data, separators=(",", ":")))
        else:
            encrypted = self._aes_encrypt("{}")

        body = json.dumps({"encryptData": encrypted}).encode("utf-8")

        req = Request(url, data=body, method="POST")
        for key, value in self._get_headers().items():
            req.add_header(key, value)

        try:
            with urlopen(req, timeout=30, context=self._ssl_context) as response:
                resp_data = json.loads(response.read().decode())
        except Exception as err:
            _LOGGER.error("API call failed: %s", err)
            raise RenphoApiError(f"API call failed: {err}") from err

        # Check response code
        code = resp_data.get("code", 0)
        if code != 101:
            msg = resp_data.get("msg", "Unknown error")
            _LOGGER.error("API error (code %s): %s", code, msg)
            # Raise auth error for token-related failures
            if self._is_auth_error(code, msg):
                self._token_validated = False
                raise RenphoAuthError(f"Authentication error: {msg}")
            raise RenphoApiError(f"API error: {msg}")

        # Decrypt response data
        if resp_data.get("data"):
            try:
                decoded = base64.b64decode(resp_data["data"])
                if len(decoded) % 16 == 0:
                    decrypted = self._aes_decrypt(resp_data["data"])
                    resp_data["decrypted"] = json.loads(decrypted)
            except Exception as err:
                _LOGGER.warning("Failed to decrypt response: %s", err)

        return resp_data

    async def async_login(self) -> bool:
        """Authenticate with Renpho API."""
        return await self._hass_async_add_executor_job(self._login)

    def _login(self) -> bool:
        """Authenticate with Renpho API (sync)."""
        _LOGGER.info("Performing fresh login to Renpho API")
        login_data = {
            "questionnaire": {},
            "login": {
                "email": self._email,
                "password": self._password,
                "areaCode": "US",
                "appRevision": APP_VERSION,
                "cellphoneType": "HomeAssistant",
                "systemType": "11",
                "platform": "android",
            },
            "bindingList": {"deviceTypes": DEVICE_TYPES},
        }

        try:
            response = self._api_call(ENDPOINT_LOGIN, login_data)
        except RenphoApiError as err:
            raise RenphoAuthError(f"Login failed: {err}") from err

        if not response.get("decrypted"):
            raise RenphoAuthError("Failed to decrypt login response")

        login_info = response["decrypted"].get("login", {})
        self._token = login_info.get("token")
        self._user_id = login_info.get("id")
        self._user_info = login_info
        self._token_validated = True

        if not self._token or not self._user_id:
            raise RenphoAuthError("Login response missing token or user ID")

        _LOGGER.debug("Login successful for user %s", self._user_id)
        return True

    def login(self) -> bool:
        """Authenticate with Renpho API (sync wrapper)."""
        return self._login()

    def set_cached_token(self, token: str, user_id: int, disable_auto_reauth: bool = True) -> None:
        """Set a cached token to avoid re-authentication."""
        self._token = token
        self._user_id = user_id
        self._token_validated = False  # Will be validated on first use
        self._disable_auto_reauth = disable_auto_reauth  # Don't auto re-login with cached tokens
        _LOGGER.debug("Loaded cached token for user %s (auto_reauth=%s)", user_id, not disable_auto_reauth)

    def get_token_data(self) -> dict[str, Any] | None:
        """Get current token data for caching."""
        if self._token and self._user_id:
            return {
                "token": self._token,
                "user_id": self._user_id,
            }
        return None

    @property
    def has_valid_token(self) -> bool:
        """Check if we have a token (may or may not be validated)."""
        return self._token is not None and self._user_id is not None

    def get_measurements(self) -> dict[str, Any]:
        """Get body composition measurements."""
        if not self._token:
            if self._disable_auto_reauth:
                raise RenphoAuthError("No token available and auto re-auth is disabled. Please update your token.")
            _LOGGER.debug("No token available, performing login")
            self._login()

        today = datetime.now().strftime("%Y-%m-%d")

        try:
            response = self._api_call(ENDPOINT_DAILY_CALORIES, {"data": today})
            self._token_validated = True  # Token worked successfully
        except RenphoAuthError:
            if self._disable_auto_reauth:
                _LOGGER.error("Token invalid/expired. Auto re-auth disabled to prevent mobile app logout. Update token manually.")
                raise RenphoAuthError("Token expired. Update token from mobile app to avoid logout.")
            # Only re-authenticate on auth errors (token expired/invalid)
            _LOGGER.info("Token invalid or expired, re-authenticating")
            self._login()
            response = self._api_call(ENDPOINT_DAILY_CALORIES, {"data": today})
        # Other RenphoApiError exceptions will propagate up without re-auth

        measurement = {}
        if response.get("decrypted"):
            measurement = (
                response["decrypted"].get("fourElectrodeWeight")
                or response["decrypted"].get("eightElectrodeWeight")
                or {}
            )

        # Build result
        weight_kg = measurement.get("weight") or self._user_info.get("weight", 0)

        return {
            "weight_kg": weight_kg,
            "weight_lbs": round(weight_kg * 2.20462, 1) if weight_kg else None,
            "bodyfat": measurement.get("bodyfat"),
            "bmi": measurement.get("bmi"),
            "muscle": measurement.get("muscle"),
            "water": measurement.get("water"),
            "bone": measurement.get("bone"),
            "bmr": measurement.get("bmr"),
            "bodyage": measurement.get("bodyage"),
            "visfat": measurement.get("visfat"),
            "subfat": measurement.get("subfat"),
            "protein": measurement.get("protein"),
            "sinew": measurement.get("sinew"),
            "fat_free_weight": measurement.get("fatFreeWeight"),
            "heart_rate": measurement.get("heartRate"),
            "height_cm": self._user_info.get("height"),
            "weight_goal_kg": self._user_info.get("weightGoal"),
            "bodyfat_goal": self._user_info.get("bodyfatGoal"),
            "last_measurement": measurement.get("localCreatedAt"),
            "scale_name": measurement.get("scaleName"),
        }

    @property
    def user_id(self) -> int | None:
        """Return user ID."""
        return self._user_id

    @property
    def user_info(self) -> dict[str, Any]:
        """Return user info."""
        return self._user_info
