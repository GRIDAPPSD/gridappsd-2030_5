from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, Literal, TypeVar

import yaml
from dataclasses_json import dataclass_json

__all__ = ["ServerConfiguration", "ReturnValue"]

import json

try:
    from gridappsd.field_interface import MessageBusDefinition
except ImportError:
    pass

import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.server.exceptions import NotFoundError
from ieee_2030_5.types_ import Lfdi

_log = logging.getLogger(__name__)

D = TypeVar("D")


@dataclass
class ReturnValue(Generic[D]):
    success: bool
    an_object: D
    was_update: bool
    location: str | None = None

    def get(self, datatype: D) -> D:
        return self.an_object


class InvalidConfigFile(Exception):
    pass


@dataclass
class FSAConfiguration:
    description: str
    programs: list[ProgramConfiguration] = field(default_factory=list)


@dataclass
class DERConfiguration:
    # capabilities:
    modesSupported: str
    type: int


@dataclass
class DeviceConfiguration:
    id: str | None = None
    lfdi: Lfdi | None = None
    post_rate: int = 3
    pin: int | None = None
    poll_rate: int = 3
    fsas: list[str] = field(default_factory=list)
    ders: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.id.__hash__() if self.id else 0


@dataclass
class CurveConfiguration:
    description: str | None = None

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__() if self.description else 0


@dataclass
class ControlBaseConfiguration:
    description: str | None = None

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__() if self.description else 0


@dataclass
class ControlConfiguration:
    description: str | None = None
    base: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, env):
        return cls(
            **{
                k: v
                for k, v in env.items()
                if k in inspect.signature(m.DERControl).parameters or k in inspect.signature(cls).parameters
            }
        )

    def __hash__(self):
        return self.description.__hash__() if self.description else 0


@dataclass
class ProgramConfiguration:
    description: str | None = None
    default_control: str | None = None
    controls: list[str] = field(default_factory=list)
    curves: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.description.__hash__() if self.description else 0


@dataclass_json
@dataclass
class GridappsdConfiguration:
    model_name: str
    default_pin: str
    publish_interval_seconds: int
    house_named_inverters_regex: str | None = None
    utility_named_inverters_regex: str | None = None
    model_dict_file: str | None = None
    address: str = "localhost"
    port: int = 61613
    username: str = "system"
    password: str = "manager"
    field_bus_def: MessageBusDefinition | str | None = None
    feeder_id_file: str | None = None
    feeder_id: str | None = None
    simulation_id_file: str | None = None

    @property
    def full_address(self):
        return f"tcp://{self.address}:{self.port}"

    def __post_init__(self):
        if self.field_bus_def is not None:
            if isinstance(self.field_bus_def, str):
                fb = json.loads(self.field_bus_def)
            else:
                fb = self.field_bus_def

            if is_ot_bus := fb.get("is_ot_bus", True):
                fb["connection_type"] = "CONNECTION_TYPE_GRIDAPPSD"
                fb["connection_args"] = dict(
                    GRIDAPPSD_ADDRESS=self.full_address, GRIDAPPSD_USER=self.username, GRIDAPPSD_PASSWORD=self.password
                )

            else:
                assert fb["connection_args"]
                assert fb["connection_type"]

            # TODO: Error in gridappsd-python library the spelling is definately incorrect.
            fb["conneciton_args"] = fb.pop("connection_args")
            assert fb["id"]

            self.field_bus_def = MessageBusDefinition(**fb)


@dataclass
class ProgramList:
    name: str
    programs: list[m.DERProgram]


