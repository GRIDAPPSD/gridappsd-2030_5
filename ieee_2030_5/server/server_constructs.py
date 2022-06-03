from __future__ import annotations

from uuid import uuid4
from dataclasses import dataclass, field
from enum import Flag, auto
import logging
from typing import Dict, Optional, List

import werkzeug
from flask import request

from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.models import (
    EndDevice,
    DERProgram,
    DERProgramList,
    ActiveDERControlListLink,
    DefaultDERControlLink,
    DERControlListLink,
    DERCurveListLink)

_log = logging.getLogger(__name__)


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
