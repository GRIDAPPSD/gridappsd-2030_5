from flask import Response

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.server.base_request import RequestOp


class Dcap(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        # TODO: Test for allowed dcap here.
        # if not self._end_devices.allowed_to_connect(self.lfdi):
        #     raise werkzeug.exceptions.Unauthorized()
        device = adpt.EndDeviceAdapter.fetch_by_property("lFDI", self.lfdi)
        device_index = adpt.EndDeviceAdapter.fetch_index(device)
        cap = adpt.DeviceCapabilityAdapter.fetch(device_index)

        return self.build_response_from_dataclass(cap)