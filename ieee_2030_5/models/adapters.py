from __future__ import annotations

from dataclasses import dataclass, fields, field
import logging
import typing
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from ieee_2030_5.certs import TLSRepository

import ieee_2030_5.config as cfg
import ieee_2030_5.models as m
from ieee_2030_5 import hrefs
from ieee_2030_5.data.indexer import add_href, get_href, get_href_filtered
from ieee_2030_5.types_ import StrPath, format_time

_log = logging.getLogger(__name__)


class InvalidConfigFile(Exception):
    pass


def __populate_from_kwargs__(obj: dataclass, **kwargs) -> Dict[str, Any]:
    for k in fields(obj):
        if k.name in kwargs:
            type_eval = eval(k.type)

            if typing.get_args(type_eval) is typing.get_args(Optional[int]):
                setattr(obj, k.name, int(kwargs[k.name]))
            elif typing.get_args(k.type) is typing.get_args(Optional[bool]):
                setattr(obj, k.name, bool(kwargs[k.name]))
            # elif bytes in args:
            #     setattr(obj, k.name, bytes(kwargs[k.name]))
            else:
                setattr(obj, k.name, kwargs[k.name])
            kwargs.pop(k.name)
    return kwargs


class BaseAdapter:
    
    __server_configuration__: cfg.ServerConfiguration
    __device_configurations__: List[cfg.DeviceConfiguration] = None
    __tls_repository__: List[cfg.TLSRepository] = None
    
    @staticmethod
    def is_initialized():
        return BaseAdapter.__device_configurations__ is not None and BaseAdapter.__tls_repository__ is not None
    
    @staticmethod
    def initialize(server_config: cfg.ServerConfiguration, tlsrepo: TLSRepository):
        BaseAdapter.__server_configuration__ = server_config
        BaseAdapter.__device_configurations__ = server_config.devices
        BaseAdapter.__tls_repository__ = tlsrepo
        
        DERCurveAdapter.initialize()
        DERControlAdapter.initialize()
        DERProgramAdapter.initialize()
        EndDeviceAdapter.initialize()
        #DeviceCapabilityAdapter.initialize()

    @staticmethod
    def build(**kwargs) -> dataclass:
        raise NotImplementedError()

    @staticmethod
    def get_by_href(href: str) -> dataclass:
        return get_href(href)
    
    @staticmethod
    def get_index(data: dataclass):
        raise NotImplemented()

    @staticmethod
    def get_next_index() -> int:
        raise NotImplementedError()

    @staticmethod
    def store(value: dataclass) -> dataclass:
        raise NotImplementedError()


class DeviceCapabilityAdapter(BaseAdapter):
    pass

class EndDeviceAdapter(BaseAdapter):
    __count__: int = 0
    __config_devices__: Dict[str, cfg.DeviceConfiguration] = {}

    @staticmethod
    def initialize():
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
        
        devices: List[cfg.DeviceConfiguration] = BaseAdapter.__device_configurations__
        
        #TODO Fix This!
        
        # for index, device in enumerate(devices):
        #     device: cfg.DeviceConfiguration = device
        #     EndDeviceAdapter.__config_devices__[device.id] = device
            
        #     ed = m.EndDevice()
            
        #     ds = m.DeviceStatus(href=hrefs.get_enddevice_href(index, "dstat"))
        #     # TODO add other stuff to device status
        #     add_href(ds.href, ds)
        #     ed.DeviceStatusLink = m.DeviceStatusLink(ds.href)
            
        #     ps = m.PowerStatus(href=hrefs.get_enddevice_href(index, "ps"))
        #     # TODO add other stuff to power status
        #     add_href(ps.href, ps)
        #     ed.PowerStatusLink = m.PowerStatusLink(ps.href)
            
        #     reg = m.Registration(href=hrefs.get_enddevice_href(index, "reg"))
        #     reg.pIN = device.pin
        #     reg.pollRate = device.poll_rate
        #     add_href(reg.href, reg)        
        #     ed.RegistrationLink = m.RegistrationLink(reg.href)
            
        #     log = m.LogEventList(href=hrefs.get_enddevice_href(index, "log"))
        #     add_href(log.href, log)
        #     ed.LogEventListLink = m.LogEventListLink(log.href)
            
            # try:
            #     dev_programs = device['programs']
            #     drp = m.DemandResponseProgramList(href=hrefs.get_enddevice_href(index, "derp"), all=len(dev_programs))
            #     for dev_program in dev_programs:
            #         for program in programs:
            #             if dev_program['description'] == program.description:
                            
            # except KeyError:
            #     _log.info(f"No programs for device: {device.id}")
                            
                            
                        
                        
            # _log.debug(f"Config program\n{device}")
        
        
    @staticmethod
    def initialize_from_storage():
        hrefs_found = get_href_filtered(hrefs.get_enddevice_href(hrefs.NO_INDEX))
        EndDeviceAdapter.__count__ = len(hrefs_found)

    @staticmethod
    def build(**kwargs) -> m.EndDevice:
        ed = m.EndDevice()
        __populate_from_kwargs__(ed, **kwargs)
        return ed
    
    @staticmethod
    def get_index(end_device: m.EndDevices) -> int:
        for i in range(EndDeviceAdapter.__count__ + 1):
            if end_device.href == hrefs.get_enddevice_href(i):
                return i
        
        raise KeyError(f"End device not found for {end_device.href}")
    

    @staticmethod
    def get_by_index(index: int) -> m.EndDevice:
        return get_href(hrefs.get_enddevice_href(index))

    @staticmethod
    def get_next_index() -> int:
        return EndDeviceAdapter.__count__

    @staticmethod
    def get_next_href() -> str:
        return hrefs.get_enddevice_href(EndDeviceAdapter.get_next_index())

    @staticmethod
    def store(device_id: str, value: m.EndDevice) -> m.EndDevice:
        """Store the end device into temporary/permanant storage.
        
        The device_id is necessary to map the configured device into the linked registration
        
        This function will add the href and registration link to the end device.  
        
        """
        if not value.href:
            value.href = EndDeviceAdapter.get_next_href()
        if not value.RegistrationLink:
            reg_time = datetime.now(timezone.utc)
            mreg = m.Registration(href=hrefs.get_registration_href(EndDeviceAdapter.get_index(value)),
                                  pIN=EndDeviceAdapter.__config_devices__[device_id].pin,
                                  dateTimeRegistered=format_time(reg_time))
            add_href(mreg.href, mreg)
            value.RegistrationLink = m.RegistrationLink(mreg.href)
            
        add_href(value.href, value)
        return value
    
    @staticmethod
    def get_all() -> List[m.EndDevice]:
        return get_href_filtered(hrefs.get_enddevice_href(hrefs.NO_INDEX))
    
