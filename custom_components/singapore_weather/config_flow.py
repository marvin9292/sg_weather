from __future__ import annotations

from typing import Any

from aiohttp import ClientError
import probatio

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    BASE_HEADERS,
    CONF_API_KEY,
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_WORK_LATITUDE,
    CONF_WORK_LONGITUDE,
    DOMAIN,
    PM25_URL,
)


class SingaporeWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def _schema(self, data: dict[str, Any] | None = None) -> probatio.Schema:
        data = data or {}

        home_latitude = (
            probatio.Required(
                CONF_HOME_LATITUDE,
                default=data[CONF_HOME_LATITUDE],
            )
            if CONF_HOME_LATITUDE in data
            else probatio.Required(CONF_HOME_LATITUDE)
        )
        home_longitude = (
            probatio.Required(
                CONF_HOME_LONGITUDE,
                default=data[CONF_HOME_LONGITUDE],
            )
            if CONF_HOME_LONGITUDE in data
            else probatio.Required(CONF_HOME_LONGITUDE)
        )
        work_latitude = (
            probatio.Required(
                CONF_WORK_LATITUDE,
                default=data[CONF_WORK_LATITUDE],
            )
            if CONF_WORK_LATITUDE in data
            else probatio.Required(CONF_WORK_LATITUDE)
        )
        work_longitude = (
            probatio.Required(
                CONF_WORK_LONGITUDE,
                default=data[CONF_WORK_LONGITUDE],
            )
            if CONF_WORK_LONGITUDE in data
            else probatio.Required(CONF_WORK_LONGITUDE)
        )

        return probatio.Schema(
            {
                probatio.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                home_latitude: NumberSelector(
                    NumberSelectorConfig(
                        min=-90,
                        max=90,
                        step="any",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                home_longitude: NumberSelector(
                    NumberSelectorConfig(
                        min=-180,
                        max=180,
                        step="any",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                work_latitude: NumberSelector(
                    NumberSelectorConfig(
                        min=-90,
                        max=90,
                        step="any",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                work_longitude: NumberSelector(
                    NumberSelectorConfig(
                        min=-180,
                        max=180,
                        step="any",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

    async def _validate_api_key(self, api_key: str) -> str | None:
        if not api_key:
            return "invalid_auth"

        headers = dict(BASE_HEADERS)
        headers["x-api-key"] = api_key
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(PM25_URL, headers=headers, timeout=15) as response:
                if response.status in (401, 403):
                    return "invalid_auth"
                if response.status == 429:
                    return "rate_limited"
                if response.status != 200:
                    return "cannot_connect"
                await response.json()
        except (ClientError, TimeoutError):
            return "cannot_connect"
        except (TypeError, ValueError):
            return "unknown"

        return None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_API_KEY] = str(user_input[CONF_API_KEY]).strip()
            error = await self._validate_api_key(user_input[CONF_API_KEY])
            if error is None:
                return self.async_create_entry(
                    title="Singapore Weather",
                    data=user_input,
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=self._schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_API_KEY] = str(user_input[CONF_API_KEY]).strip()
            error = await self._validate_api_key(user_input[CONF_API_KEY])
            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            errors["base"] = error

        data = {
            key: value
            for key, value in entry.data.items()
            if key != CONF_API_KEY
        }
        if user_input:
            data.update(
                {
                    key: value
                    for key, value in user_input.items()
                    if key != CONF_API_KEY
                }
            )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self._schema(data),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_API_KEY] = str(user_input[CONF_API_KEY]).strip()
            error = await self._validate_api_key(user_input[CONF_API_KEY])
            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            errors["base"] = error

        data = {
            key: value
            for key, value in entry.data.items()
            if key != CONF_API_KEY
        }
        if user_input:
            data.update(
                {
                    key: value
                    for key, value in user_input.items()
                    if key != CONF_API_KEY
                }
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._schema(data),
            errors=errors,
        )
