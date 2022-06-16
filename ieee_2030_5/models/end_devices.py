from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from ieee_2030_5.config import DeviceConfiguration
from ieee_2030_5.models.device_category import DeviceCategoryType
from ieee_2030_5.models.sep import (EndDevice, Registration, RegistrationLink, DeviceInformationLink,
                                    DeviceStatusLink, PowerStatusLink, SubscriptionListLink, ConfigurationLink,
                                    FileStatusLink, EndDeviceList, DeviceCapability, EndDeviceListLink,
                                    SelfDeviceLink,
                                    MirrorUsagePointListLink, DERListLink, FunctionSetAssignmentsListLink,
                                    LogEventListLink,
                                    UsagePointListLink, TimeLink, DeviceInformation)
from ieee_2030_5.types import Lfid


@dataclass
class EndDeviceIndexer:
    index: int
    id: str  # mrid for the device.
    end_device: EndDevice
    registration: Registration
    device_information: Optional[DeviceInformation] = None


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
            self._device_data[lfid] = {}
            index = self.end_devices_by_lfid[lfid].index
            sdev = SelfDeviceLink(href=hrefs.sdev)
            # TODO Add Aggregator for this
            edll = EndDeviceListLink(href=f"{hrefs.edev}", all=1)
            upt = UsagePointListLink(href=f"{hrefs.upt}", all=0)
            mup = MirrorUsagePointListLink(href=f"{hrefs.mup}", all=0)
            poll_rate = self.get_registration(index).pollRate
            timelink = TimeLink(href=f"{hrefs.tm}")

            dc = DeviceCapability(
                href=hrefs.dcap,
                MirrorUsagePointListLink=mup,
                SelfDeviceLink=sdev,
                EndDeviceListLink=edll,
                pollRate=poll_rate,
                TimeLink=timelink,
                UsagePointListLink=upt
            )
            self._device_data[lfid]["device_capability"] = dc

        return self._device_data.get(lfid)["device_capability"]

    def get_device_by_index(self, index: int) -> Optional[EndDevice]:
        return self.all_end_devices.get(index)

    def get_device_by_lfid(self, lfid: Lfid) -> Optional[EndDevice]:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)
        return self.end_devices_by_lfid.get(lfid).end_device

    def register(self, device_config: DeviceConfiguration, lfid: Lfid) -> EndDevice:
        ts = int(round(datetime.utcnow().timestamp()))
        self.device_numbers += 1
        new_dev_number = self.device_numbers

        # Manage links to different resources for the device.
        reg_link = RegistrationLink(href=hrefs.build_edev_registration_link(new_dev_number))
        cfg_link = ConfigurationLink(href=hrefs.build_edev_config_link(new_dev_number))
        dev_status_link = DeviceStatusLink(href=hrefs.build_edev_status_link(new_dev_number))
        power_status_link = PowerStatusLink(href=hrefs.build_edev_power_status_link(new_dev_number))
        # file_status_link = FileStatusLink(href=hrefs.edev_file_status_fmt.format(
        #     index=new_dev_number))
        dev_info_link = DeviceInformationLink(href=hrefs.build_edev_info_link(new_dev_number))
        # sub_list_link = SubscriptionListLink(href=hrefs.edev_sub_list_fmt.format(
        #     index=new_dev_number))
        l_fid_bytes = str(lfid).encode('utf-8')
        base_edev_single = hrefs.extend_url(hrefs.edev, new_dev_number)
        der_list_link = DERListLink(href=hrefs.extend_url(base_edev_single, suffix="der"))
        fsa_list_link = FunctionSetAssignmentsListLink(href=hrefs.extend_url(base_edev_single, suffix="fsa"), all=0)
        log_event_list_link = LogEventListLink(href=hrefs.extend_url(base_edev_single, suffix="log"))
        changed_time = datetime.now()
        changed_time.replace(microsecond=0)
        dev = EndDevice(deviceCategory=device_config.device_category_type.value,
                        lFDI=l_fid_bytes,
                        RegistrationLink=reg_link,
                        DeviceStatusLink=dev_status_link,
                        ConfigurationLink=cfg_link,
                        PowerStatusLink=power_status_link,
                        DeviceInformationLink=dev_info_link,
                        # TODO: Do actual sfid rather than lfid.
                        sFDI=lfid,
                        # file_status_link=file_status_link,
                        # subscription_list_link=sub_list_link,
                        href=f"{hrefs.edev}/{new_dev_number}",
                        DERListLink=der_list_link,
                        FunctionSetAssignmentsListLink=fsa_list_link,
                        LogEventListLink=log_event_list_link,
                        enabled=True,
                        changedTime=int(changed_time.timestamp()))

        registration = Registration(dateTimeRegistered=ts, pollRate=device_config.poll_rate, pIN=device_config.pin)

        dev_indexer = EndDeviceIndexer(index=new_dev_number, id=device_config.id,
                                       end_device=dev, registration=registration)

        self.all_end_devices[new_dev_number] = dev_indexer
        self.end_devices_by_lfid[Lfid(l_fid_bytes)] = dev_indexer
        return dev

    def get(self, index: int) -> EndDevice:
        return self.all_end_devices[index].end_device

    def get_registration(self, index: int) -> Registration:
        return self.all_end_devices[index].registration

    def get_end_device_list(self, lfid: Lfid, start: int = 0, length: int = 1) -> EndDeviceList:
        ed = self.get_device_by_lfid(lfid)
        if DeviceCategoryType(ed.deviceCategory) == DeviceCategoryType.AGGREGATOR:
            devices = [x.end_device for x in self.all_end_devices.values()]
        else:
            devices = [ed]

        # TODO Handle start, length list things.
        dl = EndDeviceList(EndDevice=devices, all=len(devices), results=len(devices), href=hrefs.edev, pollRate=900)
        return dl

import ieee_2030_5.hrefs as hrefs
