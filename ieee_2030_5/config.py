from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import List, Literal, Union, Optional, Dict, Tuple

import yaml
from dataclasses_json import dataclass_json

__all__ = ["ServerConfiguration"]

try:
    from gridappsd.field_interface import MessageBusDefinition
except ImportError as ex:
    pass

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models import DeviceCategoryType, DERProgram, DERCurve, DefaultDERControl, DERControlBase, CurveData, \
    FunctionSetAssignments
from ieee_2030_5.types_ import Lfdi

from ieee_2030_5.server.exceptions import NotFoundError


_log = logging.getLogger(__name__)


@dataclass
class DeviceConfiguration:
    id: str
    device_category_type: DeviceCategoryType
    pin: int
    hostname: str = None
    ip: str = None
    poll_rate: int = 900
    # TODO: Direct control means that only one FSA will be available to the client.
    direct_control: bool = True
    fsa_list: Optional[List[Dict]] = None
    DefaultDERControl: Optional[DefaultDERControl] = None

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.id.__hash__()


@dataclass_json
@dataclass
class GridappsdConfiguration:
    field_bus_config: Optional[str] = None
    field_bus_def: Optional[MessageBusDefinition] = None
    feeder_id_file: Optional[str] = None
    feeder_id: Optional[str] = None
    simulation_id_file: Optional[str] = None
    simulation_id: Optional[str] = None


@dataclass
class ProgramList:
    name: str
    programs: List[DERProgram]


@dataclass
class ServerConfiguration:
    openssl_cnf: str
    # Can include ip address as well
    server_hostname: str
    server_mode: Union[Literal["enddevices_create_on_start"],
                       Literal["enddevices_register_access_only"]]
    devices: List[DeviceConfiguration]

    tls_repository: str
    openssl_cnf: str

    # map into program_lists array for programs for specific
    # named list.
    programs_map: Dict[str, int] = field(default_factory=dict)
    program_lists: List[ProgramList] = field(default_factory=list)
    fsa_list: List[FunctionSetAssignments] = field(default_factory=list)
    curve_list: List[DERCurve] = field(default_factory=list)

    debug_device: Optional[str] = None
    proxy_hostname: Optional[str] = None
    gridappsd: Optional[GridappsdConfiguration] = None
    DefaultDERControl: Optional[DefaultDERControl] = None

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __post_init__(self):
        self.devices = [DeviceConfiguration.from_dict(x) for x in self.devices]
        for d in self.devices:
            d.device_category_type = eval(f"DeviceCategoryType.{d.device_category_type}")

        temp_program_list = self.program_lists
        if isinstance(self.program_lists, str):
            temp_program_list = yaml.safe_load(Path(self.program_lists).read_text())

        self.program_lists = []
        for program_list in temp_program_list['program_lists']:
            pl_obj = ProgramList(name=program_list["name"], programs=[])
            for inter_index, program_obj in enumerate(program_list['programs']):
                base = None
                if "DERControlBase" in program_obj:
                    base = DERControlBase()
                    for k in program_obj.get("DERControlBase"):
                        setattr(base, k, program_obj["DERControlBase"].get(k))
                    del program_obj["DERControlBase"]
                # TODO Do Something with base so we can retrieve it.
                # if base:
                #     self.DefaultDERControl = DefaultDERControl(DERControlBase=base)
                #     for k, v in program.items():
                #         setattr(self.DefaultDERControl, k, v)
                # else:
                program = DERProgram()

                for k, v in program_obj.items():
                    setattr(program, k, v)

                pl_obj.programs.append(program)
            self.program_lists.append(pl_obj)

        temp_curve_list = self.curve_list
        if isinstance(self.curve_list, str):
            temp_curve_list = yaml.safe_load(Path(self.curve_list).read_text())

        self.curve_list = []
        for item in temp_curve_list['curve_list']:
            curve_data: List[CurveData] = []
            for data in item.get('CurveData'):
                curve_data.append(CurveData(xvalue=data['xvalue'], yvalue=data['yvalue']))
            del item["CurveData"]

            curve = DERCurve(CurveData=curve_data)
            for k, v in item.items():
                setattr(curve, k, v)
            self.curve_list.append(curve)

        if self.gridappsd:
            self.gridappsd = GridappsdConfiguration.from_dict(self.gridappsd)
            if Path(self.gridappsd.feeder_id_file).exists():
                self.gridappsd.feeder_id = Path(self.gridappsd.feeder_id_file).read_text().strip()
            if Path(self.gridappsd.simulation_id_file).exists():
                self.gridappsd.simulation_id = Path(self.gridappsd.simulation_id_file).read_text().strip()

            if not self.gridappsd.feeder_id:
                raise ValueError("Feeder id from gridappsd not found in feeder_id_file nor was specified "
                                 "in gridappsd config section.")

            # TODO: This might not be the best place for this manipulation
            self.gridappsd.field_bus_def = MessageBusDefinition.load(self.gridappsd.field_bus_config)
            self.gridappsd.field_bus_def.id = self.gridappsd.feeder_id

            _log.info("Gridappsd Configuration For Simulation")
            _log.info(f"feeder id: {self.gridappsd.feeder_id}")
            if self.gridappsd.simulation_id:
                _log.info(f"simulation id: {self.gridappsd.simulation_id}")
            else:
                _log.info("no simulation id")
            _log.info("x" * 80)

        if self.debug_device:
            found = False
            for d in self.devices:
                if self.debug_device == d.id:
                    found = True
                    break
            if not found:
                raise ValueError("debug_device must be one of the devices available.")
        # if self.field_bus_config:
        #     self.field_bus_def = MessageBusDefinition.load(self.field_bus_config)

    def get_device_pin(self, lfdi: Lfdi, tls_repo: TLSRepository) -> int:
        for d in self.devices:
            test_lfdi = tls_repo.lfdi(d.id)
            if test_lfdi == int(lfdi):
                return d.pin
        raise NotFoundError(f"The device_id: {lfdi} was not found.")
