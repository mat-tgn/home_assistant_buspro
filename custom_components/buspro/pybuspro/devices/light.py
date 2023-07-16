from .control import _SingleChannelControl
from .device import Device
from ..helpers.enums import *
from ..helpers.generics import Generics


class Light(Device):
    def __init__(self, buspro, device_type, device_address, channel_number, name="", delay_read_current_state_seconds=0):
        super().__init__(buspro, device_address, name)
        # device_address = (subnet_id, device_id, channel_number)

        self._buspro = buspro
        self._device_type = device_type
        self._device_address = device_address
        self._channel = channel_number
        self._brightness = 0
        self._r = 0
        self._g = 0
        self._b = 0
        self._w = 0
        self._previous_brightness = None
        self.register_telegram_received_cb(self._telegram_received_cb)
        self._call_read_current_status_of_channels(run_from_init=True)

    def _telegram_received_cb(self, telegram):

        # if telegram.target_address[1] == 72:
        #    print("==== {}".format(str(telegram)))

        if telegram.operate_code == OperateCode.SingleChannelControlResponse:
            channel = telegram.payload[0]
            # success = telegram.payload[1]
            brightness = telegram.payload[2]
            if channel == self._channel:
                self._brightness = (brightness/100)*255
                self._set_previous_brightness(self._brightness)
                self._call_device_updated()
        elif telegram.operate_code == OperateCode.ReadStatusOfChannelsResponse:
            if self._channel <= telegram.payload[0]:
                self._brightness = (telegram.payload[self._channel]/100)*255
                self._set_previous_brightness(self._brightness)
                self._call_device_updated()
        elif telegram.operate_code == OperateCode.SceneControlResponse:
            self._call_read_current_status_of_channels()

    async def set_on(self, running_time_seconds=0):
        self._brightness = 255
        await self.channel_control(self._channel , self._brightness , running_time_seconds)

    async def set_off(self, running_time_seconds=0):
        self._brightness = 0
        await self.channel_control(self._channel , self._brightness , running_time_seconds)

    async def async_turn_on(self, intensity, running_time_seconds=0):
        self._set_previous_brightness(self._brightness)
        self._brightness = intensity        
        await self.channel_control(self._channel , self._brightness, running_time_seconds)

    async def async_turn_on_rgb(self,color,running_time_seconds=0):
        (r,g,b) = color
        self._r = r
        self._g = g
        self._b = b
        await self.channel_control(self._channel , r, running_time_seconds)
        await self.channel_control(self._channel+1 , g, running_time_seconds )
        await self.channel_control(self._channel+2 , b, running_time_seconds )

    async def async_turn_on_rgbw(self,color,running_time_seconds=0):
        (r,g,b,w) = color
        self._r = r
        self._g = g
        self._b = b
        self._w = w
        await self.channel_control(self._channel , r, running_time_seconds )
        await self.channel_control(self._channel+1 , g, running_time_seconds )
        await self.channel_control(self._channel+2 , b, running_time_seconds )
        await self.channel_control(self._channel+3 , w, running_time_seconds )

    async def read_status(self):
        raise NotImplementedError

    @property
    def device_identifier(self):
        return f"{self._device_address}-{self._channel}"

    @property
    def supports_brightness(self):
        return True

    @property
    def previous_brightness(self):
        return self._previous_brightness

    @property
    def current_brightness(self):
        return self._brightness 
    
    @property
    def current_color(self):
        if self._device_type == 'rgb':
            return (self._r, self._g, self._b)
        elif self._device_type == 'rgbw':
            return (self._r, self._g, self._b, self._w)

    @property
    def is_on(self):
        if self._brightness == 0:
            return False
        else:
            return True

    def _set_previous_brightness(self, brightness):
        #if self.supports_brightness and brightness > 0:
        self._previous_brightness = brightness

    async def channel_control(self, channel, value, running_time_seconds=0):
        generics = Generics()
        (minutes, seconds) = generics.calculate_minutes_seconds(running_time_seconds)
        
        scc = _SingleChannelControl(self._buspro)
        scc.subnet_id, scc.device_id = self._device_address
        scc.channel_number = channel
        scc.channel_level = int( (value/255)*100 )
        scc.running_time_minutes = minutes
        scc.running_time_seconds = seconds
        await scc.send()