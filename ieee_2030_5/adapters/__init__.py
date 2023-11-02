from __future__ import annotations
import os

import inspect
from pprint import pprint
import logging
import typing
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import (Any, ClassVar, Dict, Generic, List, Optional, Protocol, Type, TypeVar, Union,
                    get_args, get_origin)

import yaml
from blinker import Signal

import ieee_2030_5.config as cfg
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository

_log = logging.getLogger(__name__)


class AlreadyExists(Exception):
    pass


class NotFoundError(Exception):
    pass


load_event = Signal("load-store-event")
store_event = Signal("store-data-event")


def __get_store__(store_name: str) -> Path:
    if cfg.ServerConfiguration.storage_path is None:
        cfg.ServerConfiguration.storage_path = Path("data_store")
    elif isinstance(cfg.ServerConfiguration.storage_path, str):
        cfg.ServerConfiguration.storage_path = Path(cfg.ServerConfiguration.storage_path)

    store_path = cfg.ServerConfiguration.storage_path
    store_path.mkdir(parents=True, exist_ok=True)
    store_path = store_path / f"{store_name}.yml"

    return store_path


def do_load_event(caller: Union[Adapter, ResourceListAdapter]) -> None:
    """Load an adaptor type from the data_store path.


    """
    store_file = None
    if isinstance(caller, Adapter):
        _log.debug(f"Loading store {caller.generic_type_name}")
        store_file = __get_store__(caller.generic_type_name)
    elif isinstance(caller, ResourceListAdapter):
        store_file = __get_store__(caller.__class__.__name__)
    else:
        raise ValueError(f"Invalid caller type {type(caller)}")

    if not store_file.exists():
        _log.debug(f"Store {store_file.as_posix()} does not exist at present.")
        return

    # Load from yaml unsafe values etc.
    with open(store_file, "r") as f:
        items = yaml.load(f, Loader=yaml.UnsafeLoader)

        caller.__dict__.update(items)

    _log.debug(f"Loaded {caller.count} items from store")


def do_save_event(caller: Union[Adapter, ResourceListAdapter]) -> None:

    store_file = None
    if isinstance(caller, Adapter):
        _log.debug(f"Loading store {caller.generic_type_name}")
        store_file = __get_store__(caller.generic_type_name)
        _log.debug(f"Storing: {caller.generic_type_name}")
    elif isinstance(caller, ResourceListAdapter):
        store_file = __get_store__(caller.__class__.__name__)
    else:
        raise ValueError(f"Invalid caller type {type(caller)}")

    with open(store_file, 'w') as f:
        yaml.dump(caller.__dict__, f, default_flow_style=False, allow_unicode=True)


load_event.connect(do_load_event)
store_event.connect(do_save_event)


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

    def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.List_type:
        pass

    def fetch_edev_all(self) -> List:
        pass


ready_signal = Signal("ready-signal")

T = TypeVar('T')
C = TypeVar('C')
D = TypeVar('D')


