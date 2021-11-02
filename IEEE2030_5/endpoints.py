import IEEE2030_5
from IEEE2030_5 import xsd_models
from IEEE2030_5.end_device import IEEE2030_5Renderer


# Functionf ro dcap style endpoints
def dcap():
    dcap = xsd_models.DeviceCapability(
        EndDeviceListLink=xsd_models.EndDeviceListLink(),
        MirrorUsagePointListLink=xsd_models.MirrorUsagePointListLink(),
        SelfDeviceLink=xsd_models.SelfDeviceLink()
    )
    dcap.set_href(IEEE2030_5.IEEE2030_5_ENDPOINTS["dcap"].url)

    dcap.EndDeviceListLink.set_href(IEEE2030_5.IEEE2030_5_ENDPOINTS["edev-list"].url)
    dcap.SelfDeviceLink.set_href(IEEE2030_5.IEEE2030_5_ENDPOINTS["sdev"].url)

    dcap.TimeLink = xsd_models.TimeLink()
    dcap.TimeLink.set_href(IEEE2030_5.IEEE2030_5_ENDPOINTS["tm"].url)

    dcap.MirrorUsagePointListLink.set_href(IEEE2030_5.IEEE2030_5_ENDPOINTS["mup-list"].url)

    return IEEE2030_5Renderer.render({"result": dcap})
    #IEEE2030_5Agent.prep_200_response({"result": dcap})


# def sdev_log():
#     sep_log_event_list = xsd_models.LogEventList()
#     return IEEE2030_5Renderer.render({"result": sep_log_event_list})
