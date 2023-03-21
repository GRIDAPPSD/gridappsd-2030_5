from __future__ import annotations

import inspect
import logging
import re
import typing
import uuid
from copy import deepcopy
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Container, Dict, List, Optional, Protocol, Sized

import yaml

import ieee_2030_5.config as cfg
import ieee_2030_5.models as m
from ieee_2030_5 import hrefs
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.data.indexer import add_href, get_href, get_href_filtered
from ieee_2030_5.models import DeviceCategoryType
from ieee_2030_5.models.adapters import ReturnCode, populate_from_kwargs
from ieee_2030_5.types_ import Lfdi, StrPath, format_time

_log = logging.getLogger(__name__)


class BaseAdapter:
    __count__: int = 0
    __server_configuration__: cfg.ServerConfiguration
    __tls_repository__: cfg.TLSRepository = None
    __lfdi__mapped_configuration__: Dict[str, cfg.DeviceConfiguration] = {}

    @classmethod
    def get_next_index(cls) -> int:
        """Retrieve the next index for an adapter list."""
        return cls.__count__

    @classmethod
    def increment_index(cls) -> int:
        """Increment the list to the next index and return the result to the caller.
        
        
        """
        next = cls.get_next_index()
        cls.__count__ += 1
        return next

    @classmethod
    def get_current_index(cls) -> int:
        return cls.__count__

    @staticmethod
    def server_config() -> cfg.ServerConfiguration:
        return BaseAdapter.__server_configuration__

    @staticmethod
    def device_configs() -> cfg.DeviceConfiguration:
        return BaseAdapter.__server_configuration__.devices

    @staticmethod
    def tls_repo() -> cfg.TLSRepository:
        return BaseAdapter.__tls_repository__

    @staticmethod
    def get_config_from_lfdi(lfdi: str) -> Optional[cfg.DeviceConfiguration]:
        return BaseAdapter.__lfdi__mapped_configuration__.get(lfdi)

    @staticmethod
    def is_initialized():
        return BaseAdapter.__device_configurations__ is not None and BaseAdapter.__tls_repository__ is not None

    @staticmethod
    def initialize(server_config: cfg.ServerConfiguration, tlsrepo: TLSRepository):
        """Initialize all of the adapters
        
        The initialization means that there are concrete object backing the storage system based upon
        urls that can be read during the http call to the spacific end point.  In other words a
        DERCurve dataclass can be retrieved from storage by going to the href /dc/1 rather than
        having to get it through an object.  
        
        The adapters are responsible for storing data into the object store using add_href function.
        """
        BaseAdapter.__server_configuration__ = server_config
        BaseAdapter.__lfdi__mapped_configuration__ = {}
        BaseAdapter.__tls_repository__ = tlsrepo

        # Map from the configuration id and lfdi to the device configuration.
        for cfg in server_config.devices:
            lfdi = tlsrepo.lfdi(cfg.id)
            BaseAdapter.__lfdi__mapped_configuration__[lfdi] = cfg

        # Find subclasses of us and initialize them calling _initalize method
        # TODO make this non static
        EndDeviceAdapter._initialize()

    @staticmethod
    def build(**kwargs) -> dataclass:
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


class LogAdapter(BaseAdapter):

    @staticmethod
    def store(path: str, logevent: m.LogEvent):
        """Store a logevent to the given path.
        
        The 2030.5 Logevent is based upon a specific device so /edev/edevid/log is the event
        list that should be stored.  The store method only stores a single event at a time.  The
        2030.5 standard says we should hold at least 10 logs per logevent level."""
        event_list: m.LogEventList = get_href(path)
        if event_list is None:
            event_list = m.LogEventList(
                href=path, pollRate=BaseAdapter.server_config().log_event_list_poll_rate)
            event_list.LogEvent = []

        event_list.LogEvent.append(logevent)
        event_list.LogEvent = sorted(event_list.LogEvent, key="createdDateTime")
        add_href(path, event_list)

    @staticmethod
    def fetch_list(path: str, start: int = 0, after: int = 0, limit: int = 1) -> m.LogEventList:
        # TODO: implement start length
        event_list: m.LogEventList = get_href(path)

        if event_list is None:
            return m.LogEventList(href=path,
                                  all=0,
                                  results=0,
                                  pollRate=BaseAdapter.server_config().log_event_list_poll_rate)

        event_list.all = len(event_list.LogEvent)
        event_list.results = len(event_list.LogEvent)

        return event_list


