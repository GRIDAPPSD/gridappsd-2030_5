from __future__ import annotations

import logging

# from ieee_2030_5.adapters import BaseAdapter
from ieee_2030_5.certs import TLSRepository, lfdi_from_fingerprint
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.utils.tls_wrapper import OpensslWrapper

_log = logging.getLogger(__name__)

# # from copy import copy, deepcopy
# # from dataclasses import dataclass, field
# # from datetime import datetime
# # from enum import Flag, auto
# # from typing import Dict, List, Optional, Set

# # import werkzeug.exceptions

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m

# # from ieee_2030_5.adapters import BaseAdapter
# # from ieee_2030_5.certs import TLSRepository, sfdi_from_lfdi
# # from ieee_2030_5.config import (DeviceConfiguration, ProgramList,
# #                                 ServerConfiguration)
# # from ieee_2030_5.data.indexer import add_href, get_href
# # from ieee_2030_5.server.uuid_handler import UUIDHandler
# # from ieee_2030_5.types_ import Lfdi

# # _log = logging.getLogger(__name__)


# # class GroupLevel(Flag):
# #     """
# #     Each group is a construct of the layer the EndDevice is
# #     apart of.
# #     """
# #     System = auto()
# #     SubTransmission = auto()
# #     Substation = auto()
# #     Feeder = auto()
# #     Segment = auto()
# #     Transformer = auto()
# #     ServicePoint = auto()
# #     NonTopology = auto()


# # @dataclass
# # class Group:
# #     name: str
# #     description: str
# #     level: GroupLevel
# #     der_program: m.m.DERProgram
# #     _end_devices: Dict[bytes, m.EndDevice] = field(default_factory=dict)

# #     def add_end_device(self, end_device: m.EndDevice):
# #         self._end_devices[end_device.lFDI] = end_device

# #     def remove_end_device(self, end_device: m.EndDevice):
# #         self.remove_end_device_by_lfdi(end_device.lFDI)

# #     def remove_end_device_by_lfdi(self, lfdi: bytes):
# #         del self._end_devices[lfdi]

# #     def get_devices(self):
# #         return list(self._end_devices.values())


# # groups: Dict[GroupLevel, Group] = {}
# # der_programs: List[m.DERProgram] = []
# # uuid_handler: UUIDHandler = UUIDHandler()


# # def get_group(level: Optional[GroupLevel] = None, name: Optional[str] = None) -> Group:
# #     if not level and not name:
# #         raise ValueError("level or name must be specified to this function.")

# #     # if name exists then override the level with NonTopology
# #     if name:
# #         level = GroupLevel.NonTopology

# #     grp = groups.get(level)

# #     if not grp:
# #         raise ValueError(f"Invalid level specified {level}")

# #     if name is not None and level:
# #         for group in groups.values():
# #             if group.name == name:
# #                 grp = group
# #                 break

# #     return grp


# # def create_group(level: GroupLevel, name: Optional[str] = None) -> Group:
# #     if level is GroupLevel.NonTopology and not name:
# #         raise ValueError("NonTopology level must have a name associated with it")

# #     if level is not GroupLevel.NonTopology:
# #         mrid = "B" + str(level.name.__hash__())
# #         name = level.name
# #     else:
# #         mrid = "B" + str(name.__hash__())

# #     index = len(groups) + 1

# #     # TODO: Standardize urls so we can get them from a central spot.
# #     program_href = f"/sep2/A{index}/derp/1"
# #     program = m.DERProgram(mRID=mrid.encode('utf-8'),
# #                            description=name,
# #                            primacy=index * 10,
# #                            href=program_href)
# #     program.active_dercontrol_list_link = m.ActiveDERControlListLink(
# #         href=f"{program_href}/actderc")
# #     program.default_dercontrol_link = m.DefaultDERControlLink(href=f"{program_href}/dderc")
# #     program.dercontrol_list_link = m.DERControlListLink(href=f"{program_href}/derc")
# #     program.dercurve_list_link = m.DERCurveListLink(href=f"{program_href}/dc")

# #     if level not in groups:
# #         groups[level] = Group(level=level, name=name, description=name, der_program=program)

# #     der_programs.append(program)
# #     uuid_handler.add_known(mrid, program)


# # # Create all but the NonTopology group, which will get added
# # for _, lvl in enumerate(GroupLevel):
# #     create_group(lvl, name=lvl.name)

