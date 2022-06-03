from dataclasses import dataclass
from typing import Optional

DEFAULT_DCAP_ROOT = "/dcap"
DEFAULT_EDEV_ROOT = "/edev"
DEFAULT_UPT_ROOT = "/utp"
DEFAULT_MUP_ROOT = "/mup"
DEFAULT_DRP_ROOT = "/drp"
DEFAULT_SELF_ROOT = "/sdev"
DEFAULT_MESSAGE_ROOT = "/msg"


dcap: str = f"{DEFAULT_DCAP_ROOT}"
# TimeLink
tm: str = f"{DEFAULT_DCAP_ROOT}/tm"
# ResponseSetListLink
rsps: str = f"{DEFAULT_DCAP_ROOT}/rsps"
# UsagePointListLink
upt: str = DEFAULT_UPT_ROOT
# EndDeviceListLink
edev: str = DEFAULT_EDEV_ROOT
# MirrorUsagePointListLink
mup: str = DEFAULT_MUP_ROOT
# DemandResponseProgramListLink
drp: str = DEFAULT_DRP_ROOT
# MessagingProgramListLink
msg: str = DEFAULT_MESSAGE_ROOT
# SelfDeviceLink
sdev: str = DEFAULT_SELF_ROOT

sdev_di: str = f"{DEFAULT_DCAP_ROOT}/sdev/di"
sdev_log: str = f"{DEFAULT_DCAP_ROOT}/sdev/log"

mup_fmt: str = f"{DEFAULT_MUP_ROOT}" + "/{index}"

edev_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}"
reg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/reg"
# di_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/di"
#dstat_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dstat"
ps_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ps"

derp_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derp"
derp_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derp/1"

der_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/der/1"
dera_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dera/1"
dercap_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/dercap/1"
derg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derg/1"
ders_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ders/1"

derc_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derc"
derc_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/derc/1"

fsa_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fsa"
fsa_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fsa/0"

edev_cfg_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/cfg"
edev_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ds"
edev_info_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/di"
edev_power_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/ps"
edev_file_status_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/fs"
edev_sub_list_fmt: str = f"{DEFAULT_DCAP_ROOT}/edev" + "/{index}/subl"

admin: str = "/admin"


def extend_url(base_url: str, index: Optional[int] = None, suffix: Optional[str] = None):
    result = base_url
    if index is not None:
        result += f"/{index}"
    if suffix:
        result += f"/{suffix}"

    return result
