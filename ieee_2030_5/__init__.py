from ieee_2030_5.config import ServerConfiguration, DeviceConfiguration
# from collections import namedtuple
from pathlib import Path
from typing import Union

PathStr = Union[Path, str]

__all__ = ['DeviceConfiguration', 'ServerConfiguration', 'PathStr']