class ResourceListAdapter:
    """
    A generic list adapter class for storing and retrieving lists of objects of a specific type. The adapter is
    initialized with an empty list of URLs and an empty dictionary of list containers. The adapter provides methods for
    adding URLs to the list, retrieving lists of objects from the adapter, and registering types for use with the
    adapter. The adapter also provides a `load_event` signal that is emitted when the adapter is loaded.

    :ivar _list_urls: A list of URLs for the adapter
    :vartype _list_urls: list
    :ivar _list_containers: A dictionary of list containers, indexed by URL
    :vartype _list_containers: dict
    :ivar _types: A dictionary of types registered with the adapter, indexed by type name
    :vartype _types: dict
    """

    def __init__(self):
        self._list_urls = []
        self._container_dict: Dict[str, Dict[int, D]] = {}
        self._types: Dict[str, D] = {}
        if not os.environ.get('IEEE_ADAPTER_IGNORE_INITIAL_LOAD'):
            _log.debug(f"Intializing adapter {self.__class__.__name__}")
            load_event.send(self)
        else:
            _log.debug(
                f"Skip loading initial store due to IEEE_ADAPTER_IGNORE_INITIAL_LOAD being set")

    def list_size(self, list_uri: str) -> int:
        alist = self._container_dict.get(list_uri, [])
        return len(alist)

    def count(self) -> int:
        count_of = 0
        for v in self._container_dict.values():
            count_of += len(v)
        return count_of

    def get_type(self, list_uri: str) -> D:
        return self._types.get(list_uri)

    def initialize_uri(self, list_uri: str, obj: D):
        if self._container_dict.get(list_uri) and self._types.get(list_uri) != obj:
            _log.error("Must initialize before container has any items.")
            raise ValueError("Must initialize before container has any items.")
        self._types[list_uri] = obj

    def append(self, list_uri: str, obj: D):
        """
        Appends an object to a list container in the adapter. If the list container does not exist, it is created. If the
        list container exists but has not been initialized with a type, the type of the object is used to initialize the
        list container. If the list container exists and has been initialized with a type, the type of the object is checked
        against the initialized type, and an astsertion error is raised if they do not match.

        :param list_uri: The URI of the list container
        :type list_uri: str
        :param obj: The object to append to the list container
        :type obj: Generic[D] or DList container
        :raises AssertionError: If the type of the object does not match the initialized type of the list container
        """
        cls = obj.__class__
        if issubclass(cls, (m.List_type, m.SubscribableList)):
            expected_type = eval(f'm.{cls.__name__[:cls.__name__.find("List")]}')

            if self._types.get(list_uri) is not None:
                raise ValueError(f"List for {list_uri} has already been initialized")

            self._types[list_uri] = expected_type

            # Recurse over the list appending to the end for each in the list
            for ele in getattr(obj, expected_type.__name__):
                self.append(list_uri, ele)

            # Exit here as all of the sub-items have been added now.
            return

        else:    # if there is a type
            expected_type = self._types.get(list_uri)

        if expected_type:
            if not isinstance(obj, expected_type):
                raise ValueError(f"Object {obj} is not of type {expected_type.__name__}")
        else:
            self.initialize_uri(list_uri, obj.__class__)

        if list_uri not in self._container_dict:
            self._container_dict[list_uri] = {}
        self._container_dict[list_uri][len(self._container_dict[list_uri])] = obj
        store_event.send(self)

    def get_by_mrid(self, list_uri: str, mrid: str) -> Optional[T]:
        return self.get_item_by_prop(list_uri, "mRID", mrid)

    def get_item_by_prop(self, list_uri: str, prop: str, value: Any) -> D:
        for item in self._container_dict.get(list_uri, {}).values():
            if getattr(item, prop) == value:
                return item
        raise NotFoundError(f"Uri {list_uri} does not contain {prop} == {value}")

    def has_list(self, list_uri: str) -> bool:
        return list_uri in self._container_dict

    def get_resource_list(self,
                          list_uri: str,
                          start: int = 0,
                          after: int = 0,
                          limit: int = 0,
                          sort_by: List[str] = [],
                          reverse: bool = False) -> Union[m.List_type, m.SubscribableList]:
        if isinstance(sort_by, str):
            sort_by = [sort_by]
        cls = self.get_type(list_uri)
        if cls is None:
            raise KeyError(f"Resource list {list_uri} not found in adapter")

        thelist = eval(f"m.{cls.__name__}List()")
        try:
            thecontainerlist = list(self._container_dict[list_uri].values())
            for sort in sort_by:
                subobj = sort.split('.')
                if len(subobj) == 2:
                    try:
                        thecontainerlist = sorted(
                            thecontainerlist,
                            key=lambda o: getattr(getattr(o, subobj[0]), subobj[1]),
                            reverse=reverse)
                    except AttributeError:
                        # happens when value is none
                        pass
                elif len(subobj) == 1:
                    thecontainerlist = sorted(thecontainerlist,
                                              key=lambda o: getattr(o, sort),
                                              reverse=reverse)
                else:
                    raise ValueError("Can only sort through single nested properties.")
                # if "." in sort:

                # thecontainerlist = sorted(thecontainerlist, key=sort)
            thelist.href = list_uri
            thelist.all = len(thecontainerlist)
            if start == after == limit == 0:
                setattr(thelist, cls.__name__, thecontainerlist)
            else:
                posx = start + after
                setattr(thelist, cls.__name__, thecontainerlist[posx:posx + limit])
            thelist.results = len(getattr(thelist, cls.__name__))
        except KeyError:
            thelist.all = 0
            thelist.href = list_uri
            thelist.results = len(getattr(thelist, cls.__name__))
        return thelist

    def get_list(self, list_uri: str, start: int = 0, limit: int = 0, after: int = 0) -> D:
        if list_uri not in self._container_dict:
            raise KeyError(f"List {list_uri} not found in adapter")

        return list(self._container_dict[list_uri].values())

    def get(self, list_uri: str, key: int) -> D:
        if list_uri not in self._container_dict:
            raise KeyError(f"List {list_uri} not found in adapter")
        if not isinstance(key, int):
            key = int(key)

        try:
            return self._container_dict[list_uri][key]
        except KeyError:
            raise NotFoundError(f"Key {key} not found in list {list_uri}")

    def set(self, list_uri: str, key: int, value: D, overwrite: bool = True) -> D:
        if list_uri not in self._container_dict:
            raise KeyError(f"List {list_uri} not found in adapter")

        if key in self._container_dict[list_uri] and not overwrite:
            raise AlreadyExists(
                f"Key {key} already exists in list {list_uri} but overwrite not set to True")

        self._container_dict[list_uri][key] = value
        store_event.send(self)

    def store(self):
        store_event.send(self)

    def get_values(self, list_uri: str, sort_by: Optional[str] = None) -> List[D]:
        raise ValueError("Hmmmmm refactoring.")
        cpy = deepcopy(list(self._container_dict[list_uri].values()))
        if sort_by is not None:
            return sorted(cpy, key=lambda x: getattr(x, sort_by))
        else:
            return cpy

    def remove(self, list_uri: str, index: int):
        del self._container_dict[list_uri][index]
        store_event.send(self)

    def render_container(self, list_uri: str, instance: object, prop: str):
        setattr(instance, prop, deepcopy(self._container_dict[list_uri]))

    def print_container(self, list_uri: str):
        pprint(self._container_dict[list_uri])

    def print_all(self):

        for k in sorted(self._container_dict.keys()):
            print("K:", k)
            for index, v in self._container_dict[k].items():
                print("index:", index)
                pprint(v.__dict__)
            #pprint(self._container_dict[k].)

    def clear_all(self):
        self._container_dict.clear()
        self._list_urls.clear()
        self._types.clear()

    def clear(self, list_uri: str):
        if list_uri in self._container_dict:
            self._container_dict[list_uri].clear()
            self._list_urls[list_uri].clear()
            self._types[list_uri].clear()