# # der_program_list = m.DERProgramList(DERProgram=der_programs)


# # def get_der_program_list():
# #     return der_program_list


# # def get_groups() -> Dict[GroupLevel, Group]:
# #     return groups
def create_device_capability(end_device_index: int) -> m.DeviceCapability:
    """Create a device capability objecct for the passed device index

    This function does not verify that there is a device at the passed index.
    """
    device_capability = m.DeviceCapability(href=str(hrefs.DeviceCapabilityHref(end_device_index)))
    device_capability.EndDeviceListLink = m.EndDeviceListLink(href=hrefs.DEFAULT_EDEV_ROOT, all=1)
    device_capability.DERProgramListLink = m.DERProgramListLink(href=hrefs.DEFAULT_DERP_ROOT, all=0)
    device_capability.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.DEFAULT_MUP_ROOT, all=0)
    device_capability.TimeLink = m.TimeLink(href=hrefs.DEFAULT_TIME_ROOT)
    device_capability.UsagePointListLink = m.UsagePointListLink(href=hrefs.DEFAULT_UPT_ROOT, all=0)
    
    adpt.DeviceCapabilityAdapter.add(device_capability)
    return device_capability
    

def add_enddevice(device: m.EndDevice) -> m.EndDevice:
    """ Add an enddevice to the enddevice adapter and the device capability adapter.
    
    All links are filled out to the end device.
    """
    device = adpt.EndDeviceAdapter.add(device)
    device = update_enddevice_links(device)
    # Retrieve the index
    index = int(device.href.split(hrefs.SEP)[1])
    create_device_capability(index)
    
    _log.debug(f"Added {device.href}")
    

def update_enddevice_links(device: m.EndDevice) -> m.EndDevice:
    index = int(device.href.split(hrefs.SEP)[1])
    ed_href = hrefs.EndDeviceHref(index)
    device.DERListLink = m.DERListLink(href=ed_href.der_list)
    device.ConfigurationLink = m.ConfigurationLink(href=ed_href.configuration)
    device.DeviceInformationLink = m.DeviceInformationLink(href=ed_href.device_information)
    device.DeviceStatusLink = m.DeviceStatusLink(href=ed_href.device_status)
    device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=ed_href.function_set_assignments)
    device.PowerStatusLink = m.PowerStatusLink(href=ed_href.device_power_status)
    device.LogEventListLink = m.LogEventListLink(href=ed_href.log_event_list)
    device.RegistrationLink = m.RegistrationLink(href=ed_href.registration)
    adpt.EndDeviceAdapter.put(index, device)
    return device

    



def initialize_2030_5(config: ServerConfiguration, tlsrepo: TLSRepository):
    """Initialize the 2030.5 server.  
    
    This method initializes the adapters from the configuration objects into
    the persistence adapters.
    """
    _log.debug("Initializing 2030.5")
    _log.debug("Adding server level urls to cache")
    

    for index, cfg_device in enumerate(config.devices):
        
        end_device = adpt.EndDeviceAdapter.fetch_by_property("href", (str(hrefs.EndDeviceHref(index))))
        if end_device is not None:
            _log.warning(f"End device {cfg_device.id} already exists.  Updating lfdi, sfdi, and postRate.")
            end_device.lFDI = tlsrepo.lfdi(cfg_device.id)
            end_device.sFDI = tlsrepo.sfdi(cfg_device.id)
            end_device.postRate = cfg_device.post_rate
            adpt.EndDeviceAdapter.put(index, end_device)
        else:
            _log.debug(f"Adding end device {cfg_device.id} to server")
            end_device = m.EndDevice(lFDI=tlsrepo.lfdi(cfg_device.id),
                                    sFDI=tlsrepo.sfdi(cfg_device.id),
                                    postRate=cfg_device.post_rate,
                                    enabled=True)
            add_enddevice(end_device)
            adpt.RegistrationAdapter.add(m.Registration(href=end_device.RegistrationLink, 
                                                        pIN=cfg_device.pin, 
                                                        pollRate=cfg_device.poll_rate))
        

#     # start intializing the system
#     BaseAdapter.initialize(config, tlsrepo)

