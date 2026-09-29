from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from datetime import datetime, timezone, timedelta
import math
import io
from PIL import Image
from .const import DOMAIN

RAIN_PREFIX = "https://www.weather.gov.sg/files/rainarea/50km/v2/dpsri_70km_"
RAIN_SUFFIX = "0000dBR.dpsri.png"
RAIN_PAGE = "https://www.weather.gov.sg/weather-rain-area-50km/"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    async_add_entities([
        SingaporeRainAnimatedCamera(hass)
    ])

# ==========================================================
# ANIMATED RAIN MAP
# ==========================================================

class SingaporeRainAnimatedCamera(Camera):

    def __init__(self, hass):
        super().__init__()
        self.hass = hass
        self._attr_name = "Singapore Weather Animated Rain Map"
        self._attr_unique_id = "singapore_weather_animated_rain_map"
        self._attr_content_type = "image/gif"

    # 🔥 Added so it appears under Singapore Weather Card device
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "singapore_weather_card")},
            "name": "Singapore Weather Card",
            "manufacturer": "data.gov.sg",
            "model": "Weather API",
        }

    async def async_camera_image(self, width=None, height=None):

        session = async_get_clientsession(self.hass)

        try:
            async with session.get(RAIN_PAGE, timeout=15) as page:
                text = await page.text()
        except Exception:
            return None

        start = text.find('slideshowimages("') + len('slideshowimages("')
        end = text.find(');', start)
        images_str = text[start:end]
        urls = images_str.replace('"', '').split(",")

        frames = []

        for url in urls[1:]:
            try:
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        frame = Image.open(io.BytesIO(await r.read()))
                        frames.append(frame)
            except Exception:
                continue

        if not frames:
            return None

        buff = io.BytesIO()
        frames[0].save(
            buff,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=[100] * (len(frames)-1) + [1000],
            loop=0,
            disposal=2
        )

        return buff.getvalue()