class Adapter(Generic[T]):
    """
    A generic adapter class for storing and retrieving objects of a specific type. The adapter is initialized with a
    URL prefix and a generic type parameter. The adapter maintains an internal dictionary of objects, indexed by an
    integer ID. The adapter provides methods for adding, updating, and deleting objects, as well as retrieving objects
    by ID or by a custom filter function. The adapter also provides a `count` property that returns the number of
    objects currently stored in the adapter.

    :param url_prefix: The URL prefix for the adapter
    :type url_prefix: str
    :param kwargs: Additional keyword arguments
    :type kwargs: dict
    :raises ValueError: If the `generic_type` parameter is missing from `kwargs`
    """

    def __init__(self, url_prefix: str, **kwargs):
        if "generic_type" not in kwargs:
            raise ValueError("Missing generic_type parameter")
        self._generic_type: Type = kwargs['generic_type']
        self._href_prefix: str = url_prefix
        self._current_index: int = -1
        self._item_list: Dict[int, T] = {}
        if not os.environ.get('IEEE_ADAPTER_IGNORE_INITIAL_LOAD'):
            _log.debug(f"Intializing adapter {self.generic_type_name}")
            load_event.send(self)
        else:
            _log.debug(
                f"Skip loading initial store due to IEEE_ADAPTER_IGNORE_INITIAL_LOAD being set")

    @property
    def count(self) -> int:
        return len(self._item_list)

    @property
    def generic_type_name(self) -> str:
        return self._generic_type.__name__

    @property
    def href_prefix(self) -> str:
        return self._href_prefix

    @property
    def href(self) -> str:
        return self._href_prefix

    @href.setter
    def href(self, value: str) -> None:
        self._href_prefix = value

    def clear(self) -> None:
        self._current_index = -1
        self._item_list: Dict[int, T] = {}
        store_event.send(self)

    def fetch_by_mrid(self, mrid: str) -> Optional[T]:
        return self.fetch_by_property("mRID", mrid)

    def fetch_by_href(self, href: str) -> Optional[T]:
        return self.fetch_by_property("href", href)

    def fetch_by_property(self, prop: str, prop_value: Any) -> Optional[T]:
        for obj in self._item_list.values():
            # Most properties are pointers to other objects so we are going to
            # check both the property and the sub object property here, because
            # that should save some of the time later when we are looking for
            # hrefs and and can't get to them because they are wrapped in a
            # Link object.
            under_test = getattr(obj, prop)
            if isinstance(under_test, str):
                if under_test == prop_value:
                    return obj
            else:
                if getattr(under_test, prop) == prop_value:
                    return obj

    def add(self, item: T) -> T:
        if not isinstance(item, self._generic_type):
            raise ValueError(f"Item {item} is not of type {self._generic_type}")

        # Only replace if href is specified.
        if hasattr(item, 'href') and getattr(item, 'href') is None:
            setattr(item, 'href', hrefs.SEP.join([self._href_prefix,
                                                  str(self._current_index + 1)]))
        self._current_index += 1
        self._item_list[self._current_index] = item

        store_event.send(self)
        return item

    def fetch_all(self,
                  container: Optional[D] = None,
                  start: int = 0,
                  after: int = 0,
                  limit: int = 1) -> D:

        if container is not None:
            if not container.__class__.__name__.endswith("List"):
                raise ValueError("Must have List as the last portion of the name for instance")

            prop_found = container.__class__.__name__[:container.__class__.__name__.find("List")]

            items = list(self._item_list.values())
            all_len = len(items)
            all_results = len(items)
            all_items = items

            if start > len(items):
                all_items = []
                all_results = 0
            else:
                if limit == 0:
                    all_items = items[start:]
                else:
                    all_items = items[start:start + limit]
                all_results = len(all_items)

            setattr(container, prop_found, all_items)
            setattr(container, "all", all_len)
            setattr(container, "results", all_results)
        else:
            container = list(self._item_list.values())

        return container

    def fetch_index(self, obj: T, using_prop: str = None) -> int:
        found_index = -1
        for index, obj1 in self._item_list.items():
            if using_prop is None:
                if obj1 == obj:
                    found_index = index
                    break
            else:
                if getattr(obj, using_prop) == getattr(obj1, using_prop):
                    found_index = index
                    break
        if found_index == -1:
            raise KeyError(f"Object {obj} not found in adapter")
        return found_index

    def fetch(self, index: int):
        return self._item_list[index]

    def put(self, index: int, obj: T):
        self._item_list[index] = obj
        store_event.send(self)

    def fetch_by_mrid(self, mRID: str):
        for item in self._item_list.values():
            if not hasattr(item, 'mRID'):
                raise ValueError(f"Item of {type(T)} does not have mRID property")
            if item.mRID == mRID:
                return item

        raise KeyError(f"mRID ({mRID}) not found.")

    def size(self) -> int:
        return len(self._item_list)

    def __len__(self) -> int:
        return len(self._item_list)

    def store(self):
        store_event.send(self)


