from __future__ import annotations

import inspect
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, TypeVar, Union

import yaml
from dataclasses_json import dataclass_json

__all__ = ["ServerConfiguration", "ReturnValue"]

import json

try:
    from gridappsd.field_interface import MessageBusDefinition
except ImportError as ex:
    pass

import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.server.exceptions import NotFoundError
from ieee_2030_5.types_ import Lfdi

_log = logging.getLogger(__name__)

D = TypeVar("D")


@dataclass
class ReturnValue:
    success: bool
    an_object: D
    was_update: bool
    location: str = None

    def get(self, datatype: D) -> D:
        return self.an_object


class InvalidConfigFile(Exception):
    pass


@dataclass
class FSAConfiguration:
    description: str
    programs: List[ProgramConfiguration] = field(default_factory=list)


@dataclass
class DERConfiguration:
    #capabilities:
    modesSupported: str
    type: int


@dataclass
class DeviceConfiguration:
    id: str = None
    lfdi: Lfdi | None = None
    post_rate: int = 900
    pin: int = None
    poll_rate: int = 900
    fsas: List[str] = field(default_factory=list)
    ders: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.id.__hash__()


@dataclass
class CurveConfiguration:

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__()


@dataclass
class ControlBaseConfiguration:

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__()


@dataclass
class ControlConfiguration:
    description: str = None
    base: Dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, env):
        return cls(
            **{
                k: v
                for k, v in env.items() if k in inspect.signature(m.DERControl).parameters
                or k in inspect.signature(cls).parameters
            })

    def __hash__(self):
        return self.description.__hash__()


@dataclass
class ProgramConfiguration:

    default_control: str = None
    controls: List[str] = field(default_factory=list)
    curves: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__()


@dataclass_json
@dataclass
class GridappsdConfiguration:
    model_name: str
    default_pin: str
    publish_interval_seconds: int
    house_named_inverters_regex: str | None = None
    utility_named_inverters_regex: str | None = None
    model_dict_file: str | None = None
    address: str = 'localhost'
    port: int = 61613
    username: str = 'system'
    password: str = 'manager'
    field_bus_def: MessageBusDefinition | str | None = None
    feeder_id_file: Optional[str] = None
    feeder_id: Optional[str] = None
    simulation_id_file: Optional[str] = None

    @property
    def full_address(self):
        return f"tcp://{self.address}:{self.port}"

    def __post_init__(self):
        if self.field_bus_def is not None:
            if isinstance(self.field_bus_def, str):
                fb = json.loads(self.field_bus_def)
            else:
                fb = self.field_bus_def

            if is_ot_bus := fb.get('is_ot_bus', True):
                fb['connection_type'] = 'CONNECTION_TYPE_GRIDAPPSD'
                fb['connection_args'] = dict(
                    GRIDAPPSD_ADDRESS=self.full_address,
                    GRIDAPPSD_USER=self.username,
                    GRIDAPPSD_PASSWORD=self.password
                )

            else:
                assert fb['connection_args']
                assert fb['connection_type']

            # TODO: Error in gridappsd-python library the spelling is definately incorrect.
            fb['conneciton_args'] = fb.pop('connection_args')
            assert fb['id']

            self.field_bus_def = MessageBusDefinition(**fb)


@dataclass
class ProgramList:
    name: str
    programs: List[m.DERProgram]


