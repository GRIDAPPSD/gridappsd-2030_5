import logging
import uuid
from ast import Dict
from datetime import datetime
from typing import List

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import (Adapter, AdapterListProtocol, BaseAdapter,
                                  ready_signal)
from ieee_2030_5.adapters.der import DERAdapter, DERProgramAdapter
from ieee_2030_5.adapters.fsa import FSAAdapter
from ieee_2030_5.adapters.timeadapter import TimeAdapter
from ieee_2030_5.data.indexer import add_href
from ieee_2030_5.models.enums import DeviceCategoryType
from ieee_2030_5.types_ import Lfdi
from ieee_2030_5.utils import uuid_2030_5

_log = logging.getLogger(__file__)

# class _EndDeviceAdapter(BaseAdapter, AdapterListProtocol):
    
#     def __init__(self) -> None:
#         self._end_devices: List[m.EndDevice] = []
#         self._reg: Dict[int, m.Registration] = {}
#         self._fsa: List[m.FunctionSetAssignments] = []
#         self._edev_fsa: Dict[int, List[m.FunctionSetAssignments]] = {}
#         self._edev_derp: Dict[int, Dict[int, List[m.DERProgram]]] = {}
        
#     def fetch_registration(self, edev_index: int) -> m.Registration:
#         return self._reg[edev_index]
    
#     def fetch_fsa_list(self, edev_index: int, start: int = 0, after: int = 0, limit: int = 0) -> m.FunctionSetAssignmentsList:
        
#         fsa_list = FSAAdapter.fetch_all(m.FunctionSetAssignmentsList(href=hrefs.fsa_href(edev_index=edev_index)))
        
#         # fsa = FSAAdapter.fetch_edev_all()
#         # fsa_list = m.FunctionSetAssignmentsList(
#         #     href=hrefs.fsa_href(edev_index=edev_index), 
#         #     FunctionSetAssignments=self._edev_fsa.get(edev_index, []))
#         return fsa_list
    
#     def fetch_fsa(self, edev_index: int, fsa_index: int) -> m.FunctionSetAssignments:
#         return self._edev_fsa[edev_index][fsa_index]
    
#     def fetch_derp_list(self, edev_index: int, fsa_index: int, start: int = 0, after: int = 0, limit: int = 0) -> m.DERProgramList:
#         derps = self._edev_derp[edev_index][fsa_index]
        
#         derp = m.DERProgramList(href=hrefs.derp_href(edev_index=edev_index, fsa_index=fsa_index),
#                                 DERProgram=derps,
#                                 all=len(derps), results=len(derps))
        
#         return derp
        
#     def __initialize__(self, sender):
#         """ Intializes the following based upon the device configuration and the tlsrepository.
        
#         Each EndDevice will have the following sub-components initialized:
#         - PowerStatus - PowerStatusLink
#         - DeviceStatus - DeviceStatusLink
#         - Registration - RegistrationLink
#         - MessagingProgramList - MessagingProgramListLink
#         - Log
#         Either FSA or DemandResponseProgram
#         - DemandResponseProgram - DemandResponseProgramListLink
        
        
#         As well as the following properties
#         - changedTime - Current time of initialization
#         - sFDI - The short form of the certificate for the system.
#         """
#         # assert EndDeviceAdapter.__tls_repository__ is not None
#         # EndDeviceAdapter.initialize_from_storage()
#         # programs = DERProgramAdapter.get_all()
#         # stored_devices = EndDeviceAdapter.get_all()
#         programs = DERProgramAdapter.fetch_all()

#         for dev in BaseAdapter.device_configs():
#             edev = m.EndDevice()
#             edev.lFDI = BaseAdapter.__tls_repository__.lfdi(dev.id)
#             edev.sFDI = BaseAdapter.__tls_repository__.sfdi(dev.id)
#             # TODO handle enum eval in a better way.
#             edev.deviceCategory = eval(f"DeviceCategoryType.{dev.deviceCategory}")
#             edev.enabled = dev.enabled

#             # TODO remove subscribable
#             edev.subscribable = None
            
#             # Add the end device to the list.
#             index = self.add(edev)
            
#             ts = int(round(datetime.utcnow().timestamp()))
#             self._reg[index] = m.Registration(href=hrefs.registration_href(index),
#                                               pIN=dev.pin, 
#                                               dateTimeRegistered=ts)
#             edev.RegistrationLink = m.RegistrationLink(href=hrefs.registration_href(index))
#             #edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
            
