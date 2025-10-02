from __future__ import annotations

import logging
import pickle
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import format_datetime

from ieee_2030_5.models.sep import Link
from ieee_2030_5.persistance.points import get_point, set_point

__all__: list[str] = ["get_href", "add_href", "get_href_all_names", "get_href_filtered"]

_log = logging.getLogger(__name__)


@dataclass
class Index:
    href: str
    item: object
    added: str  # Optional[Union[datetime | str]]
    last_written: str  # Optional[Union[datetime | str]]
    last_hash: int | None


@dataclass
class Indexer:
    __items__: dict = field(default=None)

    def init(self):
        if self.__items__ is None:
            self.__items__ = {}

    @property
    def length(self) -> int:
        self.init()
        return len(self.__items__)

    def add(self, href: str, item: dataclass):
        self.init()

        # TODO: Verify that this method actually works with a new object.
        # If using a link, we need the true href to cache the object.
        if isinstance(href, Link):
            href = href.href
        # cached = self.__items__.get(href)
        # if cached and cached.item == item:
        #     _log.debug(f"Item already cached {href}")
        # else:
        added = format_datetime(datetime.utcnow())
        serialized_item = pickle.dumps(item)  # serialize_dataclass(item, serialization_type=SerializeType.JSON)
        obj = Index(href, item, added=added, last_written=added, last_hash=hash(serialized_item))
        # serialized_obj = serialize_dataclass(obj, serialization_type=SerializeType.JSON)

        # note storing Index object.
        set_point(href, pickle.dumps(obj))  # serialize_dataclass(obj, serialization_type=SerializeType.JSON))
        self.__items__[href] = obj

    def get(self, href) -> dataclass:
        self.init()
        # If using a link, we need the true href to cache the object.
        if isinstance(href, Link):
            href = href.href

        # First check in-memory cache
        if href in self.__items__:
            data = self.__items__[href].item
        else:
            # If not in cache, check the database
            try:
                point_data = get_point(href)
                if point_data:
                    index = pickle.loads(point_data)
                    # Check if it's an Index object or raw data
                    if hasattr(index, "item"):
                        data = index.item
                        # Update in-memory cache
                        self.__items__[href] = index
                    else:
                        # Raw data - wrap it in an Index for consistency
                        data = index
                        from datetime import datetime
                        from email.utils import format_datetime

                        wrapped_index = Index(
                            href=href,
                            item=data,
                            added=format_datetime(datetime.utcnow()),
                            last_written=format_datetime(datetime.utcnow()),
                            last_hash=None,
                        )
                        self.__items__[href] = wrapped_index
                else:
                    data = None
            except Exception as e:
                _log.debug(f"Failed to get href {href} from database: {e}")
                data = None

        return data

    def get_all(self) -> list:
        return deepcopy([x.item for x in self.__items__.values()])


__indexer__ = Indexer()


def add_href(href: str, item: dataclass):
    __indexer__.add(href, item)


def get_href(href: str) -> dataclass:
    return __indexer__.get(href)


def get_href_filtered(href_prefix: str) -> list[dataclass] | []:
    if __indexer__.__items__ is None:
        return []

    return [v.item for k, v in __indexer__.__items__.items() if k.startswith(href_prefix) and v.item is not None]


def get_href_all_names():
    return [x for x in __indexer__.__items__.keys() if __indexer__.__items__[x] is not None]
