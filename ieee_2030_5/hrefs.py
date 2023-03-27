from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import List, NamedTuple, Optional

EDEV = "edev"
DCAP = "dcap"
UTP = "upt"
MUP = "mup"
DRP = "drp"
SDEV = "sdev"
MSG = "msg"
DER = "der"
CURVE = "dc"
PROGRAM = "program"
RSPS = "rsps"
LOG = "log"
DERC = "derc"
DDERC = "dderc"
FSA = "fsa"
DERP = "derp"

DEFAULT_DCAP_ROOT = f"/{DCAP}"
DEFAULT_EDEV_ROOT = f"/{EDEV}"
DEFAULT_UPT_ROOT = f"/{UTP}"
DEFAULT_MUP_ROOT = f"/{MUP}"
DEFAULT_DRP_ROOT = f"/{DRP}"
DEFAULT_SELF_ROOT = f"/{SDEV}"
DEFAULT_MESSAGE_ROOT = f"/{MSG}"
DEFAULT_DER_ROOT = f"/{DER}"
DEFAULT_CURVE_ROOT = f"/{CURVE}"
DEFAULT_PROGRAM_ROOT = f"/{PROGRAM}"
DEFAULT_RSPS_ROOT = f"/{RSPS}"
DEFAULT_LOG_EVENT_ROOT = f"/{LOG}"
DEFAULT_FSA_ROOT = f"/{FSA}"
DEFAULT_DERP_ROOT = f"/{DERP}"

SEP = "_"
MATCH_REG = "[a-zA-Z0-9_]*"

# Used as a sentinal value when we only want the href of the root
NO_INDEX = -1

class DERSubType(Enum):
    Capability = "dercap"
    Settings = "derg"
    Status = "ders"
    Availability = "dera"
    CurrentProgram = "derp"
    
    

@lru_cache()
def get_server_config_href() -> str:
    return "/server/cfg"


@lru_cache()
def get_enddevice_list_href() -> str:
    return DEFAULT_EDEV_ROOT

@lru_cache()
def curve_href(index: int = NO_INDEX) -> str:
    if index == NO_INDEX:
        return DEFAULT_CURVE_ROOT
    
    return SEP.join([DEFAULT_CURVE_ROOT, str(index)])

@lru_cache()
def fsa_href(index: int = NO_INDEX, edev_index: int=NO_INDEX):
    if index == NO_INDEX and edev_index == NO_INDEX:
        return DEFAULT_FSA_ROOT
    elif index != NO_INDEX and edev_index == NO_INDEX:
        return SEP.join([DEFAULT_FSA_ROOT, str(index)])
    elif index == NO_INDEX and edev_index != NO_INDEX:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), FSA])
    else:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), FSA, str(index)])
    
def der_href(index: int = NO_INDEX, fsa_index: int = NO_INDEX, edev_index: int = NO_INDEX):
    if index == NO_INDEX and fsa_index == NO_INDEX and edev_index == NO_INDEX:
        return DEFAULT_DER_ROOT
    elif index != NO_INDEX and fsa_index == NO_INDEX and edev_index == NO_INDEX:
        return SEP.join([DEFAULT_DER_ROOT, str(index)])
    elif index == NO_INDEX and fsa_index != NO_INDEX and edev_index == NO_INDEX:
        return SEP.join([DEFAULT_FSA_ROOT, str(fsa_index), DERP])
    elif edev_index != NO_INDEX and fsa_index == NO_INDEX and index == NO_INDEX:
        return SEP.join([DEFAULT_EDEV_ROOT, int(edev_index), FSA])
    elif edev_index != NO_INDEX and fsa_index != NO_INDEX and index == NO_INDEX:
        return SEP.join([DEFAULT_EDEV_ROOT, int(edev_index), FSA, int(fsa_index)])
    else:
        raise ValueError(f"index={index}, fsa_index={fsa_index}, edev_index={edev_index}")
    
def edev_der_href(edev_index: int, der_index: int = NO_INDEX) -> str:
    if der_index == NO_INDEX:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), DER])
    return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), DER, str(der_index)])

class EdevHref(NamedTuple):
    edev_index: int
    der_index: int = NO_INDEX
    der_sub: DERSubType = None
    