class DERCurveAdapter(BaseAdapter):
    __count__ = 0
    
    def initialize():
        if BaseAdapter.__device_configurations__ is None:
            raise ValueError("Initialize BaseAdapter before initializing the Curves.")
        
                  

class DERProgramAdapter(BaseAdapter):
    __count__ = 0
    # __config_programs__: Dict[str, cfg.DERProgram] = {}

    @staticmethod
    def initialize():
        
        programs = BaseAdapter.__server_configuration__.programs
        _log.debug("Update m.DERPrograms' adding links to the different program pieces.")
        # Initialize "global" m.DERPrograms href lists, including all the different links to
        # locations for active, default, curve and control lists.
        for index, program_cfg in enumerate(programs):
            program = m.DERProgram(**program_cfg.__dict__)
            # program.description = program_cfg.description
            # program.primacy = program_cfg.primacy
            # program.version = program_cfg.version
            
            # TODO Fix this!
            # program.mRID = 
            # mrid = program_cfg.get('mrid')
            # if mrid is None or len(mrid.trim()) == 0:
            #     program.mRID = f"program_mrid_{index}"
            # program_cfg['mrid'] = program.mRID
            
            program.href = hrefs.get_program_href(index)
            program.ActiveDERControlListLink = m.ActiveDERControlListLink(
                href=hrefs.get_program_href(index, "actderc"), all=0)
            program.DERCurveListLink = m.DERCurveListLink(
                href=hrefs.get_program_href(index, "dc"), all=0)
            program.DefaultDERControlLink = m.DefaultDERControlLink(
                href=hrefs.get_program_href(index, "dderc"))
            program.DERControlListLink = m.DERControlListLink(
                href=hrefs.get_program_href(index, "derc"), all=0)

            add_href(program.href, program)
            
    @staticmethod
    def get_all() -> List:
        return get_href_filtered(hrefs.get_program_href(hrefs.NO_INDEX))
        
    @staticmethod
    def build(**kwargs) -> m.DERProgram:
        """ Build a DERProgram from the passed kwargs

        kwarg variables:
            der_control_checked<int> - will be passed with the value of the href for the checked control.
            default_der_control - Is the default der control that should be used when no controls are active.
        """
        program = m.DERProgram()

        kwargs = __populate_from_kwargs__(program, **kwargs)

        href_default = kwargs.pop('default_der_control', None)
        hrefs_controls = [kwargs[k] for k in kwargs if k.startswith('der_control_checked')]

        program.DefaultDERControlLink = m.DefaultDERControlLink(href=href_default)
        # m.DERControlList
        program.DERControlListLink = hrefs.get_program_href()

        return program


