import json

from flask import Flask, Response

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.models.end_devices import EndDevices


class AdminEndpoints:
    def __init__(self, app: Flask, end_devices: EndDevices, tls_repo: TLSRepository, config: ServerConfiguration):
        self.end_devices = end_devices
        self.tls_repo = tls_repo
        self.server_config = config

        app.add_url_rule("/admin/lfid", endpoint="admin/lfid", view_func=self._lfid_lists)

    def _lfid_lists(self) -> Response:
        items = []

        for k, v in self.end_devices.all_end_devices.items():
            items.append({"key": k, "lfid": int(v.end_device.lFDI)})

        return Response(json.dumps(items))
