from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List

from ieee_2030_5.config import DeviceConfiguration
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.models.device_category import DeviceCategoryType
from ieee_2030_5.models.sep import (EndDevice, Registration, RegistrationLink, DeviceInformationLink,
                                    DeviceStatusLink, PowerStatusLink, ConfigurationLink,
                                    EndDeviceList, DeviceCapability, EndDeviceListLink,
                                    SelfDeviceLink,
                                    MirrorUsagePointListLink, DERListLink, FunctionSetAssignmentsListLink,
                                    LogEventListLink,
                                    UsagePointListLink, TimeLink, DeviceInformation, DER, FunctionSetAssignments,
                                    DERProgram, DERProgramListLink, DefaultDERControl)
from ieee_2030_5.types import Lfid


@dataclass
class EndDeviceData:
    index: int
    mRID: str  # mrid for the device.
    end_device: EndDevice
    registration: Registration
    device_capability: DeviceCapability = None
    der_programs: Optional[List[DERProgram]] = field(default_factory=list)
    ders: Optional[List[DER]] = field(default_factory=list)
    function_set_assignments: Optional[List[FunctionSetAssignments]] = field(default_factory=list)
    device_information: Optional[DeviceInformation] = None


@dataclass
class EndDevices:
    """
    EndDevices contains the server side instances of an
    """
    all_end_devices: Dict[int, EndDeviceData] = field(default_factory=dict)
    _lfid_index_map: Dict[Lfid, EndDeviceData] = field(default_factory=dict)

    # only increasing device_numbers
    _last_device_number: int = field(default=-1)

    def initialize_groups(self):
        """
        Initialize groups so they are ready to go when registering devices for the
        different group levels of the system.
        """
        non_topo = get_group(level=GroupLevel.NonTopology)

        for index, indexer in self.all_end_devices.items():
            indexer.der_programs.append(non_topo.der_program)

    @property
    def num_devices(self) -> int:
        return len(self.all_end_devices)

    def get_fsa_list(self, lfid: Optional[Lfid] = None,
                     edevid: Optional[int] = None) -> List[FunctionSetAssignments] | []:
        if not ((lfid is not None) ^ edevid is not None):
            raise ValueError("Either lfid or edevid must be passed not both.")

        if lfid:
            indexer: EndDeviceData = self._lfid_index_map.get(lfid)
        else:
            indexer: EndDeviceData = self.all_end_devices.get(edevid)

        return indexer.function_set_assignments

    def get_device_capability(self, lfid: Lfid) -> DeviceCapability:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)

        if self._lfid_index_map[lfid].device_capability is None:
            index = self._lfid_index_map[lfid].index
            sdev = SelfDeviceLink(href=hrefs.sdev)
            # TODO Add Aggregator for this
            edll = EndDeviceListLink(href=f"{hrefs.edev}", all=1)
            derp = DERProgramListLink(href=f"{hrefs.derp}", all=2)
            upt = UsagePointListLink(href=f"{hrefs.upt}", all=0)
            mup = MirrorUsagePointListLink(href=f"{hrefs.mup}", all=0)
            poll_rate = self.get_registration(index).pollRate
            timelink = TimeLink(href=f"{hrefs.tm}")

            dc = DeviceCapability(
                href=hrefs.dcap,
                MirrorUsagePointListLink=mup,
                # SelfDeviceLink=sdev,
                EndDeviceListLink=edll,
                pollRate=poll_rate,
                TimeLink=timelink,
                UsagePointListLink=upt,
                DERProgramListLink=derp
            )
            self._lfid_index_map[lfid].device_capability = dc

        return self._lfid_index_map[lfid].device_capability

    def get_device_by_index(self, index: int) -> Optional[EndDevice]:
        return self.all_end_devices.get(index)

    def get_device_by_lfid(self, lfid: Lfid) -> Optional[EndDevice]:
        if not isinstance(lfid, Lfid):
            lfid = Lfid(lfid)
        return self._lfid_index_map.get(lfid).end_device

    def initialize_device(self, device_config: DeviceConfiguration, lfid: Lfid) -> EndDevice:
        ts = int(round(datetime.utcnow().timestamp()))
        self._last_device_number += 1
        new_dev_number = self._last_device_number

        default_der_control = DefaultDERControl

        # Manage links to different resources for the device.
        reg_link_href = hrefs.build_edev_registration_link(new_dev_number)
        reg_link = RegistrationLink(href=reg_link_href)

        cfg_link_href = hrefs.build_edev_config_link(new_dev_number)
        cfg_link = ConfigurationLink(cfg_link_href)

        dev_status_link_href = hrefs.build_edev_status_link(new_dev_number)
        dev_status_link = DeviceStatusLink(href=dev_status_link_href)

        power_status_link_href = hrefs.build_edev_power_status_link(new_dev_number)
        power_status_link = PowerStatusLink(href=power_status_link_href)

        # file_status_link = FileStatusLink(href=hrefs.edev_file_status_fmt.format(
        #     index=new_dev_number))
        dev_info_link_href = hrefs.build_edev_info_link(new_dev_number)
        dev_info_link = DeviceInformationLink(href=dev_info_link_href)

        # sub_list_link = SubscriptionListLink(href=hrefs.edev_sub_list_fmt.format(
        #     index=new_dev_number))
        l_fid_bytes = str(lfid).encode('utf-8')

        base_edev_single = hrefs.extend_url(hrefs.edev, new_dev_number)
        der_list_link_href = hrefs.build_der_link(new_dev_number)
        der_list_link = DERListLink(href=der_list_link_href)

        fsa_list_link_href = hrefs.extend_url(base_edev_single, suffix="fsa")
        fsa_list_link = FunctionSetAssignmentsListLink(href=fsa_list_link_href)

        log_event_list_link_href = hrefs.extend_url(base_edev_single, suffix="log")
        log_event_list_link = LogEventListLink(href=log_event_list_link_href)

        end_device_href = f"{hrefs.edev}/{new_dev_number}"
        changed_time = datetime.now()
        changed_time.replace(microsecond=0)

        end_device = EndDevice(deviceCategory=device_config.device_category_type.value,
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
                               href=end_device_href,
                               DERListLink=der_list_link,
                               FunctionSetAssignmentsListLink=fsa_list_link,
                               LogEventListLink=log_event_list_link,
                               enabled=True,
                               changedTime=int(changed_time.timestamp()))

        add_href(end_device_href, end_device)

        registration = Registration(dateTimeRegistered=ts, pollRate=device_config.poll_rate, pIN=device_config.pin)
        add_href(reg_link_href, registration)

        return get_href(end_device_href)

    def get(self, index: int) -> EndDevice:
        return self.all_end_devices[index].end_device

    def get_registration(self, index: int) -> Registration:
        return self.all_end_devices[index].registration

    def get_der_list(self, index: int) -> DERListLink:
        return self.all_end_devices[index].end_device.DERListLink

    def get_fsa(self, index: int) -> FunctionSetAssignmentsListLink:
        return self.all_end_devices[index].end_device.FunctionSetAssignmentsListLink

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
