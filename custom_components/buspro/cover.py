"""
This component provides cover support for Buspro.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/...
"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.cover import CoverEntity, CoverEntityFeature, CoverDeviceClass, PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_DEVICES)
from homeassistant.core import callback

from ..buspro import DATA_BUSPRO

_LOGGER = logging.getLogger(__name__)

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): {cv.string: DEVICE_SCHEMA},
})


# noinspection PyUnusedLocal
async def async_setup_platform(hass, config, async_add_entites, discovery_info=None):
    """Set up Buspro cover devices."""
    # noinspection PyUnresolvedReferences
    from .pybuspro.devices import Cover

    hdl = hass.data[DATA_BUSPRO].hdl
    devices = []

    for address, device_config in config[CONF_DEVICES].items():
        name = device_config[CONF_NAME]

        address2 = address.split('.')
        device_address = (int(address2[0]), int(address2[1]))
        channel_number = int(address2[2])
        _LOGGER.debug("Adding cover '{}' with address {} and channel number {}".format(name, device_address,
                                                                                        channel_number))

        cover = Cover(hdl, device_address, channel_number, name)

        devices.append(BusproCover(hass, cover))

    async_add_entites(devices)


# noinspection PyAbstractClass
class BusproCover(CoverEntity):
    """Representation of a Buspro cover."""

    def __init__(self, hass, device):
        self._hass = hass
        self._device = device
        self._attr_device_class = CoverDeviceClass.CURTAIN
        # self.setup_features()
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
        """Return the display name of this cover."""
        return self._device.name

    @property
    def available(self):
        """Return True if entity is available."""
        return self._hass.data[DATA_BUSPRO].connected

    @property
    def is_closed(self):
        """Return true if cover is closed."""
        return self._device.is_closed


    # def setup_features(self):
    #     """Return the list of supported features."""
    #     self._attr_supported_features = (   CoverEntityFeature.OPEN |
    #                                         CoverEntityFeature.CLOSE |
    #                                         CoverEntityFeature.STOP)

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )
        return features

    async def async_open_cover(self, **kwargs):
        """Instruct the cover to open."""
        await self._device.set_open()

    async def async_close_cover(self, **kwargs):
        """Instruct the cover to close."""
        await self._device.set_close()

    async def async_stop_cover(self, **kwargs):
        """Instruct the cover to stop."""
        await self._device.set_stop()

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._device.device_identifier