#             fsa_programs = []
#             for cfg_program in dev.programs:
#                 for program in programs:
#                     program.mRID = str(uuid.uuid4())
#                     if cfg_program["description"] == program.description:
#                         fsa_programs.append(program)
                    
#             if len(fsa_programs) > 0:
                
#                 fsa = m.FunctionSetAssignments()
                
#                 FSAAdapter.add(fsa)
                                
#                 for derp in fsa_programs:                  
#                     FSAAdapter.add_child(fsa, "fsa", derp)
                    
#                 edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
                
#                 # TODO we are hardcoding assuming only one fsa here.
#                 fsa.DERProgramListLink = m.DERProgramListLink(href=f"{hrefs.fsa_href(index=0)}_derp")
#                 # fsa = FSAAdapter.create(fsa_programs)
#                 # edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
#                 # self._fsa.append(fsa)
                
#                 if not self._edev_fsa.get(index):
#                     fsa_index = 0
#                     self._edev_fsa[index] = [fsa] 
#                 else:
#                     fsa_index = len(self._edev_fsa)
#                     self._edev_fsa[index].append(fsa)
                
#                 if not self._edev_derp.get(index):
#                     self._edev_derp[index] = {}

#                 self._edev_derp[index][fsa_index] = fsa_programs
            
#             has_der = False
#             for der_indx, der in enumerate(dev.ders):                
#                 DERAdapter.create(edev_index=index, der_index=der_indx, modesSupported=der["modesSupported"], deviceType=der["type"])
#                 has_der = True
#             if has_der:
#                 edev.DERListLink = m.DERListLink(hrefs.edev_der_href(edev_index=index))  # hrefs.der_sub_href(index=index))
                
#             #self._end_devices.append(edev)
                            

#             # log = m.LogEventList(href=hrefs.get_log_list_href(index),
#             #                      all=0,
#             #                      results=0,
#             #                      pollRate=BaseAdapter.server_config().log_event_list_poll_rate)
#             # edev.LogEventListLink = m.LogEventListLink(href=log.href)
#             # add_href(log.href, log)

#             # cfg = m.Configuration(href=hrefs.get_configuration_href(index))
#             # add_href(cfg.href, cfg)
#             # edev.ConfigurationLink = m.ConfigurationLink(cfg.href)

#             # ps = m.PowerStatus(href=hrefs.get_power_status_href(index))
#             # add_href(ps.href, ps)
#             # edev.PowerStatusLink = m.PowerStatusLink(href=ps.href)

#             # ds = m.DeviceStatus(href=hrefs.get_device_status(index))
#             # add_href(ds.href, ds)
#             # edev.DeviceStatusLink = m.DeviceStatusLink(href=ds.href)

#             # di = m.DeviceInformation(href=hrefs.get_device_information(index))
#             # add_href(di.href, di)
#             # edev.DeviceInformationLink = m.DeviceInformationLink(href=di.href)

#             # ts = int(round(datetime.utcnow().timestamp()))
#             # reg = m.Registration(href=hrefs.get_registration_href(index),
#             #                      pIN=dev.pin,
#             #                      dateTimeRegistered=ts)
#             # add_href(reg.href, reg)
#             # edev.RegistrationLink = m.RegistrationLink(reg.href)

#             # log = m.LogEventList(href=hrefs.get_log_list_href(index), all=0)
#             # add_href(log.href, log)
#             # edev.LogEventListLink = m.LogEventListLink(log.href)

#             # fsa_list = m.FunctionSetAssignmentsList(href=hrefs.get_fsa_list_href(edev.href))

#             # fsa = m.FunctionSetAssignments(href=hrefs.get_fsa_href(fsa_list_href=fsa_list.href,
#             #                                                        index=0),
#             #                                mRID="0F")
#             # edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(fsa_list.href)

#             # der_program_list = m.DERProgramList(href=hrefs.get_der_program_list(fsa_href=fsa.href),
#             #                                     all=0,
#             #                                     results=0)

#             # fsa.DERProgramListLink = m.DERProgramListLink(href=der_program_list.href)
#             # fsa_list.FunctionSetAssignments.append(fsa)

#             # for cfg_program in dev.programs:
#             #     for program in programs:
#             #         program.mRID = "1F"
#             #         if cfg_program["description"] == program.description:
#             #             der_program_list.all += 1
#             #             der_program_list.results += 1
#             #             der_program_list.DERProgram.append(program)
#             #             break

