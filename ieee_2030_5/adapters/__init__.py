import inspect
import logging
import typing
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from blinker import Signal

import ieee_2030_5.config as cfg
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models.sep import List_type

_log = logging.getLogger(__name__)


class ReturnCode(Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400


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

class AdapterIndexProtocol(Protocol):
    
    def fetch_at(self, index: int) -> m.Resource:
        pass


class AdapterListProtocol(AdapterIndexProtocol):
    def fetch_list(self, start: int = 0, after: int =0, limit:int = 0) -> m.List_type:
        pass
    
    def fetch_edev_all(self) -> List:
        pass
        

ready_signal = Signal("ready-signal")

class BaseAdapter:
    __count__: int = 0
    __server_configuration__: cfg.ServerConfiguration
    __tls_repository__: cfg.TLSRepository = None
    __lfdi__mapped_configuration__: Dict[str, cfg.DeviceConfiguration] = {}
    after_initialized = Signal('after-initialized')
        
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
    def ready(cls) -> Signal:
        return Signal("ready")

    @classmethod
    def get_current_index(cls) -> int:
        return cls.__count__

    @staticmethod
    def server_config() -> cfg.ServerConfiguration:
        return BaseAdapter.__server_configuration__

    @staticmethod
    def device_configs() -> List[cfg.DeviceConfiguration]:
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

        #BaseAdapter.after_initialized.send(BaseAdapter)
        ready_signal.send(BaseAdapter)
        # BaseAdapter.ready().send(BaseAdapter)
        # Find subclasses of us and initialize them calling _initalize method
        # TODO make this non static
        #EndDeviceAdapter._initialize()

    @staticmethod
    def build(**kwargs) -> dataclass:
        raise NotImplementedError()

    @staticmethod
    def store(value: dataclass) -> dataclass:
        raise NotImplementedError()

    @staticmethod
    def build_instance(cls, cfg_dict: Dict, signature_cls=None) -> object:
        if signature_cls is None:
            signature_cls = cls
        return cls(**{
            k: v
            for k, v in cfg_dict.items() if k in inspect.signature(signature_cls).parameters
        })

from ieee_2030_5.adapters.dcap import DeviceCapabilityAdapter
from ieee_2030_5.adapters.der import (DERAdapter, DERControlAdapter,
                                      DERCurveAdapter, DERProgramAdapter)
from ieee_2030_5.adapters.enddevices import EndDeviceAdapter
from ieee_2030_5.adapters.log import LogAdapter
from ieee_2030_5.adapters.mupupt import MirrorUsagePointAdapter