class DeviceCapabilityAdapter(BaseAdapter):

    @classmethod
    @lru_cache
    def get_default_dcap(cls) -> m.DeviceCapability:
        dcap = m.DeviceCapability(href=hrefs.get_dcap_href(),
                                  pollRate=BaseAdapter.server_config().device_capability_poll_rate)
        dcap.ResponseSetListLink = m.ResponseSetListLink(href=hrefs.get_response_set_href(), all=0)
        dcap.TimeLink = m.TimeLink(href=hrefs.get_time_href())
        dcap.EndDeviceListLink = m.EndDeviceListLink(href=hrefs.get_enddevice_href(hrefs.NO_INDEX),
                                                     all=0)
        dcap.MirrorUsagePointListLink = m.MirrorUsagePointListLink(
            href=hrefs.mirror_usage_point_href())
        dcap.UsagePointListLink = m.UsagePointListLink(href=hrefs.usage_point_href())
        return dcap

    @staticmethod
    def get_by_lfdi(lfdi: Lfdi) -> m.DeviceCapability:
        dc = DeviceCapabilityAdapter.get_default_dcap()
        config = BaseAdapter.get_config_from_lfdi(lfdi)
        if config:
            dc.EndDeviceListLink.all = 1
        return dc


class EndDeviceAdapter(BaseAdapter):

    @staticmethod
    def _initialize():
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

        edev_list = m.EndDeviceList(
            href=hrefs.get_enddevice_list_href(),
            all=0,
            pollRate=EndDeviceAdapter.server_config().end_device_list_poll_rate,
            EndDevice=[])

        for dev in BaseAdapter.device_configs():
            index = EndDeviceAdapter.increment_index()
            edev = m.EndDevice(href=hrefs.get_enddevice_href(index))
            edev.lFDI = BaseAdapter.__tls_repository__.lfdi(dev.id)
            edev.sFDI = BaseAdapter.__tls_repository__.sfdi(dev.id)
            # TODO handle enum eval in a better way.
            edev.deviceCategory = eval(f"DeviceCategoryType.{dev.deviceCategory}")
            edev.enabled = dev.enabled

            # TODO remove subscribable
            edev.subscribable = None

            log = m.LogEventList(href=hrefs.get_log_list_href(index),
                                 all=0,
                                 results=0,
                                 pollRate=BaseAdapter.server_config().log_event_list_poll_rate)
            edev.LogEventListLink = m.LogEventListLink(href=log.href)
            add_href(log.href, log)

            cfg = m.Configuration(href=hrefs.get_configuration_href(index))
            add_href(cfg.href, cfg)
            edev.ConfigurationLink = m.ConfigurationLink(cfg.href)

            ps = m.PowerStatus(href=hrefs.get_power_status_href(index))
            add_href(ps.href, ps)
            edev.PowerStatusLink = m.PowerStatusLink(href=ps.href)

            ds = m.DeviceStatus(href=hrefs.get_device_status(index))
            add_href(ds.href, ds)
            edev.DeviceStatusLink = m.DeviceStatusLink(href=ds.href)

            di = m.DeviceInformation(href=hrefs.get_device_information(index))
            add_href(di.href, di)
            edev.DeviceInformationLink = m.DeviceInformationLink(href=di.href)

            ts = int(round(datetime.utcnow().timestamp()))
            reg = m.Registration(href=hrefs.get_registration_href(index),
                                 pIN=dev.pin,
                                 dateTimeRegistered=ts)
            add_href(reg.href, reg)
            edev.RegistrationLink = m.RegistrationLink(reg.href)

            log = m.LogEventList(href=hrefs.get_log_list_href(index), all=0)
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
                href=hrefs.get_der_list_href(index),
            #pollRate=900,
                results=0,
                all=0)
            edev.DERListLink = m.DERListLink(der_list.href)

            add_href(der_list.href, der_list)
            add_href(fsa.href, fsa)
            add_href(fsa_list.href, fsa_list)
            add_href(der_program_list.href, der_program_list)
            add_href(edev.href, edev)

            edev_list.EndDevice.append(edev)
        edev_list.all = edev_list.results = len(edev_list.EndDevice)
        add_href(edev_list.href, edev_list)

    @staticmethod
    def fetch_list(path: str,
                   start: int = 0,
                   after: int = 0,
                   limit: int = 1,
                   lfdi: Lfdi = None) -> m.LogEventList:
        # TODO: implement start length
        edev_list: m.EndDeviceList = get_href(path)

        if edev_list is None:
            return m.EndDeviceList(href=path,
                                   all=0,
                                   results=0,
                                   pollRate=BaseAdapter.server_config().end_device_list_poll_rate)

        edev_list.EndDevice = list(filter(lambda x: x.lFDI == lfdi, edev_list.EndDevice))
        edev_list.all = len(edev_list.EndDevice)
        edev_list.results = len(edev_list.EndDevice)

        return edev_list

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
        populate_from_kwargs(ed, **kwargs)
        return ed

    @staticmethod
    def find_index(end_device: m.EndDevices) -> int:
        for i in range(EndDeviceAdapter.__count__ + 1):
            if end_device.href == hrefs.get_enddevice_href(i):
                return i

        raise KeyError(f"End device not found for {end_device.href}")

    @staticmethod
    def get_by_index(index: int) -> m.EndDevice:
        return get_href(hrefs.get_enddevice_href(index))

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
                EndDeviceAdapter.find_index(value)),
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

    def initialize():
        """Initialize the DERCurve objects based upon the BaseAdapter.__device_configuration__"""

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

    @staticmethod
    def initialize():
        """Initialize the DERProgram objects based upon the BaseAdapter.__server_configuration__"""
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

        kwargs = populate_from_kwargs(program, **kwargs)

        href_default = kwargs.pop('default_der_control', None)
        hrefs_controls = [kwargs[k] for k in kwargs if k.startswith('der_control_checked')]

        program.DefaultDERControlLink = m.DefaultDERControlLink(href=href_default)
        # m.DERControlList
        program.DERControlListLink = hrefs.get_program_href()

        return program


