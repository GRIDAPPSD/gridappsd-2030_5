from typing import List, Dict

from . import BaseModel, EndDevice, DeviceCategoryType


class EndDeviceIndexer(BaseModel):
    index: int
    end_device: EndDevice


class EndDevices(BaseModel):
    end_devices: Dict[int, EndDeviceIndexer]
    num_devices: int = 0

    def create(self, device_category: DeviceCategoryType, lfid: str):
        dev = EndDevice(device_category=device_category, lfdi=lfid)
        new_dev_number = self.num_devices + 1
        dev_indexer = EndDeviceIndexer(index=new_dev_number, end_device=dev)
        self._end_devices[new_dev_number] = dev_indexer