#             # # Allow der list here
#             # # # TODO: instantiate from config file.
#             # der_list = m.DERList(
#             #     href=hrefs.get_der_list_href(index),
#             # #pollRate=900,
#             #     results=0,
#             #     all=0)
#             # edev.DERListLink = m.DERListLink(der_list.href)

#             # self._end_devices.append(edev)

#             # edev_list.EndDevice.append(edev)
        
#     def fetch_edev_all(self) -> List:
#         return self._end_devices
    
#     def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.EndDeviceList:
#         enddevice_list = m.EndDeviceList(href=hrefs.get_enddevice_list_href(),
#                                          EndDevice=self._end_devices,
#                                          all = len(self._end_devices), results=len(self._end_devices))
#         return enddevice_list
    
#     def get_at(self, index: int) -> m.EndDevice:
#         return self._end_devices[index]
    
#     def add(self, end_device: m.EndDevice) -> int:
#         """Add and return the index of the newly added end device.
        
#         This method will also update the href to be the current location of the resource
#         """
#         end_device.href = hrefs.get_enddevice_href(len(self._end_devices))
#         self._end_devices.append(end_device)
#         return len(self._end_devices) - 1
    
#     def fetch_by_lfdi(self, lfdi: Lfdi) -> m.EndDevice:
#         try:
#             ed =  next(filter(lambda x: x.lFDI == lfdi, self._end_devices))
            
#         except StopIteration:
#             ed = None
        
#         return ed
    
#     def fetch_list_by_lfdi(self, lfdi: Lfdi) -> m.EndDeviceList:
#         try:
#             ed =  next(filter(lambda x: x.lFDI == lfdi, self._end_devices))
#             edl = m.EndDeviceList(href=hrefs.get_enddevice_list_href(),
#                             EndDevice=[ed],
#                             all=1, results=1)
#         except StopIteration:
#             edl = m.EndDeviceList(all=0, results=0)
        
#         return edl
    
#     @staticmethod
#     def get_list(lfdi: Lfdi, s: int = 0, l: int = 1) -> m.EndDeviceList:
#         ed_list = m.EndDeviceList(href=hrefs.get_enddevice_list_href(), all=0, results=0)

#         # TODO remove as we test oeg_client.
#         ed_list.pollRate = None
#         ed_list.subscribable = None

#         for ed in EndDeviceAdapter.get_all():
#             if ed.lFDI == lfdi:
#                 ed_list.all += 1
#                 ed_list.results += 1
#                 ed_list.EndDevice.append(ed)

#         return ed_list

#     @staticmethod
#     def initialize_from_storage():
#         hrefs_found = get_href_filtered(hrefs.get_enddevice_href(hrefs.NO_INDEX))
#         EndDeviceAdapter.__count__ = len(hrefs_found)

#     @staticmethod
#     def build(**kwargs) -> m.EndDevice:
#         ed = m.EndDevice()
#         populate_from_kwargs(ed, **kwargs)
#         return ed

#     @staticmethod
#     def find_index(end_device: m.EndDevice) -> int:
#         for i in range(EndDeviceAdapter.__count__ + 1):
#             if end_device.href == hrefs.get_enddevice_href(i):
#                 return i

#         raise KeyError(f"End device not found for {end_device.href}")

#     @staticmethod
#     def get_by_index(index: int) -> m.EndDevice:
#         return get_href(hrefs.get_enddevice_href(index))

#     @staticmethod
#     def get_next_href() -> str:
#         return hrefs.get_enddevice_href(EndDeviceAdapter.get_next_index())


#     @staticmethod
#     def get_by_lfdi(lfdi: Lfdi) -> m.EndDevice:
#         for ed in EndDeviceAdapter.get_all():
#             if ed.lFDI == lfdi:
#                 return ed
#         return None

#     @staticmethod
#     def store(device_id: str, value: m.EndDevice) -> m.EndDevice:
#         """Store the end device into temporary/permanant storage.
        
#         The device_id is necessary to map the configured device into the linked registration
        
#         This function will add the href and registration link to the end device.  
        
#         """
#         if not value.href:
#             value.href = EndDeviceAdapter.get_next_href()
#         if not value.RegistrationLink:
#             reg_time = datetime.now(timezone.utc)
#             pin = None
#             for dev in BaseAdapter.__device_configurations__:
#                 if dev.id == device_id:
#                     pin = dev.pin
#                     break

