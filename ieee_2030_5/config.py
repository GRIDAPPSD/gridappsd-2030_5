from typing import Any, Tuple, Dict, List, Literal, Union

import yaml
from icecream import ic
from pydantic import BaseSettings, Field, Extra, BaseModel
from pydantic.env_settings import SettingsSourceCallable

__all__ = ["ServerConfiguration"]

from ieee_2030_5.models import DeviceCategoryType


class DeviceConfiguration(BaseModel):
    id: str
    ip: str
    hostname: str
    device_category_type: DeviceCategoryType

    class Config:
        extra = Extra.allow


class ServerConfiguration(BaseSettings):
    openssl_cnf: str
    # Can include ip address as well
    server_hostname: str
    server_mode: Union[Literal["enddevices_create_on_start"],
                       Literal["enddevices_register_access_only"]] = "enddevices_create_on_start"
    devices: List[DeviceConfiguration]
    tls_repository: str
    openssl_cnf: str

    class Config:
        extra = Extra.allow
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

if __name__ == '__main__':
    cfgfile_text = """
devices:
- bus: m2001-ess1
  hostname: 6F33B5DD-50CD-4599-8559-3299BC22D9F0
  id: 6F33B5DD-50CD-4599-8559-3299BC22D9F0
  ip: 127.0.0.2
  ipu: '1.1111111'
  name: battery1
  p: 0.0
  phases: ''
  q: 0.0
  ratedE: 500000.0
  ratedS: 250000.0
  ratedU: 12470.0
  state: Waiting
  storedE: 500000.0
openssl_cnf: openssl.cnf
server: 0.0.0.0
server_mode: create_devices   # create_devices or register_only
tls_repository: ~/tls
"""
    cfg = yaml.safe_load(cfgfile_text)

    settings = Settings(cfg)
    print(settings)