class DERControlAdapter(BaseAdapter):
    __count__ = 0
    
    @staticmethod
    def initialize():
        config = DERControlAdapter.__server_configuration__.controls
        
        for index, ctl in enumerate(config):
            stored_ctl = None
            # for found in stored_controls:
            #     if ctl['description'] == found.description:
            #         _log.debug("Found description")
            #         stored_ctl = found
            #         break
            # if stored_ctl:
            #     _log.debug("Do stuff with stored ctl")
            # else:
            # Create a new DERControl and DERControlBase and initialize as much as possible
            control = m.DERControl()
            base_control = m.DERControlBase()
            control.DERControlBase = base_control
            if hasattr(ctl, "base"):
                for k, v in getattr(ctl, "base", {}).items():
                    setattr(base_control, k, v)
                del ctl["base"]
            control.href = hrefs.get_derc_href(hrefs.get_derc_href(index))
            
            control.mRID = f"dercontrol_{index}" if not hasattr(ctl, "mrid") else getattr(ctl, "mrid")
            
            add_href(control.href, control)
            

    @staticmethod
    def initialize_from_storage():
        dercs_href = hrefs.get_derc_href(hrefs.NO_INDEX)
        der_controls = get_href_filtered(dercs_href)
        DERControlAdapter.__count__ = len(der_controls)

    @staticmethod
    def build_der_control(**kwargs) -> m.DERControl:
        """ Build a DERControl object from the passed parameters.

        Args:
            **params: The parameters passed in from the web application.
        """
        control = m.DERControl()
        base_control = m.DERControlBase()
        control.DERControlBase = base_control
        field_list = fields(control)
        for k, v in kwargs.items():
            for f in field_list:
                if k == f.name:
                    setattr(control, k, v)
            for f in fields(base_control):
                if k == f.name:
                    setattr(base_control, k, v)

        return control

    @staticmethod
    def store_single(der_control: m.DERControl | m.DefaultDERControl):
        if not der_control.mRID:
            der_control.mRID = uuid.uuid4()

        if not der_control.href:
            der_control.href = hrefs.get_derc_href(DERControlAdapter.__count__)
            add_href(der_control.href, der_control)
            DERControlAdapter.__count__ += 1

        add_href(der_control.href, der_control)

    @staticmethod
    def load_from_storage() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        der_controls, default_der_control = get_href_filtered(hrefs.get_derc_href(hrefs.NO_INDEX))
        return der_controls, default_der_control

    @staticmethod
    def get_all() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        """ Retrieve a list of dataclasses for DERControl for the """
        der_controls = get_href_filtered(hrefs.get_derc_href(hrefs.NO_INDEX))
        default_der = get_href_filtered(hrefs.get_derc_default_href())
        return der_controls, default_der

    @staticmethod
    def load_from_yaml_file(yaml_file: StrPath) -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        """Load from a configuration yaml file

        The yaml file must have a list of DERControls dictionary items and a default str that matches
        with one of the DERControlName.  This method loops over the DERControls and
        creates a DERControlBase with the parameters in the config file.

        The validations that could throw errors are:

            - Required fields are DERControlName, mRID, description
            - Required no-duplicates in mRID and DERControlName

        Returns List[DERControls], DefaultDERControl
        """
        if isinstance(yaml_file, str):
            yaml_file = Path(yaml_file)
        yaml_file = yaml_file.expanduser()
        data = yaml.safe_load(yaml_file.read_text())
        default = data.get('default', None)
        if not default:
            raise ValueError(f"A default DERControl must be specified in {self.DERControlListFile}")

        # DERControls in the yaml file should be an array of DERControl instances.
        if 'DERControls' not in data or \
                not isinstance(data.get('DERControls'), list):
            raise ValueError(f"DERControls must be a list within the yaml file {self.DERControlListFile}")

        default_derc: m.DefaultDERControl = None
        derc_list: List[m.DERControl] = []
        derc_names: Dict[str, str] = {}
        mrids: Dict[str, str] = {}
        for index, derc in enumerate(data["DERControls"]):
            required = 'mRID', 'DERControlName', 'description'
            for req in required:
                if req not in derc:
                    raise ValueError(f"{req}[{index}] does not have a '{req}' in {yaml_file}.")
            name = derc.pop('DERControlName')
            mrid = derc.pop('mRID')
            description = derc.pop('description')
            if mrid in mrids:
                raise ValueError(f"Duplicate mrid {mrid} found in {yaml_file}")
            if name in derc_names:
                raise ValueError(f"Duplicate name {name} found in {yaml_file}")

            base_field_names = [fld.name for fld in fields(m.DERControlBase)]
            base_dict = {ctl: derc[ctl] for ctl in derc if ctl in base_field_names}
            control_fields = {ctl: derc[ctl] for ctl in derc if not ctl in base_dict.keys()}
            control_base = m.DERControlBase(**base_dict)
            item = m.DERControl(mRID=mrid, description=description, DERControlBase=control_base, **control_fields)
            item.href = hrefs.get_derc_href(index)

            # Build a default der control
            if name == default:
                try:
                    default_derc = m.DefaultDERControl(mRID=mrid, description=description, DERControlBase=control_base,
                                                       **control_fields)
                    default_derc.href = hrefs.get_derc_default_href()
                    add_href(default_derc.href, default_derc)
                except TypeError as ex:
                    raise InvalidConfigFile(f"{yaml_file}\ndefault config parameter {ex.args[0]}")

            add_href(item.href, item)
            derc_list.append(item)

        if not default_derc:
            raise InvalidConfigFile(f"{yaml_file} no DefaultDERControl specified.")
        if not len(derc_list) > 0:
            raise InvalidConfigFile(f"{yaml_file} must have at least one DERControl specified.")

        return derc_list, default_derc
