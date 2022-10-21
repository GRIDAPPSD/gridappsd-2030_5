import json

from flask import Flask, Response, render_template

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.server.server_constructs import EndDevices


class AdminEndpoints:
    def __init__(self, app: Flask, end_devices: EndDevices, tls_repo: TLSRepository, config: ServerConfiguration):
        self.end_devices = end_devices
        self.tls_repo = tls_repo
        self.server_config = config

        app.add_url_rule("/admin/end-device-list", view_func=self._end_device_list)
        app.add_url_rule("/admin/program-lists", view_func=self._program_lists)
        app.add_url_rule("/admin/lfdi", endpoint="admin/lfdi", view_func=self._lfdi_lists)
        app.add_url_rule("/admin/edev/<int:edevid>/fsa", view_func=self._edev_fsa)

    def _lfdi_lists(self) -> Response:
        items = []

        for k, v in self.end_devices.__all_end_devices__.items():
            items.append({"key": k, "lfdi": int(v.end_device.lFDI)})

        return Response(json.dumps(items))

    def _edev_fsa(self, edevid: int) -> Response:
        #edev = self.end_devices.get(edevid)
        return Response(json.dumps(json.dumps(self.end_devices.get_fsa_list(edevid=edevid))))

    def _program_lists(self) -> str:
        return render_template("admin/program-lists.html",
                               program_lists=self.server_config.program_lists)

    def _end_device_list(self) -> str:
        return render_template("admin/end-device-list.html",
                               end_device_list=self.end_devices.get_end_devices())