def edev_parse(path: str) -> EdevHref:
    split_pth = path.split(SEP)
    
    if len(split_pth) == 1:
        return EdevHref(NO_INDEX)
    elif len(split_pth) == 2:
        return EdevHref(int(split_pth[1]))
    elif len(split_pth) == 3:
        return EdevHref(int(split_pth[1]))
    elif len(split_pth) == 4:
        return EdevHref(int(split_pth[1]), int(split_pth[3]))
    elif len(split_pth) == 5:
        return EdevHref(int(split_pth[1]), int(split_pth[3]), split_pth[4])
    
    
def der_sub_href(edev_index: int, index: int = NO_INDEX, subtype: DERSubType = None):
    if subtype is None and index == NO_INDEX:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), DER])
    elif subtype is None:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), DER, str(index)])
    else:
        return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), DER, str(index), subtype.value])
    
@lru_cache()    
def mirror_usage_point_href(mirror_usage_point_index: int = NO_INDEX):
    """Mirror Usage Point hrefs
    
       /mup
       /mup/{mirror_usage_point_index}
       
    
    """
    if mirror_usage_point_index == NO_INDEX:
        ret = DEFAULT_MUP_ROOT
    else:
        ret = SEP.join([DEFAULT_MUP_ROOT, str(mirror_usage_point_index)])
    
    return ret

@dataclass
class UsagePointHref:
    usage_point_index: int= NO_INDEX
    meter_reading_list_index: int= NO_INDEX
    meter_reading_index: int= NO_INDEX
    reading_set_index: int= NO_INDEX
    reading_index: int= NO_INDEX
    
    @staticmethod
    def parse(href: str) -> UsagePointHref:
        items = href.split(SEP)
        if len(items) == 1:
            return UsagePointHref()
        
        if len(items) == 2:
            return UsagePointHref(usage_point_index = int(items[1]))

@dataclass
class MirrorUsagePointHref:
    mirror_usage_point_index: int = NO_INDEX
    meter_reading_list_index: int= NO_INDEX
    meter_reading_index: int= NO_INDEX
    reading_set_index: int= NO_INDEX
    reading_index: int= NO_INDEX
    
    @staticmethod
    def parse(href: str) -> MirrorUsagePointHref:
        items = href.split(SEP)
        if len(items) == 1:
            return MirrorUsagePointHref()
        
        if len(items) == 2:
            return MirrorUsagePointHref(items[1])
            

def usage_point_href(usage_point_index: int | str = NO_INDEX,
                     meter_reading_list: bool = False,
                     meter_reading_list_index: int = NO_INDEX,
                     meter_reading_index: int = NO_INDEX,
                     meter_reading_type: bool = False,
                     reading_set: bool = False,
                     reading_set_index: int = NO_INDEX,
                     reading_index: int = NO_INDEX):
    """Usage point hrefs 

       /upt
       /upt/{usage_point_index}
       /upt/{usage_point_index}/mr
       /upt/{usage_point_index}/mr/{meter_reading_index}
       /upt/{usage_point_index}/mr/{meter_reading_index}/rt
       /upt/{usage_point_index}/mr/{meter_reading_index}/rs
       /upt/{usage_point_index}/mr/{meter_reading_index}/rs/{reading_set_index}
       /upt/{usage_point_index}/mr/{meter_reading_index}/rs/{reading_set_index}/r
       /upt/{usage_point_index}/mr/{meter_reading_index}/rs/{reading_set_index}/r/{reading_index}
       
       

    """
    if isinstance(usage_point_index, str):
        base_upt = usage_point_index
    else:
        base_upt = DEFAULT_UPT_ROOT
        
    if usage_point_index == NO_INDEX:
        ret = base_upt        
    else:
        if isinstance(usage_point_index, str):
            arr = [base_upt]
        else:
            arr = [DEFAULT_UPT_ROOT, str(usage_point_index)]
            
        if meter_reading_list:
            if meter_reading_list_index == NO_INDEX:
                arr.extend(["mr"])
            else:
                arr.extend(["mr", str(meter_reading_list_index)])
                
                
        
        ret = SEP.join(arr)
    return ret


def get_der_program_list(fsa_href: str) -> str:
    return SEP.join([fsa_href, "der"])


def get_dr_program_list(fsa_href: str) -> str:
    return SEP.join([fsa_href, "dr"])


def get_fsa_list_href(end_device_href: str) -> str:
    return SEP.join([end_device_href, "fsa"])


def get_response_set_href():
    return DEFAULT_RSPS_ROOT


