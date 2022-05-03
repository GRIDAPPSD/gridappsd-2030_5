from dataclasses import dataclass, field
from datetime import datetime
from time import mktime
from typing import Dict, Optional

from . import (EndDevice, Registration, RegistrationLink, DeviceInformationLink,
               DeviceStatusLink, PowerStatusLink, SubscriptionListLink, ConfigurationLink,
               FileStatusLink, EndDeviceList, DeviceCategoryType, DeviceCapability, EndDeviceListLink, SelfDeviceLink,
               MirrorUsagePointListLink, DerlistLink, FunctionSetAssignmentsListLink, LogEventListLink,
               UsagePointListLink, TimeLink)
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
            self._device_data[lfid] = {}
            index = self.end_devices_by_lfid[lfid].index
            sdev = SelfDeviceLink(href=hrefs.sdev)
            # TODO Add Aggregator for this
            edll = EndDeviceListLink(href=f"{hrefs.edev}")
            upt = UsagePointListLink(href=f"{hrefs.upt}")
            mup = MirrorUsagePointListLink(href=f"{hrefs.mup}")
            poll_rate = 50
            timelink = TimeLink(href=f"{hrefs.tm}")
            dc = DeviceCapability(
                mirror_usage_point_list_link=mup,
                self_device_link=sdev,
                end_device_list_link=edll,
                poll_rate=poll_rate,
                time_link=timelink,
                # response_set_list_link,
                # demand_response_program_list_link
                # derprogram_list_link
                # messaging_program_list_link
                # usage_point_list_link
                usage_point_list_link=upt
            )
            self._device_data[lfid]["device_capability"] = dc

        return self._device_data.get(lfid)["device_capability"]

    def get_device_by_index(self, index: int) -> Optional[EndDevice]:
        return self.all_end_devices.get(index)

    def get_device_by_lfid(self, lfid: Lfid) -> Optional[EndDevice]:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)
        return self.end_devices_by_lfid.get(lfid).end_device

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
        base_edev_single = hrefs    .extend_url(hrefs.edev, new_dev_number)
        der_list_link = DerlistLink(href=hrefs.extend_url(base_edev_single, suffix="der"))
        fsa_list_link = FunctionSetAssignmentsListLink(href=hrefs.extend_url(base_edev_single, suffix="fsa"))
        log_event_list_link = LogEventListLink(href=hrefs.extend_url(base_edev_single, suffix="log"))
        changed_time = datetime.now()
        changed_time.replace(microsecond=0)
        dev = EndDevice(device_category=device_category.value,
                        l_fdi=l_fid_bytes,
                        registration_link=reg_link,
                        device_status_link=dev_status_link,
                        configuration_link=cfg_link,
                        power_status_link=power_status_link,
                        device_information_link=dev_info_link,
                        s_fdi=l_fid,
                        # file_status_link=file_status_link,
                        # subscription_list_link=sub_list_link,
                        href=f"{hrefs.edev}/{new_dev_number}",
                        derlist_link=der_list_link,
                        function_set_assignments_list_link=fsa_list_link,
                        log_event_list_link=log_event_list_link,
                        enabled=True,
                        changed_time=int(changed_time.timestamp()))  # int(mktime(datetime.now().timetuple())))

        registration = Registration(date_time_registered=ts, p_in=999)

        dev_indexer = EndDeviceIndexer(index=new_dev_number, end_device=dev)

        self.all_end_devices[new_dev_number] = dev_indexer
        self.end_devices_by_lfid[Lfid(l_fid_bytes)] = dev_indexer
        return dev

    def get(self, index: int) -> EndDevice:
        return self.all_end_devices[index].end_device

    def get_end_device_list(self, lfid: Lfid, start: int = 0, length: int = 1) -> EndDeviceList:
        ed = self.get_device_by_lfid(lfid)
        if DeviceCategoryType(ed.device_category) == DeviceCategoryType.AGGREGATOR:
            devices = [x.end_device for x in self.all_end_devices.values()]
        else:
            devices = [ed]

        # TODO Handle start, length list things.
        dl = EndDeviceList(end_device=devices, all=len(devices), results=len(devices), href=hrefs.edev)
        return dl
