from .device import Device
# from ..helpers.enums import *
from ..devices.control import _SequenceControl


class Sequence(Device):
    def __init__(self, buspro, device_address, sequence_address, name=""):
        super().__init__(buspro, sequence_address, name)
        # device_address = (subnet_id, device_id, area_number, scene_number)

        self._buspro = buspro
        self._device_address = device_address
        self._sequence_address = sequence_address
        # self.register_telegram_received_cb(self._telegram_received_cb)
        # self._call_read_current_status_of_channels(run_from_init=True)

    async def run(self):
        sequence_control = _SequenceControl(self._buspro)
        sequence_control.subnet_id, sequence_control.device_id = self._device_address
        sequence_control.area_number, sequence_control.sequence_number = self._sequence_address
        await sequence_control.send()
