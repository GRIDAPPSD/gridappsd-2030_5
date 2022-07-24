from __future__ import annotations

import pickle
from dataclasses import dataclass, field

from datetime import datetime
from email.utils import format_datetime
from typing import Dict, Optional
from ieee_2030_5.persistance.points import set_point, get_point


@dataclass
class Index:
    href: str
    item: object
    added: str  #  Optional[Union[datetime | str]]
    last_written: str  #   Optional[Union[datetime | str]]
    last_hash: Optional[int]


@dataclass
class Indexer:
    __items__: Dict = field(default=None)

    def init(self):
        if self.__items__ is None:
            self.__items__ = {}

    def add(self, href: str, item: dataclass):
        self.init()

        cached = self.__items__.get(href)
        if cached and cached.item == item:
            pass
        else:
            added = format_datetime(datetime.utcnow())
            serialized_item = pickle.dumps(item)  # serialize_dataclass(item, serialization_type=SerializeType.JSON)
            obj = Index(href, item, added=added, last_written=added, last_hash=hash(serialized_item))
            # serialized_obj = serialize_dataclass(obj, serialization_type=SerializeType.JSON)

            # note storing Index object.
            set_point(href, pickle.dumps(obj))  #  serialize_dataclass(obj, serialization_type=SerializeType.JSON))
            self.__items__[href] = obj

    def get(self, href) -> dataclass:
        self.init()
        if href in self.__items__:
            index = pickle.loads(get_point(href)) # pickle.loads(get_point(href))
            # index = pickle.loads(self.__items__.get(href))
            #index = deserialize_dataclass(data, SerializeType.JSON)
            data = index.item
        else:
            data = None

        return data


__indexer__ = Indexer()


def add_href(href: str, item: dataclass):
    __indexer__.add(href, item)


def get_href(href: str) -> dataclass:
    return __indexer__.get(href)
