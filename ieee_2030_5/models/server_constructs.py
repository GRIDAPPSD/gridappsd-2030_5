from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Dict, Optional, List

from ieee_2030_5.models import EndDevice, Derprogram, DerprogramList, ActiveDercontrolListLink, DefaultDercontrolLink, \
    DercontrolListLink, DercurveListLink


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
    level: GroupLevel
    der_program: Derprogram
    _end_devices: Dict[bytes, EndDevice] = field(default_factory=dict)

    def add_end_device(self, end_device: EndDevice):
        self._end_devices[end_device.l_fdi] = end_device

    def remove_end_device(self, end_device: EndDevice):
        self.remove_end_device_by_lfid(end_device.l_fdi)

    def remove_end_device_by_lfid(self, lfid: bytes):
        del self._end_devices[lfid]

    def get_devices(self):
        return list(self._end_devices.values())


groups: Dict[GroupLevel, Group] = {}
der_programs: List[Derprogram] = []

for index, group in enumerate(GroupLevel):

    mrid = "B"+str(group.name.__hash__())
    # TODO: Standardize urls so we can get them from a central spot.
    program_href = f"/sep2/A{index+1}/derp/1"
    program = Derprogram(m_rid=mrid.encode('utf-8'),
                         description=group.name,
                         primacy=index * 10,
                         href=program_href)
    program.active_dercontrol_list_link = ActiveDercontrolListLink(href=f"{program_href}/actderc")
    program.default_dercontrol_link = DefaultDercontrolLink(href=f"{program_href}/dderc")
    program.dercontrol_list_link = DercontrolListLink(href=f"{program_href}/derc")
    program.dercurve_list_link = DercurveListLink(href=f"{program_href}/dc")

    groups[group] = Group(level=group, der_program=program)
    der_programs.append(program)

der_program_list = DerprogramList(derprogram=der_programs)


#
# groups: Dict[GroupLevel, Group] = {
#     GroupLevel.System: Group(level=GroupLevel.System.value,
#                              der_program=Derprogram(m_rid="B01000000".encode('utf-8'), description="SYS-A1")),
#     # GroupLevel.SubTransmission: Group(level=GroupLevel.SubTransmission.value),
#     # GroupLevel.Substation: Group(
#     #     level=GroupLevel.Substation.value),
#     # GroupLevel.Feeder: Group(
#     #     level=GroupLevel.Feeder.value,
#     #     ),
#     # GroupLevel.Segment: Group(
#     #     level=GroupLevel.Segment.value,
#     #     ),
#     # GroupLevel.Transformer: Group(
#     #     level=GroupLevel.Transformer.value,
#     #     ),
#     # GroupLevel.ServicePoint: Group(
#     #     level=GroupLevel.ServicePoint.value,),
#     # GroupLevel.NonTopology: Group(
#     #     level=GroupLevel.NonTopology),
# }


def get_groups() -> Dict[GroupLevel, Group]:
    return groups


if __name__ == '__main__':
    print(get_groups())
    for x in der_program_list.derprogram:
        print(x.href)

    for x, v in get_groups().items():
        print(x)
        print(v)