# #     # # DERControlAdapter.initialize_from_storage()
# #     # add_href(hrefs.get_time_href(), m.TimeLink(href=hrefs.get_time_href()))
# #     # add_href(hrefs.get_enddevice_list_href(), m.EndDeviceListLink(hrefs.get_enddevice_list_href()))

# #     # _log.debug("Update DERCurves' href property")
# #     # # Create curves for der controls.
# #     # for index, curve in enumerate(config.curves):
# #     #     curve.href = hrefs.get_curve_href(index)
# #     #     add_href(curve.href, curve)

# #     # _log.debug("Registering EndDevices")
# #     # end_devices = EndDevices()
# #     # # Initialize all the enddevices on startup or load them
# #     # # from storage if available
# #     # if config.server_mode == "enddevices_create_on_start":
# #     #     # TODO load from storage if available.
# #     #     for device_config in config.devices:
# #     #         end_devices.initialize_device(device_config=device_config,
# #     #                                       lfdi=tlsrepo.lfdi(device_config.id),
# #     #                                       program_lists=config.programs)
# #     #         if device_config.fsa_list:
# #     #             for fsa in device_config.fsa_list:
# #     #                 print(fsa)
# #     #         print(end_devices.__all_end_devices__)

# #     # else:
# #     #     # Initialize allowed connection only.
# #     #     for cfg in config.devices:
# #     #         lfdi = tlsrepo.lfdi(cfg.id)
# #     #         _log.debug(f"FOR dev_id: {cfg.id} LFDI is {lfdi}")
# #     #         end_devices.add_connectable(lfdi=tlsrepo.lfdi(cfg.id))

# #     # return end_devices


# # @dataclass
# # class EndDeviceData:
# #     index: int
# #     mRID: str    # mrid for the device.
# #     end_device: m.EndDevice
# #     registration: m.Registration
# #     device_capability: m.DeviceCapability = None
# #     der_programs: Optional[List[m.DERProgram]] = field(default_factory=list)
# #     ders: Optional[List[m.DER]] = field(default_factory=list)
# #     function_set_assignments: Optional[List[m.FunctionSetAssignments]] = field(
# #         default_factory=list)
# #     device_information: Optional[m.DeviceInformation] = None


# # @dataclass
# # class EndDevices:
# #     """
# #     EndDevices contains the server side instances of an
# #     """
# #     __all_end_devices__: Dict[int, m.EndDevice] = field(default_factory=dict)
# #     _lfdi_index_map: Dict[Lfdi, int] = field(default_factory=dict)
# #     _lfdi_connection_allowed: Set[Lfdi] = field(default_factory=set)

# #     # only increasing device_numbers
# #     _last_device_number: int = field(default=-1)

# #     def allowed_to_connect(self, lfdi: Lfdi) -> bool:
# #         """
# #         Determine if the passed lfdi is within the tls repository of acceptable credentials.

# #         Args:
# #             lfdi: generated from fingerprint of the tls certificate

# #         Returns:
# #             True if connection is allowed.
# #         """
# #         return lfdi in self._lfdi_connection_allowed

# #     def initialize_groups(self):
# #         """
# #         Initialize groups so they are ready to go when registering devices for the
# #         different group levels of the system.
# #         """
# #         non_topo = get_group(level=GroupLevel.NonTopology)

# #         for index, indexer in self.__all_end_devices__.items():
# #             indexer.der_programs.append(non_topo.der_program)

# #     @property
# #     def num_devices(self) -> int:
# #         return len(self.__all_end_devices__)

# #     def get_end_devices(self) -> Dict[int, m.EndDevice]:
# #         devices: Dict[int, m.EndDevice] = {}
# #         for k, v in self.__all_end_devices__.items():
# #             devices[k] = copy(v.end_device)
# #         return devices

# #     def get_end_device_data(self, index: int) -> EndDeviceData:
# #         data = self.__all_end_devices__.get(index)
# #         if not data:
# #             raise werkzeug.exceptions.NotFound()

# #         return deepcopy(data)

# #     def get_fsa_list(self,
# #                      lfdi: Optional[Lfdi] = None,
# #                      edevid: Optional[int] = None) -> List[m.FunctionSetAssignments] | []:
# #         if not ((lfdi is not None) ^ edevid is not None):
# #             raise ValueError("Either lfdi or edevid must be passed not both.")

# #         if lfdi:
# #             indexer: EndDeviceData = self._lfdi_index_map.get(lfdi)
# #         else:
# #             indexer: EndDeviceData = self.__all_end_devices__.get(edevid)

