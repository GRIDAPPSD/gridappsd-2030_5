from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from . import (EndDevice, Registration, RegistrationLink, DeviceInformationLink,
               DeviceStatusLink, PowerStatusLink, SubscriptionListLink, ConfigurationLink,
               FileStatusLink, EndDeviceList, DeviceCategoryType, DeviceCapability, EndDeviceListLink, SelfDeviceLink,
               MirrorUsagePointListLink)
from .hrefs import EndpointHrefs

Lfid = int

hrefs = EndpointHrefs()


@dataclass
class EndDeviceIndexer:
    index: int
    end_device: EndDevice
    #registration: Registration
    # device_information: DeviceInformation


@dataclass
class EndDevices:
    all_end_devices: Dict[int, EndDeviceIndexer] = field(default_factory=dict)
    end_devices_by_lfid: Dict[Lfid, EndDeviceIndexer] = field(default_factory=dict)
    device_numbers: int = field(default=-1)
    _device_data: Dict[Lfid, Dict] = field(default_factory=dict)

    @property
    def num_devices(self) -> int:
        return len(self.all_end_devices)

    def get_device_capability(self, lfid: Lfid) -> DeviceCapability:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)

        if lfid not in self._device_data:
            index = self.end_devices_by_lfid[lfid].index
            sdev = SelfDeviceLink(href=hrefs.sdev)
            edll = EndDeviceListLink(href=f"{hrefs.edev}/{index}", all=1)
            mup = MirrorUsagePointListLink(href=f"{hrefs.mup}/{index}")
            poll_rate = 900
            dc = DeviceCapability(
                mirror_usage_point_list_link=mup,
                self_device_link=sdev,
                end_device_list_link=edll,
                poll_rate=poll_rate
            )
            self._device_data[lfid] = dc

        return self._device_data.get(lfid)

    def get_device_by_index(self, index: int) -> Optional[EndDevice]:
        return self.all_end_devices.get(index)

    def get_device_by_lfid(self, lfid: Lfid) -> Optional[EndDevice]:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)
        return self.end_devices_by_lfid.get(lfid)

    def register(self, device_category: DeviceCategoryType, l_fid: Lfid, pin_code=999) -> EndDevice:
        ts = int(round(datetime.utcnow().timestamp()))
        self.device_numbers += 1
        new_dev_number = self.device_numbers

        # Manage links to different resources for the device.
        reg_link = RegistrationLink(href=hrefs.reg_fmt.format(index=new_dev_number))
        cfg_link = ConfigurationLink(href=hrefs.edev_cfg_fmt.format(index=new_dev_number))
        dev_status_link = DeviceStatusLink(href=hrefs.edev_status_fmt.format(index=new_dev_number))
        power_status_link = PowerStatusLink(href=hrefs.edev_power_status_fmt.format(
            index=new_dev_number))
        file_status_link = FileStatusLink(href=hrefs.edev_file_status_fmt.format(
            index=new_dev_number))
        dev_info_link = DeviceInformationLink(href=hrefs.edev_info_fmt.format(
            index=new_dev_number))
        sub_list_link = SubscriptionListLink(href=hrefs.edev_sub_list_fmt.format(
            index=new_dev_number))
        l_fid_bytes = str(l_fid).encode('utf-8')
        dev = EndDevice(device_category=bytes(device_category.value),
                        l_fdi=l_fid_bytes,
                        registration_link=reg_link,
                        device_status_link=dev_status_link,
                        configuration_link=cfg_link,
                        power_status_link=power_status_link,
                        device_information_link=dev_info_link,
                        s_fdi=l_fid,
                        file_status_link=file_status_link,
                        subscription_list_link=sub_list_link)

        registration = Registration(date_time_registered=ts, p_in=999)

        dev_indexer = EndDeviceIndexer(index=new_dev_number, end_device=dev)

        self.all_end_devices[new_dev_number] = dev_indexer
        self.end_devices_by_lfid[Lfid(l_fid_bytes)] = dev_indexer
        return dev

    def get(self, index: int) -> EndDevice:
        return self.all_end_devices[index].end_device

    def get_list(self, start: int, length: int = 1) -> EndDeviceList:
        return EndDeviceList(end_device=[x.end_device for x in self.all_end_devices.values()])
        #return [x.end_device for x in self.end_devices.values()]
