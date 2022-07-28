from __future__ import annotations

import inspect
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List, Literal, Union, Optional, Dict

import yaml
from dataclasses_json import dataclass_json

__all__ = ["ServerConfiguration"]

from gridappsd.field_interface import MessageBusDefinition

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models import DeviceCategoryType, DERProgram, DERCurve, DefaultDERControl, DERControlBase, CurveData
from ieee_2030_5.types import Lfid

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

    # def from_dict(self, **kwargs) -> GridappsdConfiguration:
    #     schema = marshmallow_dataclass.class_schema(GridappsdConfiguration)
    #     return schema().load(kwargs)
        # if kwargs:
        #     return schema().load(init)
        # else:
        #     return GridappsdConfiguration()


@dataclass
class ServerConfiguration:
    openssl_cnf: str
    # Can include ip address as well
    server_hostname: str
    server_mode: Union[Literal["enddevices_create_on_start"],
                       Literal["enddevices_register_access_only"]]
    devices: List[DeviceConfiguration]
    program_list: List[DERProgram]
    curve_list: List[DERCurve]

    tls_repository: str
    openssl_cnf: str

    gridappsd: Optional[GridappsdConfiguration] = None
    DefaultDERControl: Optional[DefaultDERControl] = None

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __post_init__(self):
        self.devices = [DeviceConfiguration.from_dict(x) for x in self.devices]
        for d in self.devices:
            d.device_category_type = eval(f"DeviceCategoryType.{d.device_category_type}")

        temp_program_list = self.program_list
        if isinstance(self.program_list, str):
            temp_program_list = yaml.safe_load(Path(self.program_list).read_text())

        self.program_list = []
        for item in temp_program_list['der_program_list']:
            base = None
            if "DERControlBase" in item:
                base = DERControlBase()
                for k in item.get("DERControlBase"):
                    setattr(base, k, item.get(k))
                del item["DERControlBase"]

            if "default_der_control" in item:
                del item["default_der_control"]

                self.DefaultDERControl = DefaultDERControl(DERControlBase=base)
                for k, v in item.items():
                    setattr(self.DefaultDERControl, k, v)
            else:
                program = DERProgram()
                self.program_list.append(program)
                for k, v in item.items():
                    setattr(program, k, v)

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

        # if self.field_bus_config:
        #     self.field_bus_def = MessageBusDefinition.load(self.field_bus_config)

    def get_device_pin(self, lfid: Lfid, tls_repo: TLSRepository) -> int:
        for d in self.devices:
            test_lfid = tls_repo.lfdi(d.id)
            if test_lfid == int(lfid):
                return d.pin
        raise NotFoundError(f"The device_id: {lfid} was not found.")

    #
    # class Config:
    #     # env_prefix = "IEEE_2030_5_"
    #     extra = Extra.allow
    #
    #     @classmethod
    #     def customise_sources(
    #             cls,
    #             init_settings: SettingsSourceCallable,
    #             env_settings: SettingsSourceCallable,
    #             file_secret_settings: SettingsSourceCallable,
    #     ) -> Tuple[SettingsSourceCallable, ...]:
    #         # Add load from yml file, change priority and remove file secret option
    #         return init_settings, yml_config_setting, env_settings

# class ConfigObj:
#     def __init__(self, in_dict: dict):
#         assert isinstance(in_dict, dict)
#         for key, val in in_dict.items():
#             if isinstance(val, (list, tuple)):
#                 setattr(self, key, [ConfigObj(x) if isinstance(x, dict) else x for x in val])
#             else:
#                 setattr(self, key, ConfigObj(val) if isinstance(val, dict) else val)