@dataclass
class ServerConfiguration:
    openssl_cnf: str

    tls_repository: str

    server: str
    port: int

    # Handle keep-alive settings
    connection_idle_timeout: int = 300  # 5 minutes default
    max_keep_alive_requests: int = 1000
    keep_alive_timeout: int = 60  # seconds

    service_name: str = "IEEE_2030_5"
    simulation_id: str | None = None

    ui_port: int | None = None

    include_default_der_on_all_devices: bool = True
    include_default_der_program_on_ders: bool = True

    default_program: m.DERProgram | None = None
    default_der_control: m.DefaultDERControl | None = None

    cleanse_storage: bool = True
    storage_path: str | None = None

    log_event_list_poll_rate: int = 900
    device_capability_poll_rate: int = 900
    mirror_usage_point_post_rate: int = 300
    end_device_list_poll_rate: int = 86400  # daily check-in

    # General poll and post rates from config
    poll_rate: int = 900  # Default poll rate for device capabilities (15 minutes)
    post_rate: int = 300  # Default post rate for mirror usage points (5 minutes)

    # Individual resource poll rates (defaults match _poll_rate values)
    device_capability: int = 900  # matches device_capability_poll_rate
    end_device_list: int = 86400  # matches end_device_list_poll_rate
    der_list: int = 900  # matches poll_rate
    der_program_list: int = 900  # matches poll_rate
    fsa_list: int = 900  # matches poll_rate
    mirror_usage_point: int = 300  # matches mirror_usage_point_post_rate
    usage_point: int = 900  # matches poll_rate
    registration: int = 900  # matches poll_rate
    log_event_list: int = 900  # matches log_event_list_poll_rate
    reading_set: int = 900  # matches poll_rate
    time: int = 900  # matches poll_rate

    generate_admin_cert: bool = False
    lfdi_client: str | None = None
    debug_client_traffic: bool = False  # Enable per-client request/response logging to files

    fsas: list[FSAConfiguration] = field(default_factory=list)
    programs: list[ProgramConfiguration] = field(default_factory=list)
    devices: list[DeviceConfiguration] = field(default_factory=list)
    ders: list[DERConfiguration] = field(default_factory=list)
    curves: list[CurveConfiguration] = field(default_factory=list)

    server_mode: Literal["enddevices_create_on_start"] | Literal["enddevices_register_access_only"] = (
        "enddevices_register_access_only"
    )

    lfdi_mode: Literal["lfdi_mode_from_file"] | Literal["lfdi_mode_from_cert_fingerprint"] = (
        "lfdi_mode_from_cert_fingerprint"
    )

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

    proxy_hostname: str | None = None
    proxy_enabled: bool = False
    proxy_debug: bool = False

    # Dual server configuration for HTTP admin access
    dual_server_enabled: bool = False
    admin_http_port: int = 5001

    gridappsd: GridappsdConfiguration | None = None
    # DefaultDERControl: Optional[DefaultDERControl] = None
    # DERControlList: Optional[DERControl] = field(default=list)

    # Database backend configuration
    database_backend: str = "zodb"  # Options: "zodb" or "sqlite"
    database_path: Path | None = None  # Optional custom path for database file

    # ZODB configuration (used when database_backend = "zodb")
    zodb_path: Path | None = None
    zodb_pool_size: int = 7
    zodb_cache_size: int = 10000
    zodb_pack_interval_hours: int = 24

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
        if self.zodb_path is None:
            self.zodb_path = Path("~/.ieee_2030_5_data/main.fs").expanduser()

        if self.devices is None:
            self.devices = []
        else:
            self.devices = [DeviceConfiguration.from_dict(x) for x in self.devices]

        if self.default_program:
            # Get DefaultDERControl off of the default program and bulid the base.
            if "DefaultDERControl" in self.default_program:
                self.default_der_control = m.DefaultDERControl(
                    **{
                        k: v
                        for k, v in self.default_program.items()
                        if k in inspect.signature(m.DefaultDERControl).parameters
                    }
                )

                if "DERControlBase" in self.default_program["DefaultDERControl"]:
                    cb = self.default_program["DefaultDERControl"]["DERControlBase"]
                    self.default_der_control.DERControlBase = m.DERControlBase(
                        **{k: v for k, v in cb.items() if k in inspect.signature(m.DERControlBase).parameters}
                    )

            # Populate from the default_program dictionary the keys of the configuration file.
            self.default_program = m.DERProgram(
                **{k: v for k, v in self.default_program.items() if k in inspect.signature(m.DERProgram).parameters}
            )

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
            if d.id is not None:
                test_lfdi = tls_repo.lfdi(d.id)
                if test_lfdi == int(lfdi):
                    if d.pin is not None:
                        return d.pin
                    else:
                        raise NotFoundError(f"Device {lfdi} found but has no PIN configured.")
        raise NotFoundError(f"The device_id: {lfdi} was not found.")
