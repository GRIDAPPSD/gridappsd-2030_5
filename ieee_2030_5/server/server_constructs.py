from __future__ import annotations

from uuid import uuid4
from dataclasses import dataclass, field
from enum import Flag, auto
import logging
from typing import Dict, Optional, List

import werkzeug
from flask import request

from ieee_2030_5.models import (
    EndDevice,
    DERProgram,
    DERProgramList,
    ActiveDERControlListLink,
    DefaultDERControlLink,
    DERControlListLink,
    DERCurveListLink)

_log = logging.getLogger(__name__)


class AlreadyExistsError(Exception):
    pass


class GroupLevel(Flag):
    """
    Each group is a construct of the layer the EndDevice is
    apart of.
    """
    System = auto()
    SubTransmission = auto()
    Substation = auto()
    Feeder = auto()
    Segment = auto()
    Transformer = auto()
    ServicePoint = auto()
    NonTopology = auto()


class UUIDHandler:
    handler: UUIDHandler = None
    bag: dict = {}
    uuids: set = set()

    def __new__(cls):
        if UUIDHandler.handler is None:
            UUIDHandler.handler = super().__new__(cls)
        return UUIDHandler.handler

    def add_known(self, uuid: str, obj: object):
        assert isinstance(uuid, str) and obj is not None
        self.bag[uuid] = obj
        self.bag[id(obj)] = uuid
        self.uuids.add(uuid)

    def add(self, obj) -> str:
        """
        Add an object to the UUIDHandler.  If the object already exists
        in the collection then raise AlreadyExistsError

        :param: obj - The object to store in the handler.
        """
        if obj in self.bag:
            raise AlreadyExistsError(f"obj {obj} already exists in bag")

        new_uuid = str(uuid4())
        while new_uuid in self.uuids:
            new_uuid = str(uuid4())

        self.bag[new_uuid] = obj
        self.bag[id(obj)] = new_uuid
        self.uuids.add(new_uuid)
        return new_uuid

    def get_uuid(self, obj) -> Optional[str]:
        """
        Retrieve a uuid for a matching object.  If match exists the
        function returns the uuid, if not then returns None.

        :param: object An object to match.

        return: A string uuid or None
        """
        return self.bag.get(id(obj))

    def get_obj(self, uuid: str) -> Optional[object]:
        """
        Retrieve an object based on the passed uuid.  If match exists the
        function returns the object, if not then returns None.

        :param: str A uuid to match against.

        return: An object or None
        """
        return self.bag.get(uuid)

    def get_uuids(self) -> List[str]:
        return list(self.uuids.copy())


@dataclass
class Group:
    name: str
    description: str
    level: GroupLevel
    der_program: DERProgram
    _end_devices: Dict[bytes, EndDevice] = field(default_factory=dict)

    def add_end_device(self, end_device: EndDevice):
        self._end_devices[end_device.lFDI] = end_device

    def remove_end_device(self, end_device: EndDevice):
        self.remove_end_device_by_lfid(end_device.lFDI)

    def remove_end_device_by_lfid(self, lfid: bytes):
        del self._end_devices[lfid]

    def get_devices(self):
        return list(self._end_devices.values())


groups: Dict[GroupLevel, Group] = {}
der_programs: List[DERProgram] = []
uuid_handler: UUIDHandler = UUIDHandler()


def get_group(level: Optional[GroupLevel] = None, name: Optional[str] = None):

    if not level and not name:
        raise ValueError("level or name must be specified to this function.")

    # if name exists then override the level with NonTopology
    if name:
        level = GroupLevel.NonTopology

    grp = groups.get(level)

    if not grp:
        raise ValueError(f"Invalid level specified {level}")

    if name is not None and level:
        for g in groups.values():
            if g.name == name:
                grp = g
                break

    return grp


def create_group(level: GroupLevel, name: Optional[str] = None) -> Group:
    if level is GroupLevel.NonTopology and not name:
        raise ValueError("NonTopology level must have a name associated with it")

    if level is not GroupLevel.NonTopology:
        mrid = "B" + str(level.name.__hash__())
        name = level.name
    else:
        mrid = "B" + str(name.__hash__())

    index = len(groups) + 1

    # TODO: Standardize urls so we can get them from a central spot.
    program_href = f"/sep2/A{index}/derp/1"
    program = DERProgram(mRID=mrid.encode('utf-8'),
                         description=name,
                         primacy=index * 10,
                         href=program_href)
    program.active_dercontrol_list_link = ActiveDERControlListLink(href=f"{program_href}/actderc")
    program.default_dercontrol_link = DefaultDERControlLink(href=f"{program_href}/dderc")
    program.dercontrol_list_link = DERControlListLink(href=f"{program_href}/derc")
    program.dercurve_list_link = DERCurveListLink(href=f"{program_href}/dc")

    if level not in groups:
        groups[level] = Group(level=level, name=name, description=name, der_program=program)

    der_programs.append(program)
    uuid_handler.add_known(mrid, program)


# Create all but the NonTopology group, which will get added
for _, lvl in enumerate(GroupLevel):
    create_group(lvl, name=lvl.name)


der_program_list = DERProgramList(DERProgram=der_programs)


def get_der_program_list():
    return der_program_list


def get_groups() -> Dict[GroupLevel, Group]:
    return groups


class ServerOperation:

    def __init__(self):
        if 'ieee_2030_5_peercert' not in request.environ:
            raise werkzeug.exceptions.Forbidden()

    def head(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def get(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def post(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def delete(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def put(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def execute(self):
        methods = {
            'GET': self.get,
            'POST': self.post,
            'DELETE': self.delete,
            'PUT': self.put
        }
        _log.debug(f"Request method is {request.environ['REQUEST_METHOD']}")
        fn = methods.get(request.environ['REQUEST_METHOD'])
        if not fn:
            raise werkzeug.exceptions.MethodNotAllowed()

        return fn()


if __name__ == '__main__':
    print(get_groups())
    for x in der_program_list.DERProgram:
        print(x.href)

    for x, v in get_groups().items():
        print(x)
        print(v)

    create_group(name="foo")
    g = get_group(name="foo")
    assert GroupLevel.NonTopology == g.level
    assert "foo" == g.name