@dataclass
class ServerConfiguration:
    openssl_cnf: str

    tls_repository: str

    server: str
    port: int

    service_name: str = "IEEE_2030_5"
    simulation_id: str | None = None

    ui_port: int = None

    include_default_der_on_all_devices: bool = True
    include_default_der_program_on_ders: bool = True

    default_program: m.DERProgram | None = None
    default_der_control: m.DefaultDERControl | None = None

    cleanse_storage: bool = True
    storage_path: str = None

    log_event_list_poll_rate: int = 900
    device_capability_poll_rate: int = 900
    mirror_usage_point_post_rate: int = 300
    end_device_list_poll_rate: int = 86400    # daily check-in

    generate_admin_cert: bool = False
    lfdi_client: str | None = None

    fsas: List[FSAConfiguration] = field(default_factory=list)
    programs: List[ProgramConfiguration] = field(default_factory=list)
    devices: List[DeviceConfiguration] = field(default_factory=list)
    ders: List[DERConfiguration] = field(default_factory=list)
    curves: List[CurveConfiguration] = field(default_factory=list)

    server_mode: Union[
        Literal["enddevices_create_on_start"],
        Literal["enddevices_register_access_only"]] = "enddevices_register_access_only"

    lfdi_mode: Union[
        Literal["lfdi_mode_from_file"],
        Literal["lfdi_mode_from_cert_fingerprint"]] = "lfdi_mode_from_cert_fingerprint"

    # programs: List[DERProgramConfiguration] = field(default_factory=list)
    # controls: List[DERControlConfiguration] = field(default_factory=list)
    # curves: List[DERCurveConfiguration] = field(default_factory=list)
    # events: List[Dict] = field(default_factory=list)

    # # map into program_lists array for programs for specific
    # # named list.
    # programs_map: Dict[str, int] = field(default_factory=dict)
    # program_lists: List[ProgramList] = field(default_factory=list)
    # fsa_list: List[FunctionSetAssignments] = field(default_factory=list)
    # curve_list: List[DERCurve] = field(default_factory=list)

    proxy_hostname: Optional[str] = None
    gridappsd: Optional[GridappsdConfiguration] = None
    # DefaultDERControl: Optional[DefaultDERControl] = None
    # DERControlList: Optional[DERControl] = field(default=list)

    @property
    def server_hostname(self) -> str:
        server = self.server
        if self.port:
            server = server + f":{self.port}"

        return server

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    @classmethod
    def load(cls, file: Path) -> ServerConfiguration:
        if not file.exists():
            raise InvalidConfigFile(f"File does not exist: {file}")
        return cls.from_dict(yaml.safe_load(file.read_text()))

    def __post_init__(self):
        # self.curves = [DERCurveConfiguration.from_dict(x) for x in self.curves]
        # self.controls = [DERControlConfiguration.from_dict(x) for x in self.controls]
        # self.programs = [DERProgramConfiguration.from_dict(x) for x in self.programs]

        if self.devices is None:
            self.devices = []
        else:
            self.devices = [DeviceConfiguration.from_dict(x) for x in self.devices]

        if self.default_program:
            # Get DefaultDERControl off of the default program and bulid the base.
            if 'DefaultDERControl' in self.default_program:
                self.default_der_control = m.DefaultDERControl(
                    **{k: v for k, v in self.default_program.items() if k in inspect.signature(m.DefaultDERControl).parameters})

                if 'DERControlBase' in self.default_program['DefaultDERControl']:
                    cb = self.default_program['DefaultDERControl']['DERControlBase']
                    self.default_der_control.DERControlBase = m.DERControlBase(**{k: v for k, v in cb.items() if k in inspect.signature(m.DERControlBase).parameters})


            # Populate from the default_program dictionary the keys of the configuration file.
            self.default_program = m.DERProgram(
                **{k: v
                   for k, v in self.default_program.items() if k in inspect.signature(m.DERProgram).parameters})

        if self.gridappsd:
            self.gridappsd = GridappsdConfiguration.from_dict(self.gridappsd)

            # TODO Configuration for field bus here
            # if Path(self.gridappsd.feeder_id_file).exists():
            #     self.gridappsd.feeder_id = Path(self.gridappsd.feeder_id_file).read_text().strip()
            # if Path(self.gridappsd.simulation_id_file).exists():
            #     self.gridappsd.simulation_id = Path(
            #         self.gridappsd.simulation_id_file).read_text().strip()

            # if not self.gridappsd.feeder_id:
            #     raise ValueError(
            #         "Feeder id from gridappsd not found in feeder_id_file nor was specified "
            #         "in gridappsd config section.")

            # # TODO: This might not be the best place for this manipulation
            # self.gridappsd.field_bus_def = MessageBusDefinition.load(
            #     self.gridappsd.field_bus_def)
            # self.gridappsd.field_bus_def.id = self.gridappsd.feeder_id

            # _log.info("Gridappsd Configuration For Simulation")
            # _log.info(f"feeder id: {self.gridappsd.feeder_id}")
            # if self.gridappsd.simulation_id:
            #     _log.info(f"simulation id: {self.gridappsd.simulation_id}")
            # else:
            #     _log.info("no simulation id")
            # _log.info("x" * 80)

        # if self.field_bus_def:
        #     self.field_bus_def = MessageBusDefinition.load(self.field_bus_def)

    def get_device_pin(self, lfdi: Lfdi, tls_repo: TLSRepository) -> int:
        for d in self.devices:
            test_lfdi = tls_repo.lfdi(d.id)
            if test_lfdi == int(lfdi):
                return d.pin
        raise NotFoundError(f"The device_id: {lfdi} was not found.")
