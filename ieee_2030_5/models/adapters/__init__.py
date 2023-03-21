from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Dict, Optional

import ieee_2030_5.config as cfg


class ReturnCode(Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400

class InvalidConfigFile(Exception):
    pass


def populate_from_kwargs(obj: object, **kwargs) -> Dict[str, Any]:

    if not is_dataclass(obj):
        raise ValueError(f"The passed object {obj} is not a dataclass.")

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

from ieee_2030_5.models.adapters.adapters import *
from ieee_2030_5.models.adapters.mupupt import MirrorUsagePointAdapter