@lru_cache()
def get_der_list_href(index: int) -> str:
    if index == NO_INDEX:
        ret = DEFAULT_DER_ROOT
    else:
        ret = SEP.join([DEFAULT_DER_ROOT, str(index)])
    return ret


@lru_cache()
def get_enddevice_href(edev_indx: int, subref: str = None) -> str:
    if edev_indx == NO_INDEX:
        ret = DEFAULT_EDEV_ROOT
    elif subref:
        ret = SEP.join([DEFAULT_EDEV_ROOT, f"{edev_indx}", f"{subref}"])
    else:
        ret = SEP.join([DEFAULT_EDEV_ROOT, f"{edev_indx}"])
    return ret


@lru_cache()
def registration_href(edev_index: int) -> str:
    return SEP.join([DEFAULT_EDEV_ROOT, str(edev_index), "rg"])


@lru_cache()
def get_configuration_href(edev_index: int) -> str:
    return get_enddevice_href(edev_index, "cfg")


@lru_cache()
def get_power_status_href(edev_index: int) -> str:
    return get_enddevice_href(edev_index, "ps")


@lru_cache()
def get_device_status(edev_index: int) -> str:
    return get_enddevice_href(edev_index, "ds")


@lru_cache()
def get_device_information(edev_index: int) -> str:
    return get_enddevice_href(edev_index, "di")


@lru_cache()
def get_time_href() -> str:
    # return f"{DEFAULT_DCAP_ROOT}{SEP}tm"
    return f"/tm"


@lru_cache()
def get_log_list_href(edev_index: int) -> str:
    return get_enddevice_href(edev_index, "lel")


@lru_cache()
def get_dcap_href() -> str:
    return f"{DEFAULT_DCAP_ROOT}"


def get_dderc_href() -> str:
    return SEP.join([DEFAULT_DER_ROOT, DDERC])


def get_derc_default_href(derp_index: int) -> str:
    return SEP.join([DEFAULT_DER_ROOT, DDERC, f"{derp_index}"])


def get_derc_href(index: int) -> str:
    """Return the DERControl href to the caller

    if NO_INDEX then don't include the index in the result.
    """
    if index == NO_INDEX:
        return SEP.join([DEFAULT_DER_ROOT, DERC])

    return SEP.join([DEFAULT_DER_ROOT, DERC, f"{index}"])


def get_program_href(index: int, subref: str = None):
    """Return the DERProgram href to the caller

    Args:
        index: if NO_INDEX then don't include the index in the result else use the index
        subref: used to specify a subsection in the program.
    """
    if index == NO_INDEX:
        ref = f"{DEFAULT_PROGRAM_ROOT}"
    else:
        if subref is not None:
            ref = f"{DEFAULT_PROGRAM_ROOT}{SEP}{index}{SEP}{subref}"
        else:
            ref = f"{DEFAULT_PROGRAM_ROOT}{SEP}{index}"
    return ref


# TimeLink
# tm: str = f"{DEFAULT_DCAP_ROOT}{SEP}tm"
# # ResponseSetListLink
# rsps: str = f"{DEFAULT_DCAP_ROOT}{SEP}rsps"
# # UsagePointListLink
# upt: str = DEFAULT_UPT_ROOT
#
# DERProgramListLink
# derp: str = "/derp"
#
# # EndDeviceListLink
# edev: str = DEFAULT_EDEV_ROOT
# edev_urls: List = [
#     f"/<regex('{edev}[0-9a-zA-Z\-]*'):path>",
#     # f"{edev}/<path:fullpath>"
#     # ,
#     # f"{edev}/<int:index>",
#     # f"{edev}/<int:index>/<category>"
# ]
#
# # MirrorUsagePointListLink
# mup: str = DEFAULT_MUP_ROOT
# mup_urls: List = [
#     (mup, ('GET', 'POST')),
#     f"{mup}/<int:index>"
# ]
#
# curve: str = "/curves"
# curve_urls: List = [
#     f"{curve}",
#     (f"{curve}/<int:index>", ("GET",))
# ]
#
# program: str = "/programs"
# program_urls: List = [
#     f"{program}",
#     (f"{program}/<int:index>/actderc", ("GET",)),
#     (f"{program}/<int:index>/dc", ("GET",)),
#     (f"{program}/<int:index>/dderc", ("GET",)),
#     (f"{program}/<int:index>/derc", ("GET",)),
# ]
#
# der: str = "/der"
# der_urls: List = [
#     (f"{der}/<int:edev_id>", ('GET', 'POST')),
#     (f"{der}/<int:edev_id>/<int:id>", ('GET', 'PUT', 'DELETE')),
#     (f"{der}/<int:edev_id>/<int:id>/upt", ('GET', 'DELETE')),
#     (f"{der}/<int:edev_id>/<int:id>/derp", ('GET', 'POST')),
#     (f"{der}/<int:edev_id>/<int:id>/cdp", ('GET', 'DELETE')),
#     (f"{der}/<int:edev_id>/<int:id>/derg", ('GET', 'PUT')),
#     (f"{der}/<int:edev_id>/<int:id>/ders", ('GET', 'PUT')),
#     (f"{der}/<int:edev_id>/<int:id>/dera", ('GET', 'PUT')),
#     (f"{der}/<int:edev_id>/<int:id>/dercap", ('GET', 'PUT')),
# ]
#
sdev: str = DEFAULT_SELF_ROOT


