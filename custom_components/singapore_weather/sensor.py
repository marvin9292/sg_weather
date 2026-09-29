from __future__ import annotations

import math
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_WORK_LATITUDE,
    CONF_WORK_LONGITUDE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SingaporeWeatherBase(CoordinatorEntity):

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_weather")},
            "name": "Singapore Weather",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }


# ==========================================================
# DEFINE
# ==========================================================

def slugify(text: str) -> str:
    return text.lower().replace(" ", "_").replace("-", "_")

def create_forecast_sensors(coordinator):
    sensors = []
    try:
        forecasts = coordinator.data["forecast"]["data"]["items"][0]["forecasts"]

        for f in forecasts:
            area = f["area"]
            area_slug = slugify(area)

            sensors.append(
                ForecastSensor(
                    coordinator,
                    area,
                    f"{area_slug}_forecast",
                    f"{area} Forecast",
                )
            )
    except Exception:
        pass
    return sensors

def create_temperature_sensors(coordinator):
    sensors = []
    try:
        stations = coordinator.data["temperature"]["data"]["stations"]
        for s in stations:
            if s["id"] != "S06":
                continue

            station_id = s["id"]
            name_slug = slugify(s["name"])
            sensors.append(
                TemperatureSensor(
                    coordinator,
                    station_id,
                    f"{name_slug}_{station_id}_temperature",
                    f"{s['name']} ({station_id}) Temperature",
                )
            )
    except Exception:
        pass
    return sensors

def create_humidity_sensors(coordinator):
    sensors = []
    try:
        stations = coordinator.data["humidity"]["data"]["stations"]
        for s in stations:
            if s["id"] != "S06":
                continue

            station_id = s["id"]
            name_slug = slugify(s["name"])
            sensors.append(
                HumiditySensor(
                    coordinator,
                    station_id,
                    f"{name_slug}_{station_id}_humidity",
                    f"{s['name']} ({station_id}) Humidity",
                )
            )
    except Exception:
        pass
    return sensors

def _deg_to_compass(deg):
    if deg is None:
        return None
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(deg / 45) % 8
    return directions[idx]

