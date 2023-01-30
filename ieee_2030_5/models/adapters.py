from __future__ import annotations

import inspect
import logging
import re
import typing
import uuid
from copy import deepcopy
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

import ieee_2030_5.config as cfg
import ieee_2030_5.models as m
from ieee_2030_5 import hrefs
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.data.indexer import add_href, get_href, get_href_filtered
from ieee_2030_5.models.enums import DeviceCategoryType
from ieee_2030_5.types_ import Lfdi, StrPath, format_time

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
    __tls_repository__: cfg.TLSRepository = None

    @staticmethod
    def is_initialized():
        return BaseAdapter.__device_configurations__ is not None and BaseAdapter.__tls_repository__ is not None

    @staticmethod
    def initialize(server_config: cfg.ServerConfiguration, tlsrepo: TLSRepository):
        """Initialize all of the adapters."""
        BaseAdapter.__server_configuration__ = server_config
        BaseAdapter.__device_configurations__ = server_config.devices
        BaseAdapter.__lfdi__mapped_configuration__ = {}
        BaseAdapter.__tls_repository__ = tlsrepo

        # Map from the configuration id and lfdi to the device configuration.
        for cfg in server_config.devices:
            BaseAdapter.__lfdi__mapped_configuration__[tlsrepo.lfdi(cfg.id)] = cfg

        DERCurveAdapter.initialize()
        DERControlAdapter.initialize()
        DERProgramAdapter.initialize()
        EndDeviceAdapter.initialize()
        DeviceCapabilityAdapter.initialize()

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

    @staticmethod
    def build_instance(cls, cfg_dict: Dict, signature_cls=None) -> dataclass:
        if signature_cls is None:
            signature_cls = cls
        return cls(**{
            k: v
            for k, v in cfg_dict.items() if k in inspect.signature(signature_cls).parameters
        })


class DeviceCapabilityAdapter(BaseAdapter):
    __dcap__: m.DeviceCapability = None

    @staticmethod
    def initialize():
        dcap = m.DeviceCapability(href=hrefs.get_dcap_href())
        dcap.ResponseSetListLink = m.ResponseSetListLink(href=hrefs.get_response_set_href(), all=0)
        dcap.TimeLink = m.TimeLink(href=hrefs.get_time_href())
        dcap.EndDeviceListLink = m.EndDeviceListLink(href=hrefs.get_enddevice_href(hrefs.NO_INDEX),
                                                     all=0)
        # dcap.UsagePointListLink = m.UsagePointListLink(href=hrefs.)
        # dcap.MirrorUsagePointListLink = m.MirrorUsagePointListLink(href=hrefs.get_mup)
        DeviceCapabilityAdapter.__dcap__ = dcap

    @staticmethod
    def get_by_lfdi(lfdi: Lfdi) -> m.DeviceCapability:
        dc = deepcopy(DeviceCapabilityAdapter.__dcap__)
        if lfdi in BaseAdapter.__lfdi__mapped_configuration__:
            dc.EndDeviceListLink.all = 1
        return dc