# #         return indexer.function_set_assignments

# #     def get_device_capability(self, lfdi: Lfdi) -> Optional[m.DeviceCapability]:
# #         """

# #         Args:
# #             lfdi:

# #         Returns:

# #         """
# #         if not isinstance(lfdi, Lfdi):
# #             lfdi = Lfdi(lfdi.encode('ascii'))

# #         # Allowed to connect
# #         # if not self.allowed_to_connect(lfdi):
# #         #     return None

# #         dc = m.DeviceCapability(href=hrefs.get_dcap_href())
# #         # TODO if aggregator then count number of devices
# #         # Use get_href to retrieve the already constructed object from cache.
# #         dc.EndDeviceListLink = get_href(hrefs.get_enddevice_list_href())
# #         dc.TimeLink = get_href(hrefs.get_time_href())

# #         return dc

# #     def get_device_by_index(self, index: int) -> m.EndDevice:
# #         return self.__get_enddevice_by_index__(index)

# #     def get_device_by_lfdi(self, lfdi: Lfdi) -> Optional[m.EndDevice]:
# #         """

# #         Args:
# #             lfdi:

# #         Returns:

# #         """
# #         retvalue = None
# #         # Handle bytes to str conversion because the lfdi_index_map uses str not bytes.
# #         if not isinstance(lfdi, str):
# #             lfdi = lfdi.decode('utf-8')
# #         index = self._lfdi_index_map.get(lfdi)
# #         if index is not None:
# #             retvalue = self.__all_end_devices__.get(index)
# #             if retvalue.lFDI != lfdi:
# #                 print("It doesn't match")
# #         return retvalue

# #     def __get_enddevicedata_by_lfdi__(self, lfdi: Lfdi):
# #         index = self.__get_index_by_lfdi__(lfdi)
# #         return self.__all_end_devices__[index]

# #     def __get_index_by_lfdi__(self, lfdi: Lfdi):
# #         if not isinstance(lfdi, Lfdi):
# #             lfdi = Lfdi(lfdi)

# #         index = self._lfdi_index_map.get(lfdi)
# #         if index is None:
# #             raise werkzeug.exceptions.NotFound()
# #         return index

# #     def __get_enddevice_by_index__(self, index: int) -> m.EndDevice:
# #         ed = self.__all_end_devices__.get(index)
# #         if ed is None:
# #             raise werkzeug.exceptions.NotFound()
# #         return ed

# #     def __next_id__(self) -> int:
# #         self._last_device_number += 1
# #         return self._last_device_number

# #     def add_end_device(self, end_device: m.EndDevice) -> str:
# #         assert end_device.lFDI
# #         assert end_device.sFDI

# #         new_id = self.__next_id__()
# #         self.__all_end_devices__[new_id] = end_device
# #         self._lfdi_index_map[end_device.lFDI] = new_id
# #         if not end_device.href:
# #             end_device.href = hrefs.get_enddevice_href(new_id)
# #         add_href(end_device.href, end_device)
# #         return end_device.href

# #     def initialize_device(self, device_config: DeviceConfiguration, lfdi: Lfdi,
# #                           program_lists: List[ProgramList]) -> m.EndDevice:
# #         """
# #         Create a new EndDevice object from the passed DeviceConfiguration.  Each time
# #         the method is called it will increase the number of a device such that the
# #         hrefs from the EndDevice will be unique across the server.

# #         Notes:
# #             Adds EndDevice to the object store
# #             Adds Registration to the object store

# #         Args:
# #             device_config:
# #             lfdi:
# #             program_lists:

# #         Returns:
# #             An instantiated EndDevice.

# #         """
# #         ts = int(round(datetime.utcnow().timestamp()))
# #         new_dev_number = self.__next_id__()

# #         enddevice_href = hrefs.get_enddevice_href(new_dev_number)
# #         end_device = m.EndDevice(
# #             href=enddevice_href,
# #             deviceCategory=device_config.deviceCategory,
# #             lFDI=lfdi,
# #             sFDI=sfdi_from_lfdi(lfdi),
# #             RegistrationLink=m.RegistrationLink(hrefs.get_registration_href(new_dev_number)),
# #             ConfigurationLink=m.ConfigurationLink(hrefs.get_configuration_href(new_dev_number)))
# #         add_href(enddevice_href, end_device)
# #         fsa_link_href = hrefs.get_fsa_list_href(end_device.href)
# #         end_device.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(
# #             href=fsa_link_href, all=len(device_config.fsa_list))
# #         if device_config.fsa_list:

# #             fsa_list = m.FunctionSetAssignmentsList(href=fsa_link_href,
# #                                                     all=len(device_config.fsa_list))
# #             for fsa_index, fsa_config in enumerate(device_config.fsa_list):
# #                 fsa_href = hrefs.get_fsa_href(fsa_list.href, fsa_index)
# #                 fsa = m.FunctionSetAssignments(href=fsa_href,
# #                                                mRID=fsa_config.get("mRID"),
# #                                                description=fsa_config.get("description"))

# #                 # TODO: Load other programs
# #                 fsa.DERProgramListLink = m.DERProgramListLink(
# #                     href=hrefs.get_der_program_list(fsa_href))
# #                 fsa.DemandResponseProgramListLink = m.DemandResponseProgramListLink(
# #                     href=hrefs.get_dr_program_list(fsa_href))
# #                 # for pl in program_lists:
# #                 #     fsa.Pro
# #                 #     _log.debug(pl)
# #                 add_href(fsa_href, fsa)
# #                 fsa_list.FunctionSetAssignments.append(fsa)
# #             add_href(fsa_link_href, fsa_list)

# #         add_href(hrefs.get_registration_href(new_dev_number),
# #                  m.Registration(pIN=device_config.pin, pollRate=device_config.poll_rate))
# #         self.__all_end_devices__[new_dev_number] = end_device
# #         self._lfdi_index_map[lfdi] = new_dev_number

# #         return get_href(enddevice_href)
# #         # cfg_link_href = hrefs.build_edev_config_link(new_dev_number)
# #         # cfg_link = ConfigurationLink(cfg_link_href)
# #         #
# #         # dev_status_link_href = hrefs.build_edev_status_link(new_dev_number)
# #         # dev_status_link = DeviceStatusLink(href=dev_status_link_href)
# #         #
# #         # power_status_link_href = hrefs.build_edev_power_status_link(new_dev_number)
# #         # power_status_link = PowerStatusLink(href=power_status_link_href)
# #         #
# #         # # file_status_link = FileStatusLink(href=hrefs.edev_file_status_fmt.format(
# #         # #     index=new_dev_number))
# #         # dev_info_link_href = hrefs.build_edev_info_link(new_dev_number)
# #         # dev_info_link = DeviceInformationLink(href=dev_info_link_href)
# #         #
# #         # # sub_list_link = SubscriptionListLink(href=hrefs.edev_sub_list_fmt.format(
# #         # #     index=new_dev_number))
# #         # l_fid_bytes = str(lfdi).encode('utf-8')