# ==========================================================
# SETUP
# ==========================================================
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinators = hass.data[DOMAIN][entry.entry_id]
    main = coordinators["main"]
    psi = coordinators["psi"]
    fourday = coordinators["fourday"]

    entities = [

        # ================= RAIN =================
        RainfallSensor(main, "S115", "rainfall_tuas_s115", "Rainfall Tuas (S115)"),
        RainfallSensor(main, "S50", "rainfall_clementi_s50", "Rainfall Clementi (S50)"),
        RainfallSensor(main, "S230", "rainfall_west_coast_road_s230", "Rainfall West Coast Road (S230)"),
        RainfallSensor(main, "S81", "rainfall_punggol_central_s81", "Rainfall Punggol Central (S81)"),
        RainfallSensor(main, "S119", "rainfall_nicoll_highway_s119", "Rainfall Nicoll Highway (S119)"),

        # ================= WBGT =================
        WBGTTemperatureSensor(main),
        WBGTHeatStressSensor(main),

        # ================= FLOOD =================
        FloodSensor(main),

        # ================= LIGHTNING =================
        LightningRawSensor(main),
        LightningNearHomeSensor(
            main,
            entry.data[CONF_HOME_LATITUDE],
            entry.data[CONF_HOME_LONGITUDE],
        ),
        LightningNearWorkSensor(
            main,
            entry.data[CONF_WORK_LATITUDE],
            entry.data[CONF_WORK_LONGITUDE],
        ),
        LightningCloudToGroundSensor(main),

        # ================= PM2.5 =================
        PM25OneHourSensor(main, "east"),
        PM25OneHourSensor(main, "south"),
        PM25OneHourSensor(main, "west"),
        PM25OneHourSensor(main, "north"),
        PM25OneHourSensor(main, "central"),

        # ================= PSI =================
        PSIPollutantIndexSensor(psi, "east", "co_index"),
        PSIPollutantIndexSensor(psi, "east", "so2_index"),
        PSIPollutantIndexSensor(psi, "east", "no2_index"),
        PSIPollutantIndexSensor(psi, "east", "o3_index"),
        PSIPollutantIndexSensor(psi, "east", "pm10_index"),
        PSIPollutantIndexSensor(psi, "east", "pm25_index"),
        PSIOverallSensor(psi, "east"),

        PSIPollutantIndexSensor(psi, "south", "co_index"),
        PSIPollutantIndexSensor(psi, "south", "so2_index"),
        PSIPollutantIndexSensor(psi, "south", "no2_index"),
        PSIPollutantIndexSensor(psi, "south", "o3_index"),
        PSIPollutantIndexSensor(psi, "south", "pm10_index"),
        PSIPollutantIndexSensor(psi, "south", "pm25_index"),
        PSIOverallSensor(psi, "south"),

        PSIPollutantIndexSensor(psi, "west", "co_index"),
        PSIPollutantIndexSensor(psi, "west", "so2_index"),
        PSIPollutantIndexSensor(psi, "west", "no2_index"),
        PSIPollutantIndexSensor(psi, "west", "o3_index"),
        PSIPollutantIndexSensor(psi, "west", "pm10_index"),
        PSIPollutantIndexSensor(psi, "west", "pm25_index"),
        PSIOverallSensor(psi, "west"),

        PSIPollutantIndexSensor(psi, "north", "co_index"),
        PSIPollutantIndexSensor(psi, "north", "so2_index"),
        PSIPollutantIndexSensor(psi, "north", "no2_index"),
        PSIPollutantIndexSensor(psi, "north", "o3_index"),
        PSIPollutantIndexSensor(psi, "north", "pm10_index"),
        PSIPollutantIndexSensor(psi, "north", "pm25_index"),
        PSIOverallSensor(psi, "north"),

        PSIPollutantIndexSensor(psi, "central", "co_index"),
        PSIPollutantIndexSensor(psi, "central", "so2_index"),
        PSIPollutantIndexSensor(psi, "central", "no2_index"),
        PSIPollutantIndexSensor(psi, "central", "o3_index"),
        PSIPollutantIndexSensor(psi, "central", "pm10_index"),
        PSIPollutantIndexSensor(psi, "central", "pm25_index"),
        PSIOverallSensor(psi, "central"),
        
        # ================= UVI =================
        UVISensor(main),
    ]

    entities.extend(create_forecast_sensors(main))
    entities.extend(create_temperature_sensors(main))
    entities.extend(create_humidity_sensors(main))

    entities.append(
        WindSpeedSensor(
            main,
            "S06",
            "paya_lebar_airport_s06_wind_speed",
            "Paya Lebar Airport (S06) Wind Speed",
        )
    )

    entities.append(
        WindDirectionSensor(
            main,
            "S06",
            "paya_lebar_airport_s06_wind_direction",
            "Paya Lebar Airport (S06) Wind Direction",
        )
    )

    async_add_entities(entities)


# ==========================================================
# RAIN
# ==========================================================

class RainfallSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:weather-rainy"
    _attr_native_unit_of_measurement = "mm"
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, station, unique_id, name):
        super().__init__(coordinator)
        self._station = station
        self._attr_unique_id = unique_id
        self._attr_name = name

    @property
    def native_value(self):
        try:
            reading_block = self.coordinator.data["rain"]["data"]["readings"][0]
            for r in reading_block["data"]:
                if r["stationId"] == self._station:
                    return float(r["value"])
        except Exception:
            return None

    @property
    def extra_state_attributes(self):
        try:
            return {"timestamp": self.coordinator.data["rain"]["data"]["readings"][0]["timestamp"]}
        except Exception:
            return {}

# ==========================================================
# WBGT
# ==========================================================

class WBGTTemperatureSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "sengkang_wbgt"
    _attr_name = "Sengkang WBGT"
    _attr_icon = "mdi:thermometer"
    _attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self):
        try:
            readings = (
                self.coordinator.data["wbgt"]["data"]["records"][0]
                ["item"]["readings"]
            )

            for r in readings:
                if r["station"]["id"] == "S184":
                    value = r.get("wbgt")

                    if value in (None, "", "NA", "N/A"):
                        return None

                    return float(value)

        except (KeyError, IndexError, TypeError, ValueError):
            return None

        return None

class WBGTHeatStressSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "sengkang_heat_stress"
    _attr_name = "Sengkang Heat Stress"
    _attr_icon = "mdi:alert"

    @property
    def native_value(self):
        try:
            readings = self.coordinator.data["wbgt"]["data"]["records"][0]["item"]["readings"]
            for r in readings:
                if r["station"]["id"] == "S184":
                    return r["heatStress"]
        except Exception:
            return None


# ==========================================================
# FLOOD
# ==========================================================

class FloodSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "singapore_flood_status"
    _attr_name = "Singapore Flood Status"
    _attr_icon = "mdi:weather-flood"

    @property
    def native_value(self):
        try:
            readings = self.coordinator.data["flood"]["data"]["records"][0]["item"]["readings"]
            return "Flood" if readings else "No Flood"
        except Exception:
            return "No Flood"

    @property
    def extra_state_attributes(self):
        try:
            return {"readings": self.coordinator.data["flood"]["data"]["records"][0]["item"]["readings"]}
        except Exception:
            return {"readings": []}


# ==========================================================
# LIGHTNING RAW
# ==========================================================

class LightningRawSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "singapore_lightning_raw"
    _attr_name = "Singapore Lightning Raw"
    _attr_icon = "mdi:weather-lightning"

    @property
    def native_value(self):
        try:
            strikes = self.coordinator.data["lightning"]["data"]["records"][0]["item"]["readings"]
            return len(strikes)
        except Exception:
            return 0

    @property
    def extra_state_attributes(self):
        try:
            strikes = self.coordinator.data["lightning"]["data"]["records"][0]["item"]["readings"]
            return {"readings": strikes}
        except Exception:
            return {"readings": []}


# ==========================================================
# LIGHTNING NEAR BASE
# ==========================================================

class _LightningNearBase(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:weather-lightning"
    radius = 2.5

    def __init__(self, coordinator, latitude: float, longitude: float):
        super().__init__(coordinator)
        self.lat0 = float(latitude)
        self.lon0 = float(longitude)

    def _calculate(self):
        try:
            strikes = self.coordinator.data["lightning"]["data"]["records"][0]["item"]["readings"]
        except Exception:
            return 0, None, None, None, None

        nearest = 999
        nearest_lat = None
        nearest_lon = None
        nearest_text = None
        count = 0

        for s in strikes:
            try:
                lat = float(s["location"]["latitude"])
                lon = float(s["location"]["longitude"])
            except Exception:
                continue

            dx = (lat - self.lat0) * 111
            dy = (lon - self.lon0) * 111
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= self.radius:
                count += 1
                if dist < nearest:
                    nearest = dist
                    nearest_lat = lat
                    nearest_lon = lon
                    nearest_text = s.get("text")

        return count, nearest_lat, nearest_lon, nearest_text, nearest

    @property
    def native_value(self):
        count, *_ = self._calculate()
        return count

    @property
    def extra_state_attributes(self):
        count, lat, lon, text, nearest = self._calculate()

        if lat is None:
            return {
                "nearest_km": None,
                "direction": None,
                "gps": "",
                "strike_text": None,
            }

        y = lon - self.lon0
        x = lat - self.lat0
        bearing = math.degrees(math.atan2(y, x))
        if bearing < 0:
            bearing += 360

        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
        direction = dirs[int((bearing + 22.5) / 45)]

        return {
            "nearest_km": round(nearest, 2),
            "direction": direction,
            "gps": f"{lat},{lon}",
            "strike_text": text,
        }


class LightningNearHomeSensor(_LightningNearBase):
    _attr_unique_id = "lightning_near_home"
    _attr_name = "Lightning Near Home"


class LightningNearWorkSensor(_LightningNearBase):
    _attr_unique_id = "lightning_near_work"
    _attr_name = "Lightning Near Work"


# ==========================================================
# CLOUD TO GROUND
# ==========================================================

class LightningCloudToGroundSensor(SingaporeWeatherBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "lightning_cloud_to_ground"
    _attr_name = "Lightning Cloud To Ground"
    _attr_icon = "mdi:weather-lightning"

    @property
    def native_value(self):
        try:
            strikes = self.coordinator.data["lightning"]["data"]["records"][0]["item"]["readings"]
            return sum(
                1 for s in strikes
                if s.get("text") in ["Cloud to Ground", "Cloud-to-Ground"]
            )
        except Exception:
            return 0

    @property
    def extra_state_attributes(self):
        try:
            strikes = self.coordinator.data["lightning"]["data"]["records"][0]["item"]["readings"]
            gps_list = []
            for s in strikes:
                if s.get("text") in ["Cloud to Ground", "Cloud-to-Ground"]:
                    try:
                        lat = float(s["location"]["latitude"])
                        lon = float(s["location"]["longitude"])
                        gps_list.append({"lat": lat, "lon": lon})
                    except Exception:
                        continue
            return {"gps_list": gps_list}
        except Exception:
            return {"gps_list": []}

# ==========================================================
# CHANGE DEVICE CLASS TO SINGAPORE WEATHER FORECAST FOR ALL AREA FORECAST
# ==========================================================
class SingaporeWeatherForecasttBase(CoordinatorEntity):

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_weather_forecast")},
            "name": "Singapore Weather Forecast",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }

# ==========================================================
# FORECAST
# ==========================================================

class ForecastSensor(SingaporeWeatherForecasttBase, SensorEntity):
    _attr_should_poll = False

    def __init__(self, coordinator, area, unique_id, name):
        super().__init__(coordinator)
        self._area = area
        self._attr_unique_id = unique_id
        self._attr_name = name

    @property
    def native_value(self):
        try:
            forecasts = self.coordinator.data["forecast"]["data"]["items"][0]["forecasts"]
            for f in forecasts:
                if f["area"] == self._area:
                    return f["forecast"]
        except Exception:
            return "Unknown"

    @property
    def icon(self):
        state = self.native_value

        if not state:
            return "mdi:weather-cloudy"

        mapping = {
            "Fair": "mdi:weather-sunny",
            "Fair (Day)": "mdi:weather-sunny",
            "Fair (Night)": "mdi:weather-night",
            "Fair & Warm": "mdi:weather-sunny-alert",

            "Partly Cloudy": "mdi:weather-partly-cloudy",
            "Partly Cloudy (Day)": "mdi:weather-partly-cloudy",
            "Partly Cloudy (Night)": "mdi:weather-night-partly-cloudy",

            "Cloudy": "mdi:weather-cloudy",
            "Hazy": "mdi:weather-hazy",
            "Slightly Hazy": "mdi:weather-hazy",
            "Windy": "mdi:weather-windy",
            "Mist": "mdi:weather-fog",
            "Fog": "mdi:weather-fog",

            "Light Rain": "mdi:weather-rainy",
            "Moderate Rain": "mdi:weather-pouring",
            "Heavy Rain": "mdi:weather-pouring",

            "Passing Showers": "mdi:weather-rainy",
            "Light Showers": "mdi:weather-rainy",
            "Showers": "mdi:weather-rainy",
            "Heavy Showers": "mdi:weather-pouring",

            "Thundery Showers": "mdi:weather-lightning-rainy",
            "Heavy Thundery Showers": "mdi:weather-lightning-rainy",
            "Heavy Thundery Showers with Gusty Winds": "mdi:weather-lightning-rainy",
        }

        return mapping.get(state, "mdi:weather-cloudy")

# ==========================================================
# CAHNGE DEVICE CLASS TO SINGAPORE WEATHER CLASS FOR PM2.5 (1 HOUR) AND PSI
# ==========================================================
class SingaporePollutantBase(CoordinatorEntity):

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_pollutant")},
            "name": "Singapore Pollutant",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }

# ==========================================================
# PM2.5 (1-HOUR)
# ==========================================================

class PM25OneHourSensor(SingaporePollutantBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:blur"
    _attr_native_unit_of_measurement = "µg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, region: str):
        super().__init__(coordinator)
        self._region = region.lower()
        self._attr_unique_id = f"singapore_{self._region}_pm25"
        self._attr_name = f"Singapore {self._region.capitalize()} PM2.5"
        self._attr_native_unit_of_measurement = "µg/m³"

    @property
    def native_value(self):
        pm25 = self.coordinator.data.get("pm25")
        if not pm25 or "data" not in pm25:
            return None

        items = pm25["data"].get("items")
        if not items:
            return None

        readings = items[0].get("readings", {}).get("pm25_one_hourly", {})
        return readings.get(self._region)


# ==========================================================
# PSI (POLLUTANT INDEX + OVERALL)
# ==========================================================

class PSIPollutantIndexSensor(SingaporePollutantBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:chemical-weapon"
    _attr_state_class = SensorStateClass.MEASUREMENT

    _POLLUTANT_MAP = {
        "co_index": "co_sub_index",
        "so2_index": "so2_sub_index",
        "o3_index": "o3_sub_index",
        "pm10_index": "pm10_sub_index",
        "pm25_index": "pm25_sub_index",
        "no2_index": "no2_one_hour_max",
    }

    def __init__(self, coordinator, region: str, pollutant: str):
        super().__init__(coordinator)
        self._region = region.lower()
        self._pollutant = pollutant.lower()

        self._api_key = self._POLLUTANT_MAP.get(self._pollutant, self._pollutant)

        self._attr_unique_id = f"singapore_{self._region}_{self._pollutant}"
        self._attr_name = f"Singapore {self._region.capitalize()} {self._pollutant.upper()}"

    @property
    def native_value(self):
        try:
            readings = self.coordinator.data["psi"]["data"]["items"][0]["readings"]
            return readings[self._api_key][self._region]
        except Exception:
            return None

class PSIOverallSensor(SingaporePollutantBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:gauge"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, region: str):
        super().__init__(coordinator)
        self._region = region.lower()
        self._attr_unique_id = f"singapore_{self._region}_psi"
        self._attr_name = f"Singapore {self._region.capitalize()} PSI"

    @property
    def native_value(self):
        try:
            readings = (
                self.coordinator.data["psi"]["data"]["items"][0]
                ["readings"]["psi_twenty_four_hourly"]
            )
            return readings.get(self._region)
        except Exception:
            return None

# ==========================================================
# CHANGE DEVICE CLASS FOR UVI, PAYA LEBAR AIRPORT TEMPERATURE, HUMIDITY, WIND SPEED, WIND DIRECTION TO DEVICE SINGAPORE WEATHER CLASS
# ==========================================================
class SingaporeWeatherCardBase(CoordinatorEntity):

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_weather_card")},
            "name": "Singapore Weather Card",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }

# ==========================================================
# UVI
# ==========================================================

class UVISensor(SingaporeWeatherCardBase, SensorEntity):
    _attr_should_poll = False
    _attr_unique_id = "singapore_uvi"
    _attr_name = "Singapore UVI"
    _attr_icon = "mdi:white-balance-sunny"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        try:
            return self.coordinator.data["uvi"]["data"]["records"][0]["index"][0]["value"]
        except Exception:
            return None

# ==========================================================
# PAYA LEBAR AIRPORT TEMPERATURE
# ==========================================================

class TemperatureSensor(SingaporeWeatherCardBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:thermometer"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, station, unique_id, name):
        super().__init__(coordinator)
        self._station = station
        self._attr_unique_id = unique_id
        self._attr_name = name

    @property
    def native_value(self):
        try:
            reading_blocks = self.coordinator.data["temperature"]["data"].get("readings", [])
            for block in reversed(reading_blocks):
                for r in block.get("data", []):
                    if r.get("stationId") == self._station:
                        return float(r["value"])
        except Exception:
            return None
        return None


# ==========================================================
# PAYA LEBAR AIRPORT HUMIDITY
# ==========================================================

class HumiditySensor(SingaporeWeatherCardBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:water-percent"
    _attr_native_unit_of_measurement = "%"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, station, unique_id, name):
        super().__init__(coordinator)
        self._station = station
        self._attr_unique_id = unique_id
        self._attr_name = name

    @property
    def native_value(self):
        try:
            reading_blocks = self.coordinator.data["humidity"]["data"].get("readings", [])
            for block in reversed(reading_blocks):
                for r in block.get("data", []):
                    if r.get("stationId") == self._station:
                        return float(r["value"])
        except Exception:
            return None
        return None
            
# ==========================================================
# PAYA LEBAR AIRPORT WIND SPEED
# ==========================================================
class WindSpeedSensor(SingaporeWeatherCardBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:weather-windy"
    _attr_native_unit_of_measurement = "km/h"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, station, unique_id, name):
        super().__init__(coordinator)
        self._station = station
        self._attr_unique_id = unique_id
        self._attr_name = name

    @property
    def native_value(self):
        try:
            reading_blocks = self.coordinator.data["wind_speed"]["data"].get("readings", [])
            for block in reversed(reading_blocks):
                for r in block.get("data", []):
                    if r.get("stationId") == self._station:
                        # data.gov.sg wind speed is reported in knots.
                        # Convert to km/h to match this entity's unit.
                        return round(float(r["value"]) * 1.852, 2)
        except Exception:
            return None
        return None

# ==========================================================
# PAYA LEBAR AIRPORT WIND DIRECTION
# ==========================================================
class WindDirectionSensor(SingaporeWeatherCardBase, SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:compass"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, station, unique_id, name):
        super().__init__(coordinator)
        self._station = station
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._deg = None

    @property
    def native_value(self):
        try:
            reading_blocks = self.coordinator.data["wind_direction"]["data"].get("readings", [])
            for block in reversed(reading_blocks):
                for r in block.get("data", []):
                    if r.get("stationId") == self._station:
                        self._deg = float(r["value"]) % 360
                        return self._deg
        except Exception:
            return None
        return None

    @property
    def extra_state_attributes(self):
        if self._deg is None:
            return {}
        return {
            "compass": _deg_to_compass(self._deg)
        }