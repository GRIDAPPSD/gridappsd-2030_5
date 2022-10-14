from functools import lru_cache
from typing import Optional, List

EDEV = "edev"
DCAP = "dcap"
UTP = "utp"
MUP = "mup"
DRP = "drp"
SDEV = "sdev"
MSG = "msg"
DER = "der"
CURVE = "curve"
PROGRAM = "program"

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

SEP = "_"
MATCH_REG = "[a-zA-Z0-9_]*"


@lru_cache()
def get_enddevice_list_href() -> str:
    return DEFAULT_EDEV_ROOT


def get_curve_href(index: int) -> str:
    return SEP.join([DEFAULT_CURVE_ROOT, str(index)])


def get_fsa_href(fsa_list_href: str, index: int) -> str:
    return SEP.join([fsa_list_href, str(index)])


def get_der_program_list(fsa_href: str) -> str:
    return SEP.join([fsa_href, "der"])


def get_dr_program_list(fsa_href: str) -> str:
    return SEP.join([fsa_href, "dr"])


def get_fsa_list_href(end_device_href: str) -> str:
    return SEP.join([end_device_href, "fsa"])


@lru_cache()
def get_enddevice_href(index: int) -> str:
    return SEP.join([DEFAULT_EDEV_ROOT, f"{index}"])


@lru_cache()
def get_registration_href(index: int) -> str:
    return SEP.join([DEFAULT_EDEV_ROOT, f"{index}", "reg"])


@lru_cache()
def get_configuration_href(index: int) -> str:
    return SEP.join([DEFAULT_EDEV_ROOT, f"{index}", "cfg"])


@lru_cache()
def get_time_href() -> str:
    return f"{DEFAULT_DCAP_ROOT}{SEP}tm"


@lru_cache()
def get_dcap_href() -> str:
    return f"{DEFAULT_DCAP_ROOT}"


def get_program_href(index: int, subref: str = None):
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


def build_der_link(edev_id: Optional[int] = None, id: Optional[int] = None, suffix: Optional[str] = None) -> str:
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