# #         # base_edev_single = hrefs.extend_url(hrefs.edev, new_dev_number)
# #         # der_list_link_href = hrefs.build_der_link(new_dev_number)
# #         # der_list_link = DERListLink(href=der_list_link_href)
# #         #
# #         # fsa_list_link_href = hrefs.extend_url(base_edev_single, suffix="fsa")
# #         # fsa_list_link = FunctionSetAssignmentsListLink(href=fsa_list_link_href)
# #         #
# #         # log_event_list_link_href = hrefs.extend_url(base_edev_single, suffix="log")
# #         # log_event_list_link = LogEventListLink(href=log_event_list_link_href)
# #         #
# #         # time_link_href = hrefs.tm
# #         # time_link = TimeLink(href=time_link_href)
# #         #
# #         # end_device_href = f"{hrefs.edev}/{new_dev_number}"
# #         # end_device_list_link = EndDeviceListLink(href=hrefs.edev)
# #         #
# #         # changed_time = datetime.now()
# #         # changed_time.replace(microsecond=0)
# #         #
# #         # program_list_names = [x.name for x in program_lists]
# #         # found_fsa_item = set()
# #         # fsa_items: List[FunctionSetAssignments] = []
# #         # for fsa in device_config.fsa_list:
# #         #     found_program = None
# #         #     for fsa_name in fsa['program_lists']:
# #         #         for program_list in program_lists:
# #         #             if program_list.name == fsa_name:
# #         #                 found_program = program_list
# #         #     if found_program is None:
# #         #         raise ValueError(f"Invalid fsa: {fsa} not found in program_lists.  Check configuration.")
# #         #
# #         #     fsa_items.append(FunctionSetAssignments(mRID=fsa['mRID'], description=fsa['description'],
# #         #                                             href=hrefs.extend_url(fsa_list_link_href, len(fsa_items))))
# #         #
# #         # device_capability_link = hrefs.dcap
# #         # device_capability = DeviceCapability(href=device_capability_link, TimeLink=time_link,
# #         #                                      EndDeviceListLink=end_device_list_link)
# #         # end_device = EndDevice(deviceCategory=device_config.device_category_type.value,
# #         #                        lFDI=l_fid_bytes,
# #         #                        RegistrationLink=reg_link,
# #         #                        DeviceStatusLink=dev_status_link,
# #         #                        ConfigurationLink=cfg_link,
# #         #                        PowerStatusLink=power_status_link,
# #         #                        DeviceInformationLink=dev_info_link,
# #         #                        # TODO: Do actual sfdi rather than lfdi.
# #         #                        sFDI=lfdi,
# #         #                        # file_status_link=file_status_link,
# #         #                        # subscription_list_link=sub_list_link,
# #         #                        href=end_device_href,
# #         #                        # DERListLink=der_list_link,
# #         #                        FunctionSetAssignmentsListLink=fsa_list_link,
# #         #                        LogEventListLink=log_event_list_link,
# #         #                        enabled=True,
# #         #                        changedTime=int(changed_time.timestamp()))
# #         #
# #         # add_href(end_device_href, end_device)
# #         #
# #         # registration = Registration(dateTimeRegistered=ts, pollRate=device_config.poll_rate, pIN=device_config.pin)
# #         # add_href(reg_link_href, registration)
# #         # edd = EndDeviceData(index=new_dev_number, mRID=device_config.id,
# #         #                     end_device=end_device, registration=registration,
# #         #                     function_set_assignments=fsa_items,
# #         #                     device_capability=device_capability)
# #         # self.__all_end_devices__[new_dev_number] = edd
# #         # self._lfdi_index_map[lfdi] = new_dev_number


# # #        return get_href(end_device_href)

# #     def get(self, index: int) -> m.EndDevice:
# #         return get_href(hrefs.get_enddevice_href(index))

# #     def get_registration(self, index: int) -> m.Registration:
# #         return get_href(hrefs.get_registration_href(index))

# #     def get_der_list(self, index: int) -> m.DERListLink:
# #         return self.__all_end_devices__[index].end_device.DERListLink

# #     def get_fsa(self, index: int) -> m.FunctionSetAssignmentsListLink:
# #         return get_href(hrefs.get_fsa_list_href())
# #         # return self.__all_end_devices__[index].end_device.FunctionSetAssignmentsListLink

# #     def get_end_device_list(self, lfdi: Lfdi, start: int = 0, length: int = 1) -> m.EndDeviceList:
# #         """

# #         Args:
# #             lfdi:
# #             start:
# #             length:

# #         Returns:

# #         """
# #         ed = self.get_device_by_lfdi(lfdi)

# #         if ed is None:
# #             return m.EndDeviceList(hrefs.get_enddevice_list_href(), all=0, results=0)

# #         if ed.deviceCategory is not None:
# #             if m.DeviceCategoryType(ed.deviceCategory) == m.DeviceCategoryType.AGGREGATOR:
# #                 devices = [x for x in self.__all_end_devices__.values()]
# #             else:
# #                 devices = [ed]
# #         else:
# #             devices = [ed]

# #         # TODO Handle start, length list things.
# #         dl = m.EndDeviceList(EndDevice=devices,
# #                              all=len(devices),
# #                              results=len(devices),
# #                              href=hrefs.get_enddevice_list_href(),
# #                              pollRate=900)
# #         return dl

# #     def add_connectable(self, lfdi: Lfdi):
# #         self._lfdi_connection_allowed.add(lfdi)

# # if __name__ == '__main__':
# #     print(get_groups())
# #     for x in der_program_list.m.DERProgram:
# #         print(x.href)

# #     for x, v in get_groups().items():
# #         print(x)
# #         print(v)

# #     create_group(name="foo")
# #     g = get_group(name="foo")
# #     assert GroupLevel.NonTopology == g.level
# #     assert "foo" == g.name
