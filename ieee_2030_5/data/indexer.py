from dataclasses import field, dataclass
from typing import Dict

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Index:
    index: int
    href: str
    item: dataclass


class Indexer:
    __items__: Dict[str, Index] = {}

    def add(self, index:int, href: str, item: dataclass):
        cached = self.__items__.get(href)
        if cached and cached.item == item:
            cached.index = index
        else:
            self.__items__[href] = Index(index, href, item)
