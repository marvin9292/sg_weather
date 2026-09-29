DOMAIN = "singapore_weather"

SCAN_INTERVAL = 300  # 5 minutes

CONF_API_KEY = "api_key"
CONF_HOME_LATITUDE = "home_latitude"
CONF_HOME_LONGITUDE = "home_longitude"
CONF_WORK_LATITUDE = "work_latitude"
CONF_WORK_LONGITUDE = "work_longitude"

BASE_HEADERS = {
    "accept": "application/json",
    "User-Agent": "Home Assistant Singapore Weather",
}

RAIN_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
FORECAST_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
LIGHTNING_URL = "https://api-open.data.gov.sg/v2/real-time/api/weather?api=lightning"
FLOOD_URL = "https://api-open.data.gov.sg/v2/real-time/api/weather/flood-alerts"
WBGT_URL = "https://api-open.data.gov.sg/v2/real-time/api/weather?api=wbgt"
UVI_URL = "https://api-open.data.gov.sg/v2/real-time/api/uv"
TEMPERATURE_URL = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
HUMIDITY_URL = "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity"
WIND_SPEED_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-speed"
WIND_DIRECTION_URL = "https://api-open.data.gov.sg/v2/real-time/api/wind-direction"
FOUR_DAY_FORECAST_URL = "https://api-open.data.gov.sg/v2/real-time/api/four-day-outlook"
PM25_URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25"
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