class EndDeviceAdapter(BaseAdapter):
    __count__: int = 0

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
        programs = DERProgramAdapter.get_all()

        for dev in BaseAdapter.__device_configurations__:
            next_index = EndDeviceAdapter.get_next_index()
            edev = m.EndDevice(href=hrefs.get_enddevice_href(next_index))
            edev.lFDI = BaseAdapter.__tls_repository__.lfdi(dev.id)
            edev.sFDI = BaseAdapter.__tls_repository__.sfdi(dev.id)
            # TODO handle enum eval in a better way.
            edev.deviceCategory = eval(f"DeviceCategoryType.{dev.deviceCategory}")
            edev.enabled = dev.enabled

            # TODO remove subscribable
            edev.subscribable = None

            cfg = m.Configuration(href=hrefs.get_configuration_href(next_index))
            add_href(cfg.href, cfg)
            # edev.ConfigurationLink = m.ConfigurationLink(cfg.href)

            ps = m.PowerStatus(href=hrefs.get_power_status_href(next_index))
            add_href(ps.href, ps)
            #edev.PowerStatusLink = m.PowerStatusLink(href=ps.href)

            ds = m.DeviceStatus(href=hrefs.get_device_status(next_index))
            add_href(ds.href, ds)
            #edev.DeviceStatusLink = m.DeviceStatusLink(href=ds.href)

            di = m.DeviceInformation(href=hrefs.get_device_information(next_index))
            add_href(di.href, di)
            #edev.DeviceInformationLink = m.DeviceInformationLink(href=di.href)

            ts = int(round(datetime.utcnow().timestamp()))
            reg = m.Registration(href=hrefs.get_registration_href(next_index),
                                 pIN=dev.pin,
                                 dateTimeRegistered=ts)
            add_href(reg.href, reg)
            edev.RegistrationLink = m.RegistrationLink(reg.href)

            log = m.LogEventList(href=hrefs.get_log_list_href(next_index), all=0)
            add_href(log.href, log)
            edev.LogEventListLink = m.LogEventListLink(log.href)

            fsa_list = m.FunctionSetAssignmentsList(href=hrefs.get_fsa_list_href(edev.href))

            fsa = m.FunctionSetAssignments(href=hrefs.get_fsa_href(fsa_list_href=fsa_list.href,
                                                                   index=0),
                                           mRID="0F")
            edev.FunctionSetAssignmentsListLink = m.FunctionSetAssignmentsListLink(fsa_list.href)

            der_program_list = m.DERProgramList(href=hrefs.get_der_program_list(fsa_href=fsa.href),
                                                all=0,
                                                results=0)

            fsa.DERProgramListLink = m.DERProgramListLink(href=der_program_list.href)
            fsa_list.FunctionSetAssignments.append(fsa)

            for cfg_program in dev.programs:
                for program in programs:
                    program.mRID = "1F"
                    if cfg_program["description"] == program.description:
                        der_program_list.all += 1
                        der_program_list.results += 1
                        der_program_list.DERProgram.append(program)
                        break

            # Allow der list here
            # # TODO: instantiate from config file.
            der_list = m.DERList(
                href=hrefs.get_der_list_href(next_index),
            #pollRate=900,
                results=0,
                all=0)
            edev.DERListLink = m.DERListLink(der_list.href)

            add_href(der_list.href, der_list)
            add_href(fsa.href, fsa)
            add_href(fsa_list.href, fsa_list)
            add_href(der_program_list.href, der_program_list)

            add_href(edev.href, edev)
            EndDeviceAdapter.__count__ += 1

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
    def get_list(lfdi: Lfdi, s: int = 0, l: int = 1) -> m.EndDeviceList:
        ed_list = m.EndDeviceList(href=hrefs.get_enddevice_list_href(), all=0, results=0)

        # TODO remove as we test oeg_client.
        ed_list.pollRate = None
        ed_list.subscribable = None

        for ed in EndDeviceAdapter.get_all():
            if ed.lFDI == lfdi:
                ed_list.all += 1
                ed_list.results += 1
                ed_list.EndDevice.append(ed)

        return ed_list

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
    def add(sfdi: str, lfdi: Lfdi) -> m.EndDevice:
        dev = m.EndDevice(href=EndDeviceAdapter.get_next_href(), sFDI=sfdi, lFDI=lfdi)
        dev.RegistrationLink = m.RegistrationLink(href=hrefs.get_registration_href())

    @staticmethod
    def get_by_lfdi(lfdi: Lfdi) -> m.EndDevice:
        for ed in EndDeviceAdapter.get_all():
            if ed.lFDI == lfdi:
                return ed
        return None

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
            pin = None
            for dev in BaseAdapter.__device_configurations__:
                if dev.id == device_id:
                    pin = dev.pin
                    break

            mreg = m.Registration(href=hrefs.get_registration_href(
                EndDeviceAdapter.get_index(value)),
                                  pIN=pin,
                                  dateTimeRegistered=format_time(reg_time))
            add_href(mreg.href, mreg)
            value.RegistrationLink = m.RegistrationLink(mreg.href)

        add_href(value.href, value)
        return value

    @staticmethod
    def get_all() -> List[m.EndDevice]:
        end_devices: List[m.EndDevice] = []
        href_prefix = hrefs.get_enddevice_href(hrefs.NO_INDEX)
        cpl = re.compile(f"{href_prefix}{hrefs.SEP}[0-9]+$")
        for ed in get_href_filtered(href_prefix=href_prefix):
            if cpl.match(ed.href):
                end_devices.append(ed)

        return sorted(end_devices, key=lambda k: k.href)


class DERCurveAdapter(BaseAdapter):
    __count__ = 0

    def initialize():
        if BaseAdapter.__device_configurations__ is None:
            raise ValueError("Initialize BaseAdapter before initializing the Curves.")

        curves_cfg = BaseAdapter.__server_configuration__.curves

        for index, curve_cfg in enumerate(curves_cfg):

            der_curve = m.DERCurve(**curve_cfg.__dict__)
            der_curve.href = hrefs.get_curve_href(index)
            add_href(der_curve.href, der_curve)

    @staticmethod
    def get_all() -> DERCurveAdapter:
        return list(filter(lambda x: isinstance(x, m.DERCurve), get_href_filtered("")))


