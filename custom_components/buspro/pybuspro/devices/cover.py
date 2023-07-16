from .control import _CoverControl
from .device import Device
from ..helpers.enums import *
from ..helpers.generics import Generics


class Cover(Device):
    def __init__(self, buspro, device_address, channel_number, name="", delay_read_current_state_seconds=0):
        super().__init__(buspro, device_address, name)
        # device_address = (subnet_id, device_id, channel_number)

        self._buspro = buspro
        self._device_address = device_address
        self._channel = channel_number
        self._status = CoverStatus.CLOSE
        self.register_telegram_received_cb(self._telegram_received_cb)
        self._call_read_current_status_of_channels(run_from_init=True)

    def _telegram_received_cb(self, telegram):
        if telegram.operate_code == OperateCode.CurtainSwitchControlResponse:
            channel = telegram.payload[0]
            # success = telegram.payload[1]
            status = telegram.payload[2]
            if channel == self._channel:
                self._status = status
                self._call_device_updated()
        elif telegram.operate_code == OperateCode.CurtainSwitchStatusResponse:
            if self._channel <= telegram.payload[0]:
                self._status = telegram.payload[self._channel]
                self._call_device_updated()

    async def set_stop(self):
        await self._set(CoverStatus.STOP)

    async def set_open(self):
        await self._set(CoverStatus.OPEN)

    async def set_close(self):
        await self._set(CoverStatus.CLOSE)

    async def read_status(self):
        raise NotImplementedError

    @property
    def is_closed(self):
        return None
        # if self._status == CoverStatus.CLOSE:
        #     return True
        # else:
        #     return False

    @property
    def device_identifier(self):
        return f"{self._device_address}-{self._channel}"

    async def _set(self, status):
        self._status = status

        scc = _CoverControl(self._buspro)
        scc.subnet_id, scc.device_id = self._device_address
        scc.channel_number = self._channel
        scc.channel_status = self._status
        await scc.send()