#             mreg = m.Registration(href=hrefs.get_registration_href(
#                 EndDeviceAdapter.find_index(value)),
#                                   pIN=pin,
#                                   dateTimeRegistered=format_time(reg_time))
#             add_href(mreg.href, mreg)
#             value.RegistrationLink = m.RegistrationLink(mreg.href)

#         add_href(value.href, value)
#         return value

#     @staticmethod
#     def get_all() -> List[m.EndDevice]:
#         end_devices: List[m.EndDevice] = []
#         href_prefix = hrefs.get_enddevice_href(hrefs.NO_INDEX)
#         cpl = re.compile(f"{href_prefix}{hrefs.SEP}[0-9]+$")
#         for ed in get_href_filtered(href_prefix=href_prefix):
#             if cpl.match(ed.href):
#                 end_devices.append(ed)

#         return sorted(end_devices, key=lambda k: k.href)

# EndDeviceAdapter = _EndDeviceAdapter()
# ready_signal.connect(EndDeviceAdapter.__initialize__, DERProgramAdapter)

EndDeviceAdapter = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
def initialize_end_device_adapter(sender):
    """ Intializes the following based upon the device configuration and the tlsrepository.
        
    Each EndDevice will have the following sub-components initialized:
    - PowerStatus - PowerStatusLink
    - DeviceStatus - DeviceStatusLink
    - Registration - RegistrationLink
    - MessagingProgramList - MessagingProgramListLink
    - Log
    Either FSA or DemandResponseProgram
    - DemandResponseProgram - DemandResponseProgramListLink
    
    
    As well as the following properties
    - changedTime - Current time of initialization
    - sFDI - The short form of the certificate for the system.
    """
    # assert EndDeviceAdapter.__tls_repository__ is not None
    # EndDeviceAdapter.initialize_from_storage()
    # programs = DERProgramAdapter.get_all()
    # stored_devices = EndDeviceAdapter.get_all()
    programs = DERProgramAdapter.fetch_all()

    for dev in BaseAdapter.device_configs():
        ts = int(round(datetime.utcnow().timestamp()))
        
        edev = m.EndDevice()
        edev.lFDI = BaseAdapter.__tls_repository__.lfdi(dev.id)
        edev.sFDI = BaseAdapter.__tls_repository__.sfdi(dev.id)
        # TODO handle enum eval in a better way.
        edev.deviceCategory = eval(f"DeviceCategoryType.{dev.deviceCategory}")
        edev.enabled = dev.enabled
        edev.changedTime = ts

        # TODO remove subscribable
        edev.subscribable = None
        
        
        EndDeviceAdapter.add(edev)
        
        # Add the end device to the list.
        index = EndDeviceAdapter.fetch_index(edev)
        
        
        EndDeviceAdapter.add_child(edev, hrefs.End_Device_Registration, 
                                   m.Registration(href=hrefs.registration_href(index), pIN=dev.pin, dateTimeRegistered=ts))
        edev.RegistrationLink = m.RegistrationLink(href=hrefs.registration_href(index))
        
        di = hrefs.EdevHref(edev_index=index, edev_subtype=hrefs.EDevSubType.DeviceInformation)
        EndDeviceAdapter.add_child(edev, hrefs.End_Device_Information, m.DeviceInformation(href=str(di)))
        edev.DeviceInformationLink = m.DeviceInformationLink(str(di))
        
        ds = hrefs.EdevHref(edev_index=index, edev_subtype=hrefs.EDevSubType.DeviceStatus)
        EndDeviceAdapter.add_child(edev, hrefs.End_Device_Status, m.DeviceStatus(str(ds)))
        edev.DeviceStatusLink = m.DeviceStatusLink(str(ds))
        
        #edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
        
        fsa_programs = []
        for cfg_program in dev.programs:
            for program in programs:
                program.mRID = uuid_2030_5()
                if cfg_program["description"] == program.description:
                    fsa_programs.append(program)
                
        if len(fsa_programs) > 0:
            
            fsa = m.FunctionSetAssignments()
            
            FSAAdapter.add(fsa)
                            
            for derp in fsa_programs:                  
                FSAAdapter.add_child(fsa, hrefs.FSA, derp)
                
            edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
            
            # TODO we are hardcoding assuming only one fsa here.
            fsa.DERProgramListLink = m.DERProgramListLink(href=f"{hrefs.fsa_href(index=0)}_{hrefs.DER_Program}")
            # fsa = FSAAdapter.create(fsa_programs)
            # edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(href=hrefs.fsa_href(edev_index=index))
            # self._fsa.append(fsa)
            EndDeviceAdapter.add_child(edev, hrefs.FSA, fsa)
            
        has_der = False
        for der_indx, der in enumerate(dev.ders):
            der_href = hrefs.EdevHref(edev_index=index, edev_subtype=hrefs.EDevSubType.DER, edev_subtype_index=der_indx)
            der = m.DER(href=str(der_href))
            der_href.edev_der_subtype = hrefs.DERSubType.Availability
            der.DERAvailabilityLink = m.DERAvailabilityLink(str(der_href))
            
            der_href.edev_der_subtype = hrefs.DERSubType.Capability
            der.DERCapabilityLink = m.DERCapabilityLink(str(der_href))
            
            der_href.edev_der_subtype = hrefs.DERSubType.Settings
            der.DERSettingsLink = m.DERSettingsLink(str(der_href))
            
            der_href.edev_der_subtype = hrefs.DERSubType.Status
            der.DERStatusLink = m.DERStatusLink(str(der_href))
            
            EndDeviceAdapter.add_child(edev, hrefs.DER, der)
            has_der = True
            
        if has_der:
            edev.DERListLink = m.DERListLink(hrefs.edev_der_href(edev_index=index))  # hrefs.der_sub_href(index=index))
    
    ready_signal.send(EndDeviceAdapter)
        #self._end_devices.append(edev)
                        

        # log = m.LogEventList(href=hrefs.get_log_list_href(index),
        #                      all=0,
        #                      results=0,
        #                      pollRate=BaseAdapter.server_config().log_event_list_poll_rate)
        # edev.LogEventListLink = m.LogEventListLink(href=log.href)
        # add_href(log.href, log)

        # cfg = m.Configuration(href=hrefs.get_configuration_href(index))
        # add_href(cfg.href, cfg)
        # edev.ConfigurationLink = m.ConfigurationLink(cfg.href)

        # ps = m.PowerStatus(href=hrefs.get_power_status_href(index))
        # add_href(ps.href, ps)
        # edev.PowerStatusLink = m.PowerStatusLink(href=ps.href)

        # ds = m.DeviceStatus(href=hrefs.get_device_status(index))
        # add_href(ds.href, ds)
        # edev.DeviceStatusLink = m.DeviceStatusLink(href=ds.href)

        # di = m.DeviceInformation(href=hrefs.get_device_information(index))
        # add_href(di.href, di)
        # edev.DeviceInformationLink = m.DeviceInformationLink(href=di.href)

        # ts = int(round(datetime.utcnow().timestamp()))
        # reg = m.Registration(href=hrefs.get_registration_href(index),
        #                      pIN=dev.pin,
        #                      dateTimeRegistered=ts)
        # add_href(reg.href, reg)
        # edev.RegistrationLink = m.RegistrationLink(reg.href)

        # log = m.LogEventList(href=hrefs.get_log_list_href(index), all=0)
        # add_href(log.href, log)
        # edev.LogEventListLink = m.LogEventListLink(log.href)

        # fsa_list = m.FunctionSetAssignmentsList(href=hrefs.get_fsa_list_href(edev.href))

        # fsa = m.FunctionSetAssignments(href=hrefs.get_fsa_href(fsa_list_href=fsa_list.href,
        #                                                        index=0),
        #                                mRID="0F")
        # edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(fsa_list.href)

        # der_program_list = m.DERProgramList(href=hrefs.get_der_program_list(fsa_href=fsa.href),
        #                                     all=0,
        #                                     results=0)

        # fsa.DERProgramListLink = m.DERProgramListLink(href=der_program_list.href)
        # fsa_list.FunctionSetAssignments.append(fsa)

        # for cfg_program in dev.programs:
        #     for program in programs:
        #         program.mRID = "1F"
        #         if cfg_program["description"] == program.description:
        #             der_program_list.all += 1
        #             der_program_list.results += 1
        #             der_program_list.DERProgram.append(program)
        #             break

        # # Allow der list here
        # # # TODO: instantiate from config file.
        # der_list = m.DERList(
        #     href=hrefs.get_der_list_href(index),
        # #pollRate=900,
        #     results=0,
        #     all=0)
        # edev.DERListLink = m.DERListLink(der_list.href)

        # self._end_devices.append(edev)

        # edev_list.EndDevice.append(edev)
ready_signal.connect(initialize_end_device_adapter, DERProgramAdapter)

