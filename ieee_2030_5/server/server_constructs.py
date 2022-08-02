from __future__ import annotations

import logging
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Flag, auto
from typing import Dict, Optional, List

from ieee_2030_5 import hrefs
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration, DeviceConfiguration
from ieee_2030_5.data.indexer import add_href, get_href
from ieee_2030_5.models import (
    EndDevice,
    DERProgram,
    DERProgramList,
    ActiveDERControlListLink,
    DefaultDERControlLink,
    DERControlListLink,
    DERCurveListLink, Registration, DERListLink, FunctionSetAssignmentsListLink, EndDeviceList, DeviceCategoryType,
    DefaultDERControl, RegistrationLink, ConfigurationLink, DeviceStatusLink, PowerStatusLink, DeviceInformationLink,
    LogEventListLink, SelfDeviceLink, EndDeviceListLink, DERProgramListLink, UsagePointListLink,
    MirrorUsagePointListLink, TimeLink, DeviceCapability, FunctionSetAssignments, DeviceInformation, DER)

from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.types import Lfid

_log = logging.getLogger(__name__)


class GroupLevel(Flag):
    """
    Each group is a construct of the layer the EndDevice is
    apart of.
    """
    System = auto()
    SubTransmission = auto()
    Substation = auto()
    Feeder = auto()
    Segment = auto()
    Transformer = auto()
    ServicePoint = auto()
    NonTopology = auto()


@dataclass
class Group:
    name: str
    description: str
    level: GroupLevel
    der_program: DERProgram
    _end_devices: Dict[bytes, EndDevice] = field(default_factory=dict)

    def add_end_device(self, end_device: EndDevice):
        self._end_devices[end_device.lFDI] = end_device

    def remove_end_device(self, end_device: EndDevice):
        self.remove_end_device_by_lfid(end_device.lFDI)

    def remove_end_device_by_lfid(self, lfid: bytes):
        del self._end_devices[lfid]

    def get_devices(self):
        return list(self._end_devices.values())


groups: Dict[GroupLevel, Group] = {}
der_programs: List[DERProgram] = []
uuid_handler: UUIDHandler = UUIDHandler()


def get_group(level: Optional[GroupLevel] = None, name: Optional[str] = None) -> Group:

    if not level and not name:
        raise ValueError("level or name must be specified to this function.")

    # if name exists then override the level with NonTopology
    if name:
        level = GroupLevel.NonTopology

    grp = groups.get(level)

    if not grp:
        raise ValueError(f"Invalid level specified {level}")

    if name is not None and level:
        for group in groups.values():
            if group.name == name:
                grp = group
                break

    return grp


def create_group(level: GroupLevel, name: Optional[str] = None) -> Group:
    if level is GroupLevel.NonTopology and not name:
        raise ValueError("NonTopology level must have a name associated with it")

    if level is not GroupLevel.NonTopology:
        mrid = "B" + str(level.name.__hash__())
        name = level.name
    else:
        mrid = "B" + str(name.__hash__())

    index = len(groups) + 1

    # TODO: Standardize urls so we can get them from a central spot.
    program_href = f"/sep2/A{index}/derp/1"
    program = DERProgram(mRID=mrid.encode('utf-8'),
                         description=name,
                         primacy=index * 10,
                         href=program_href)
    program.active_dercontrol_list_link = ActiveDERControlListLink(href=f"{program_href}/actderc")
    program.default_dercontrol_link = DefaultDERControlLink(href=f"{program_href}/dderc")
    program.dercontrol_list_link = DERControlListLink(href=f"{program_href}/derc")
    program.dercurve_list_link = DERCurveListLink(href=f"{program_href}/dc")

    if level not in groups:
        groups[level] = Group(level=level, name=name, description=name, der_program=program)

    der_programs.append(program)
    uuid_handler.add_known(mrid, program)


# Create all but the NonTopology group, which will get added
for _, lvl in enumerate(GroupLevel):
    create_group(lvl, name=lvl.name)


der_program_list = DERProgramList(DERProgram=der_programs)


def get_der_program_list():
    return der_program_list


def get_groups() -> Dict[GroupLevel, Group]:
    return groups


def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository) -> EndDevices:
    _log.debug("Initializing 2030.5")

    _log.debug("Update DERCurves' href property")
    # Create curves for der controls.
    for index, curve in enumerate(config.curve_list):
        curve.href = f"{hrefs.curve}/{index}"
        add_href(curve.href, curve)

    _log.debug("Update DERPrograms' adding links to the different program pieces.")
    # Initialize "global" DERPrograms href lists, including all of the different links to
    # locations for active, default, curve and control lists.
    for program_list in config.program_lists:
        for index, program in enumerate(program_list.programs):
            program.href = f"{hrefs.program}/{index}"
            program.ActiveDERControlListLink = ActiveDERControlListLink(href=f"{program.href}/actderc", all=0)
            program.DERCurveListLink = DERCurveListLink(href=f"{program.href}/dc", all=0)
            program.DefaultDERControlLink = DefaultDERControlLink(href=f"{program.href}/dderc")
            program.DERControlListLink = DERControlListLink(href=f"{program.href}/derc", all=0)

            add_href(program.href, program)

    _log.debug("Registering EndDevices")
    end_devices = EndDevices()
    if config.server_mode == "enddevices_create_on_start":
        for device_config in config.devices:
            end_device = end_devices.initialize_device(device_config=device_config, lfid=tlsrepo.lfdi(device_config.id))
            for fsa in device_config.fsa_list:
                print(fsa)


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

    def get_end_devices(self) -> Dict[int, EndDevice]:
        devices: Dict[int, EndDevice] = {}
        for k, v in self.all_end_devices.items():
            devices[k] = copy(v.end_device)
        return devices

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
        new_dev_number =self._last_device_number

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
        edd = EndDeviceData(index=new_dev_number, mRID=end_device.lFDI,
                            end_device=end_device, registration=registration)
        self.all_end_devices[new_dev_number] = edd
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

if __name__ == '__main__':
    print(get_groups())
    for x in der_program_list.DERProgram:
        print(x.href)

    for x, v in get_groups().items():
        print(x)
        print(v)

    create_group(name="foo")
    g = get_group(name="foo")
    assert GroupLevel.NonTopology == g.level
    assert "foo" == g.name
