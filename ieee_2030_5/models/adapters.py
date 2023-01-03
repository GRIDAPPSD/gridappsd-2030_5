from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import logging
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import typing
import yaml

from ieee_2030_5 import hrefs
import ieee_2030_5.config as cfg
from ieee_2030_5.data.indexer import add_href, get_href_filtered, get_href
import ieee_2030_5.models as m
from ieee_2030_5.types_ import StrPath, format_time

_log = logging.getLogger(__name__)

class InvalidConfigFile(Exception):
    pass


def __populate_from_kwargs__(obj: dataclasses.dataclass, **kwargs) -> Dict[str, Any]:
    for k in dataclasses.fields(obj):
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
    @staticmethod
    def initialize_from_storage():
        raise NotImplementedError()

    @staticmethod
    def build(**kwargs) -> dataclasses.dataclass:
        raise NotImplementedError()

    @staticmethod
    def get_by_href(href: str) -> dataclasses.dataclass:
        return get_href(href)
    
    @staticmethod
    def get_index(data: dataclasses.dataclass):
        raise NotImplemented()

    @staticmethod
    def get_next_index() -> int:
        raise NotImplementedError()

    @staticmethod
    def store(value: dataclasses.dataclass) -> dataclasses.dataclass:
        raise NotImplementedError()
    

class EndDeviceAdapter(BaseAdapter):
    __count__: int = 0
    __config_devices__: Dict[str, cfg.DeviceConfiguration] = {}

    @staticmethod
    def initialize(devices: List):
        EndDeviceAdapter.initialize_from_storage()
        stored_devices = EndDeviceAdapter.get_all()
        
        for device in devices:
            EndDeviceAdapter.__config_devices__[device.id] = device
            _log.debug(f"Config program\n{device}")
        
        
    @staticmethod
    def initialize_from_storage():
        hrefs_found = get_href_filtered(hrefs.get_enddevice_href(-1))
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
        return get_href_filtered(hrefs.get_enddevice_href(-1))

class DERProgramAdapter(BaseAdapter):
    __count__ = 0

    @staticmethod
    def initialize(programs: List):
        DERProgramAdapter.initialize_from_storage()
        
    @staticmethod
    def initialize_from_storage():
        hrefs_found = get_href_filtered(hrefs.get_program_href(-1))
        DERProgramAdapter.__count__ = len(hrefs_found)

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
    def initialize(config: List[Any]):
        DERControlAdapter.initialize_from_storage()
        
        stored_controls, stored_default = DERControlAdapter.get_all()
        
        for ctl in config:
            stored_ctl = None
            for found in stored_controls:
                if ctl['description'] == found.description:
                    _log.debug("Found description")
                    stored_ctl = found
                    break
            if stored_ctl:
                _log.debug("Do stuff with stored ctl")
            else:
                # Create a new DERControl and DERControlBase and initialize as much as possible
                control = m.DERControl()
                base_control = m.DERControlBase()
                control.DERControlBase = base_control
                if "base" in ctl:
                    for k, v in ctl["base"].items():
                        setattr(base_control, k, v)
                    del ctl["base"]

    @staticmethod
    def initialize_from_storage():
        dercs_href = hrefs.get_derc_href(-1)
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
        field_list = dataclasses.fields(control)
        for k, v in kwargs.items():
            for f in field_list:
                if k == f.name:
                    setattr(control, k, v)
            for f in dataclasses.fields(base_control):
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
        der_controls, default_der_control = get_href_filtered(hrefs.get_derc_href(-1))
        return der_controls, default_der_control

    @staticmethod
    def get_all() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        """ Retrieve a list of dataclasses for DERControl for the """
        der_controls = get_href_filtered(hrefs.get_derc_href(-1))
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

            base_field_names = [fld.name for fld in dataclasses.fields(m.DERControlBase)]
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