def build_der_link(edev_id: Optional[int] = None,
                   id: Optional[int] = None,
                   suffix: Optional[str] = None) -> str:
    if edev_id is None:
        raise ValueError("edev_id must be specified.")
    if id is not None and suffix is not None:
        link = build_link(f"{der}", f"{edev_id}", f"{id}", suffix)
    elif id is not None:
        link = build_link(f"{der}", f"{edev_id}", f"{id}")
    elif suffix is not None:
        link = build_link(f"{der}", f"{edev_id}", suffix)
    else:
        link = build_link(f"{der}", f"{edev_id}")

    return link


def build_edev_registration_link(index: int) -> str:
    return build_link(f"{edev}", index, "reg")


def build_edev_status_link(index: int) -> str:
    return build_link(f"{edev}", index, "ds")


def build_edev_config_link(index: int) -> str:
    return build_link(f"{edev}", index, "cfg")


def build_edev_info_link(index: int) -> str:
    return build_link(f"{edev}", index, "di")


def build_edev_power_status_link(index: int) -> str:
    return build_link(f"{edev}", index, "ps")


def build_edev_fsa_link(index: int, fsa_index: Optional[int] = None) -> str:
    return build_link(f"{edev}", index, "fsa", fsa_index)


# edev_cfg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/cfg"
# edev_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ds"
# edev_info_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/di"
# edev_power_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ps"
# edev_file_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fs"
# edev_sub_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/subl"

#
# # DemandResponseProgramListLink
# drp: str = DEFAULT_DRP_ROOT
# # MessagingProgramListLink
# msg: str = DEFAULT_MESSAGE_ROOT
# # SelfDeviceLink
# sdev: str = DEFAULT_SELF_ROOT
#
# edev_base: str = '/edev'
# edev: List[str] = [
#     DEFAULT_EDEV_ROOT,
#     [f"{DEFAULT_EDEV_ROOT}/<int:index>", ["GET", "POST"]]
# ]
#
#
#
# sdev_di: str = f"{DEFAULT_DCAP_ROOT}/sdev/di"
# sdev_log: str = f"{DEFAULT_DCAP_ROOT}/sdev/log"
#
# mup_fmt: str = f"{DEFAULT_MUP_ROOT}" + "/{index}"
#
# edev_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}"
# reg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/reg"
# # di_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/di"
# #dstat_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dstat"
# ps_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ps"
#
# derp_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derp"
# derp_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derp/1"
#
# der_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/der/1"
# dera_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dera/1"
# dercap_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dercap/1"
# derg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derg/1"
# ders_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ders/1"
#
# derc_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derc"
# derc_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derc/1"
#
# fsa_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fsa"
# fsa_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fsa/0"
#
# edev_cfg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/cfg"
# edev_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ds"
# edev_info_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/di"
# edev_power_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ps"
# edev_file_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fs"
# edev_sub_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/subl"

admin: str = "/admin"
uuid_gen: str = "/uuid"


def build_link(base_url: str, *suffix: Optional[str]):
    result = base_url
    if result.endswith("/"):
        result = result[:-1]

    if suffix:
        for p in suffix:
            if p is not None:
                if isinstance(p, str):
                    if p.startswith("/"):
                        result += f"{p}"
                    else:
                        result += f"/{p}"
                else:
                    result += f"/{p}"

    return result


def extend_url(base_url: str, index: Optional[int] = None, suffix: Optional[str] = None):
    result = base_url
    if index is not None:
        result += f"/{index}"
    if suffix:
        result += f"/{suffix}"

    return result
