"""
This component provides light support for Buspro.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/...
"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import LightEntity, ColorMode, PLATFORM_SCHEMA, ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_RGBW_COLOR
from homeassistant.const import (CONF_NAME, CONF_DEVICES)
from homeassistant.core import callback

from ..buspro import DATA_BUSPRO

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVICE_RUNNING_TIME = 0
DEFAULT_PLATFORM_RUNNING_TIME = 0
DEFAULT_TYPE = "monochrome"

DEVICE_SCHEMA = vol.Schema({
    vol.Optional("running_time", default=DEFAULT_DEVICE_RUNNING_TIME): cv.positive_int,
    vol.Optional("type", default=DEFAULT_TYPE): cv.string,
    vol.Required("channel"): cv.positive_int,
    vol.Required(CONF_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional("running_time", default=DEFAULT_PLATFORM_RUNNING_TIME): cv.positive_int,
    vol.Required(CONF_DEVICES): {cv.string: DEVICE_SCHEMA},
})


# noinspection PyUnusedLocal
async def async_setup_platform(hass, config, async_add_entites, discovery_info=None):
    """Set up Buspro light devices."""
    # noinspection PyUnresolvedReferences
    from .pybuspro.devices import Light

    hdl = hass.data[DATA_BUSPRO].hdl
    devices = []
    platform_running_time = int(config["running_time"])

    for address, device_config in config[CONF_DEVICES].items():
        
        name = device_config[CONF_NAME]
        device_running_time = int(device_config["running_time"])
        device_type = device_config['type']
        channel_number = int(device_config['channel'])

        if device_running_time == 0:
            device_running_time = platform_running_time
        if device_type!= "onoff":
            device_running_time = 0

        address2 = address.split('.')
        device_address = (int(address2[0]), int(address2[1]))
        # channel_number = int(address2[2])

        _LOGGER.debug("Adding '{}' light '{}' with address {} and channel number {}".format(device_type, name, device_address, channel_number))
        light = Light(hdl, device_type, device_address, channel_number, name)
        devices.append(BusproLight(hass, light, device_running_time, device_type))

    async_add_entites(devices)


# noinspection PyAbstractClass
class BusproLight(LightEntity):
    """Representation of a Buspro light."""

    def __init__(self, hass, device, running_time, type):
        self._hass = hass
        self._device = device
        self._type = type
        self._running_time = running_time
        self.setup_color_modes()
        self.async_register_callbacks()

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""

        # noinspection PyUnusedLocal
        async def after_update_callback(device):
            """Call after device was updated."""
            await self.async_update_ha_state()

        self._device.register_device_updated_cb(after_update_callback)

    @property
    def should_poll(self):
        """No polling needed within Buspro."""
        return False

    @property
    def name(self):
        """Return the display name of this light."""
        return self._device.name

    @property
    def available(self):
        """Return True if entity is available."""
        return self._hass.data[DATA_BUSPRO].connected

    @property
    def brightness(self):
        """Return the brightness of the light."""
        brightness = self._device.current_brightness
        return brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return RGB color of the light."""
        color = self._device.current_color 
        return color
    
    def setup_color_modes(self):
        self._attr_supported_color_modes = set()
        if self._type == "white" or self._type == "monochrome":
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
            # flags = LightEntity.ColorMode.BRIGHTNESS
        elif self._type == "rgb":
            # flags = LightEntity.ColorMode.RGB
            self._attr_supported_color_modes.add(ColorMode.RGB)
        elif self._type == "rgbw":
            # flags = LightEntity.ColorMode.RGBW
            self._attr_supported_color_modes.add(ColorMode.RGBW)
        else:
            # flags = LightEntity.ColorMode.ONOFF
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._device.is_on
    
    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.debug(f"Command `turn_on` with args: `{kwargs}`")

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs.get(ATTR_BRIGHTNESS)
            await self._device.async_turn_on(brightness, self._running_time)
        elif ATTR_RGB_COLOR in kwargs:
            color = kwargs.get(ATTR_RGB_COLOR)
            await self._device.async_turn_on_rgb(color, self._running_time)
        elif ATTR_RGBW_COLOR in kwargs:
            color = kwargs.get(ATTR_RGBW_COLOR)
            await self._device.async_turn_on_rgbw(color, self._running_time)

        # if not self.is_on and self._device.previous_brightness is not None and brightness == 100:
        #     brightness = self._device.previous_brightness

        

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self._device.set_off(self._running_time)

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._device.device_identifier


