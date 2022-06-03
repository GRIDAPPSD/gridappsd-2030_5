import inspect
from dataclasses import dataclass
from typing import List, Literal, Union

__all__ = ["ServerConfiguration"]

from ieee_2030_5.models import DeviceCategoryType


@dataclass
class DeviceConfiguration:
    id: str
    ip: str
    hostname: str
    device_category_type: DeviceCategoryType

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __hash__(self):
        return self.id.__hash__()


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

    @classmethod
    def from_dict(cls, env):
        return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})

    def __post_init__(self):
        self.devices = [DeviceConfiguration.from_dict(x) for x in self.devices]
        for d in self.devices:
            d.device_category_type = eval(f"DeviceCategoryType.{d.device_category_type}")

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