class DERControlAdapter(BaseAdapter):

    @staticmethod
    def fetch_default() -> m.DefaultDERControl:
        dderc = get_href(hrefs.get_dderc_href())

        if dderc is None:
            derbase = m.DERControlBase(opModConnect=True, opModEnergize=False)

            # Defaults from Jakaria on 1/26/2023
            dderc = m.DefaultDERControl(href=hrefs.get_dderc_href(),
                                        mRID=uuid.uuid4(),
                                        description="Default DER Control Mode",
                                        setESDelay=300,
                                        setESLowVolt=0.917,
                                        setESHighVolt=1.05,
                                        setESLowFreq=59.5,
                                        setESHighFreq=60.1,
                                        setESRampTms=300,
                                        setESRandomDelay=0,
                                        DERControlBase=derbase)
            add_href(dderc.href, dderc)

        return dderc

    @staticmethod
    def store_default(dderc: m.DefaultDERControl):
        add_href(hrefs.get_dderc_href(), dderc)

    @staticmethod
    def initialize():
        """Initialize the DERControl and DERControlBase objects based upon the BaseAdapter.__server_configuration__"""
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
    def create_from_parameters(**kwargs) -> m.DERControl:
        """Create and store a new DERControl object from the passed kwargs
        
        If invalid parameters are passed then a ValueError should be raised.        
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


if __name__ == '__main__':
    import yaml

    from ieee_2030_5.__main__ import get_tls_repository
    from ieee_2030_5.config import ServerConfiguration
    
    cfg_pth = Path("/home/os2004/repos/gridappsd-2030_5/config.yml")
    cfg_dict = yaml.safe_load(cfg_pth.read_text())

    config = ServerConfiguration(**cfg_dict)

    tls_repo = get_tls_repository(config, False)

    BaseAdapter.initialize(config, tls_repo)    
    
    print(EndDeviceAdapter.fetch_list('/edev'))