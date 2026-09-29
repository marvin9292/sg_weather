from __future__ import annotations

from datetime import datetime

from homeassistant.components.weather import WeatherEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.weather import WeatherEntityFeature

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    coordinators = hass.data[DOMAIN][entry.entry_id]
    coordinator = coordinators["fourday"]
    async_add_entities([SingaporeFourDayWeather(coordinator)], True)


class SingaporeFourDayWeather(CoordinatorEntity, WeatherEntity):

    _attr_unique_id = "singapore_four_day_weather"
    _attr_name = "Singapore 4-Day Weather"
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_native_temperature_unit = "°C"
    _attr_native_wind_speed_unit = "km/h"

    # 🔥 Added so it appears under Singapore Weather Card device
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_weather_card")},
            "name": "Singapore Weather Card",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }

    # ==========================================================
    # CURRENT CONDITION (State)
    # ==========================================================

    @property
    def condition(self):
        try:
            f = self._today_forecast()
            return self._map_condition(f["forecast"]["text"])
        except Exception:
            return "cloudy"

    # ==========================================================
    # CURRENT TEMPERATURE (LIVE S06)
    # ==========================================================

    @property
    def native_temperature(self):
        try:
            state = self.hass.states.get(
                "sensor.paya_lebar_airport_s06_temperature"
            )
            if state and state.state not in ("unknown", "unavailable"):
                return float(state.state)
        except Exception:
            pass

        # fallback to forecast high
        try:
            f = self._today_forecast()
            return f["temperature"]["high"]
        except Exception:
            return None

    # ==========================================================
    # HUMIDITY (LIVE S06)
    # ==========================================================

    @property
    def humidity(self):
        try:
            state = self.hass.states.get(
                "sensor.paya_lebar_airport_s06_humidity"
            )
            if state and state.state not in ("unknown", "unavailable"):
                return float(state.state)
        except Exception:
            pass

        # fallback to forecast high
        try:
            f = self._today_forecast()
            return f["relativeHumidity"]["high"]
        except Exception:
            return None

    # ==========================================================
    # WIND (FROM FORECAST)
    # ==========================================================

    @property
    def native_wind_speed(self):
        try:
            state = self.hass.states.get(
                "sensor.paya_lebar_airport_s06_wind_speed"
            )
            if state and state.state not in ("unknown", "unavailable"):
                return float(state.state)
        except Exception:
            pass
        return None
    
    
    @property
    def wind_direction(self):
        try:
            state = self.hass.states.get(
                "sensor.paya_lebar_airport_s06_wind_direction"
            )
            if state and state.state not in ("unknown", "unavailable"):
                return state.attributes.get("compass")
        except Exception:
            pass
        return None

    # ==========================================================
    # DAILY FORECAST STRIP
    # ==========================================================

    async def async_forecast_daily(self):
        try:
            forecasts = self.coordinator.data["four_day_forecast"]["data"]["records"][0]["forecasts"]

            result = []

            for f in forecasts:
                result.append(
                    {
                        "datetime": f["timestamp"],
                        "temperature": f["temperature"]["high"],
                        "templow": f["temperature"]["low"],
                        "condition": self._map_condition(f["forecast"]["text"]),
                    }
                )

            return result

        except Exception:
            return []

    # ==========================================================
    # EXTRA ATTRIBUTES
    # ==========================================================

    @property
    def extra_state_attributes(self):
        try:
            record = self._record()
            f = self._today_forecast()

            return {
                "summary": f["forecast"]["summary"],
                "forecast_text": f["forecast"]["text"],
                "forecast_code": f["forecast"]["code"],

                "temp_low": f["temperature"]["low"],
                "temp_high": f["temperature"]["high"],

                "humidity_low": f["relativeHumidity"]["low"],
                "humidity_high": f["relativeHumidity"]["high"],

                "wind_speed_low": f["wind"]["speed"]["low"],
                "wind_speed_high": f["wind"]["speed"]["high"],
                "wind_direction": self.wind_direction,

                "last_updated": record["updatedTimestamp"],
            }

        except Exception:
            return {}

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    def _record(self):
        return self.coordinator.data["four_day_forecast"]["data"]["records"][0]

    def _all_forecasts(self):
        return self._record()["forecasts"]

    def _today_forecast(self):
        return self._all_forecasts()[0]

    def _map_condition(self, text: str) -> str:
        text = text.lower()

        if "thunder" in text:
            return "lightning-rainy"
        if "shower" in text:
            return "rainy"
        if "rain" in text:
            return "rainy"
        if "partly" in text:
            return "partlycloudy"
        if "cloud" in text:
            return "cloudy"
        if "fair" in text or "sunny" in text:
            return "sunny"

        return "cloudy"