class DERProgramAdapter(BaseAdapter):
    __count__ = 0
    # __config_programs__: Dict[str, cfg.DERProgram] = {}

    @staticmethod
    def initialize():

        cfg_programs = BaseAdapter.__server_configuration__.programs
        cfg_der_controls = BaseAdapter.__server_configuration__.controls
        _log.debug("Update m.DERPrograms' adding links to the different program pieces.")

        der_controls = DERControlAdapter.get_all()
        der_curves = DERCurveAdapter.get_all()
        # Initialize "global" m.DERPrograms href lists, including all the different links to
        # locations for active, default, curve and control lists.
        for index, program_cfg in enumerate(cfg_programs):
            # The configuration contains a mapping to control lists so when
            # building the DERProgram object we need to remove it from the paramters before
            # initialization.
            params = program_cfg.__dict__.copy()
            del params['default_control']
            del params['controls']
            del params['curves']
            program = m.DERProgram(**params)
            program.description = program_cfg.description
            program.primacy = program_cfg.primacy
            # program.version = program_cfg.version

            # TODO Fix this!
            # program.mRID =
            # mrid = program_cfg.get('mrid')
            # if mrid is None or len(mrid.trim()) == 0:
            #     program.mRID = f"program_mrid_{index}"
            # program_cfg['mrid'] = program.mRID

            program.href = hrefs.get_program_href(index)

            try:
                der_ctl = next(
                    filter(lambda d: d.description == program_cfg.default_control, der_controls))
                der_cfg = next(
                    filter(lambda d: d.description == program_cfg.default_control,
                           cfg_der_controls))
            except StopIteration:
                raise InvalidConfigFile(
                    f"Section program: {program_cfg.description} default control {program_cfg.default_control} not found!"
                )
            else:
                default_ctl: m.DefaultDERControl = BaseAdapter.build_instance(
                    m.DefaultDERControl, der_cfg.__dict__)
                default_ctl.href = hrefs.get_derc_default_href(index)
                #default_ctl.mRID = der_ctl.mRID + " default"
                default_ctl.setESDelay = 20
                default_ctl.DERControlBase = der_ctl.DERControlBase

                add_href(default_ctl.href, default_ctl)
                program.DefaultDERControlLink = m.DefaultDERControlLink(href=default_ctl.href)

            der_control_list = m.DERControlList(href=hrefs.get_program_href(index, hrefs.DERC))

            for ctl_description in program_cfg.controls:
                try:
                    derc = next(filter(lambda d: d.description == ctl_description, der_controls))
                except StopIteration:
                    raise InvalidConfigFile(
                        f"Section program: {program_cfg.description} control {ctl_description} not found!"
                    )
                else:
                    der_control_list.DERControl.append(derc)

            add_href(der_control_list.href, der_control_list)

            der_curve_list = m.DERCurveList(href=hrefs.get_program_href(index, hrefs.CURVE))

            for curve_description in program_cfg.curves:
                try:
                    der_curve = next(
                        filter(lambda d: d.description == curve_description, der_curves))
                except StopIteration:
                    raise InvalidConfigFile(
                        f"Section program: {program_cfg.description} curve {curve_description} not found!"
                    )
                else:
                    der_curve_list.DERCurve.append(der_curve)

            der_curve_list.all = len(der_curve_list.DERCurve)

            add_href(der_control_list.href, der_curve_list)
            add_href(program.href, program)

    @staticmethod
    def get_all() -> List[m.DERProgram]:
        return list(
            filter(lambda p: isinstance(p, m.DERProgram),
                   get_href_filtered(hrefs.get_program_href(hrefs.NO_INDEX))))

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
            base_control: m.DERControlBase = BaseAdapter.build_instance(m.DERControlBase, ctl.base)

            control: m.DERControl = BaseAdapter.build_instance(m.DERControl, ctl.__dict__)
            control.href = hrefs.get_derc_href(index=index)
            #control.mRID = f"MYCONTROL{index}"
            control.DERControlBase = base_control

            # control.mRID = f"dercontrol_{index}" if not hasattr(ctl, "mrid") else getattr(
            #     ctl, "mrid")
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
    def get_all() -> List[m.DERControl]:
        """ Retrieve a list of dataclasses for DERControl for the """
        return list(filter(lambda a: isinstance(a, m.DERControl), get_href_filtered("")))

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
            raise ValueError(
                f"A default DERControl must be specified in {self.DERControlListFile}")

        # DERControls in the yaml file should be an array of DERControl instances.
        if 'DERControls' not in data or \
                not isinstance(data.get('DERControls'), list):
            raise ValueError(
                f"DERControls must be a list within the yaml file {self.DERControlListFile}")

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
            item = m.DERControl(mRID=mrid,
                                description=description,
                                DERControlBase=control_base,
                                **control_fields)
            item.href = hrefs.get_derc_href(index)

            # TODO: Figure out if we need a global default or if that
            # is specific to the DERProgram construct.
            # Build a default der control
            # if name == default:
            #     try:
            #         default_derc = m.DefaultDERControl(mRID=mrid,
            #                                            description=description,
            #                                            DERControlBase=control_base,
            #                                            **control_fields)
            #         default_derc.href = hrefs.get_derc_default_href()
            #         add_href(default_derc.href, default_derc)
            #     except TypeError as ex:
            #         raise InvalidConfigFile(f"{yaml_file}\ndefault config parameter {ex.args[0]}")

            add_href(item.href, item)
            derc_list.append(item)

        # if not default_derc:
        #     raise InvalidConfigFile(f"{yaml_file} no DefaultDERControl specified.")
        if not len(derc_list) > 0:
            raise InvalidConfigFile(f"{yaml_file} must have at least one DERControl specified.")

        return derc_list, None    # default_derc
