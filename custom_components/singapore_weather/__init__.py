from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from datetime import timedelta
import asyncio
import logging

from .const import (
    DOMAIN,
    BASE_HEADERS,
    CONF_API_KEY,
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_WORK_LATITUDE,
    CONF_WORK_LONGITUDE,
    RAIN_URL,
    FORECAST_URL,
    LIGHTNING_URL,
    FLOOD_URL,
    WBGT_URL,
    UVI_URL,
    TEMPERATURE_URL,
    HUMIDITY_URL,
    WIND_SPEED_URL,
    WIND_DIRECTION_URL,
    FOUR_DAY_FORECAST_URL,
    PM25_URL,
    PSI_URL,
)


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "camera", "weather"]


async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate old Singapore Weather config entries."""
    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry,
            version=2,
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
):

    required_private_settings = (
        CONF_API_KEY,
        CONF_HOME_LATITUDE,
        CONF_HOME_LONGITUDE,
        CONF_WORK_LATITUDE,
        CONF_WORK_LONGITUDE,
    )
    if any(key not in entry.data for key in required_private_settings):
        raise ConfigEntryAuthFailed(
            "Singapore Weather private settings are required. Reauthenticate the integration."
        )

    api_key = str(entry.data[CONF_API_KEY]).strip()
    if not api_key:
        raise ConfigEntryAuthFailed(
            "data.gov.sg API key is required. Reauthenticate Singapore Weather."
        )

    session = async_get_clientsession(hass)
    headers = dict(BASE_HEADERS)
    headers["x-api-key"] = api_key

    # ==========================================================
    # API FETCH
    # ==========================================================

    async def fetch_json(url):
        try:
            async with session.get(
                url,
                headers=headers,
                timeout=15,
            ) as resp:

                if resp.status in (401, 403):
                    raise ConfigEntryAuthFailed(
                        "Invalid data.gov.sg API key"
                    )

                if resp.status != 200:
                    raise UpdateFailed(
                        f"API {url} returned status {resp.status}"
                    )

                return await resp.json()

        except (ConfigEntryAuthFailed, UpdateFailed):
            raise
        except Exception as err:
            raise UpdateFailed(
                f"API error for {url}: {err}"
            ) from err

    # ==========================================================
    # WIND DIAGNOSTIC
    # ==========================================================

    def log_wind_diagnostic(
        label: str,
        payload,
        station_id: str = "S109",
    ):
        """
        Log exactly what data.gov.sg returned for S109.

        This does NOT expose the API key.
        """

        if payload is None:
            _LOGGER.warning(
                "[WIND DIAG] %s: payload is None",
                label,
            )
            return

        if not isinstance(payload, dict):
            _LOGGER.warning(
                "[WIND DIAG] %s: unexpected payload type: %s",
                label,
                type(payload).__name__,
            )
            return

        try:
            api_code = payload.get("code")
            data = payload.get("data") or {}

            stations = data.get("stations") or []
            reading_blocks = data.get("readings") or []
            reading_unit = data.get("readingUnit")

            # --------------------------------------------------
            # Check whether S109 exists in station metadata
            # --------------------------------------------------

            station_info = None

            for station in stations:
                if station.get("id") == station_id:
                    station_info = station
                    break

            # --------------------------------------------------
            # Find S109 actual reading
            # --------------------------------------------------

            found_reading = None
            found_timestamp = None

            reading_count = 0
            available_station_ids = []

            for block in reading_blocks:

                timestamp = block.get("timestamp")

                readings = block.get("data") or []

                reading_count += len(readings)

                for reading in readings:

                    sid = reading.get("stationId")

                    if sid:
                        available_station_ids.append(sid)

                    if sid == station_id:
                        found_reading = reading.get("value")
                        found_timestamp = timestamp

            # --------------------------------------------------
            # Diagnostic output
            # --------------------------------------------------

            _LOGGER.warning(
                "[WIND DIAG] %s | "
                "api_code=%s | "
                "unit=%s | "
                "station_metadata_S109=%s | "
                "reading_S109=%s | "
                "value=%s | "
                "timestamp=%s | "
                "reading_count=%s",
                label,
                api_code,
                reading_unit,
                station_info is not None,
                found_reading is not None,
                found_reading,
                found_timestamp,
                reading_count,
            )

            # If S109 is missing, log which station IDs
            # actually appeared in the reading payload.

            if found_reading is None:
                _LOGGER.warning(
                    "[WIND DIAG] %s | "
                    "S109 missing. Available station IDs: %s",
                    label,
                    ",".join(
                        sorted(set(available_station_ids))
                    ),
                )

        except Exception as err:
            _LOGGER.exception(
                "[WIND DIAG] Error inspecting %s response: %s",
                label,
                err,
            )

    # ==========================================================
    # MAIN DATA
    # Update every 5 minutes
    # ==========================================================

    async def async_update_main():

        data = {}

        data["rain"] = await fetch_json(RAIN_URL)
        data["forecast"] = await fetch_json(FORECAST_URL)
        data["lightning"] = await fetch_json(LIGHTNING_URL)
        data["flood"] = await fetch_json(FLOOD_URL)
        data["wbgt"] = await fetch_json(WBGT_URL)
        data["uvi"] = await fetch_json(UVI_URL)
        data["temperature"] = await fetch_json(TEMPERATURE_URL)
        data["humidity"] = await fetch_json(HUMIDITY_URL)

        # ------------------------------------------------------
        # WIND SPEED
        # ------------------------------------------------------

        data["wind_speed"] = await fetch_json(
            WIND_SPEED_URL
        )

        log_wind_diagnostic(
            "WIND SPEED",
            data["wind_speed"],
        )

        # ------------------------------------------------------
        # WIND DIRECTION
        # ------------------------------------------------------

        data["wind_direction"] = await fetch_json(
            WIND_DIRECTION_URL
        )

        log_wind_diagnostic(
            "WIND DIRECTION",
            data["wind_direction"],
        )

        # ------------------------------------------------------
        # PM2.5
        # ------------------------------------------------------

        data["pm25"] = await fetch_json(PM25_URL)

        return data

    main_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_main",
        update_method=async_update_main,
        update_interval=timedelta(minutes=5),
    )

    # ==========================================================
    # PSI
    # ==========================================================

    async def async_update_psi():

        return {
            "psi": await fetch_json(PSI_URL)
        }

    psi_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_psi",
        update_method=async_update_psi,
        update_interval=timedelta(minutes=30),
    )

    # ==========================================================
    # 4 DAY FORECAST
    # ==========================================================

    async def async_update_four_day():

        return {
            "four_day_forecast":
                await fetch_json(FOUR_DAY_FORECAST_URL)
        }

    four_day_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_fourday",
        update_method=async_update_four_day,
        update_interval=timedelta(hours=2),
    )

    # ==========================================================
    # INITIAL REFRESH
    # ==========================================================

    await main_coordinator.async_config_entry_first_refresh()

    # Main coordinator already performs 11 API requests.
    # Wait before making PSI / four-day calls.
    await asyncio.sleep(10)

    await psi_coordinator.async_config_entry_first_refresh()
    await four_day_coordinator.async_config_entry_first_refresh()

    # ==========================================================
    # STORE COORDINATORS
    # ==========================================================

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "main": main_coordinator,
        "psi": psi_coordinator,
        "fourday": four_day_coordinator,
    }

    # ==========================================================
    # LOAD PLATFORMS
    # ==========================================================

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        domain_data = hass.data.get(DOMAIN)
        if domain_data is not None:
            domain_data.pop(entry.entry_id, None)

            if not domain_data:
                hass.data.pop(DOMAIN, None)

    return unload_ok