from ieee_2030_5.adapters.adapters import (DERAdapter, DERControlAdapter, DERCurveAdapter,
                                           DERProgramAdapter, DeviceCapabilityAdapter,
                                           EndDeviceAdapter, FunctionSetAssignmentsAdapter,
                                           RegistrationAdapter, MirrorUsagePointAdapter,
                                           UsagePointAdapter, TimeAdapter, ListAdapter,
                                           create_mirror_usage_point, create_mirror_meter_reading)

__all__ = [
    'DERControlAdapter', 'DERCurveAdapter', 'DERProgramAdapter', 'DeviceCapabilityAdapter',
    'EndDeviceAdapter', 'FunctionSetAssignmentsAdapter', 'RegistrationAdapter', 'DERAdapter',
    'MirrorUsagePointAdapter', 'TimeAdapter', 'UsagePointAdapter', 'create_mirror_usage_point',
    'create_mirror_meter_reading', 'ListAdapter'
]


def clear_all_adapters():
    for adpt in __all__:
        obj = eval(adpt)
        if isinstance(obj, Adapter):
            obj.clear()
        elif isinstance(obj, ResourceListAdapter):
            obj.clear_all()


# from ieee_2030_5.adapters.log import LogAdapter
# from ieee_2030_5.adapters.mupupt import MirrorUsagePointAdapter
