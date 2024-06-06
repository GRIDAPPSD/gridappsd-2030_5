import flet as ft

import json
from http.client import HTTPSConnection
import ssl
from typing import Callable

import logging
import os
from pathlib import Path
from fastapi.middleware.wsgi import WSGIMiddleware
from urllib.parse import urlparse

_log = logging.getLogger(__name__)

this_view: ft.Ref[ft.View] = ft.Ref()
this_page: ft.Ref[ft.Page] = ft.Ref()
admin_cert: ft.Ref[ft.TextField] = ft.Ref()
admin_key: ft.Ref[ft.TextField] = ft.Ref()
ca_cert: ft.Ref[ft.TextField] = ft.Ref()
text_response: ft.Ref[ft.Text] = ft.Ref()
col_response: ft.Ref[ft.Column] = ft.Ref()
admin_endpoint: ft.Ref[ft.Column] = ft.Ref()

def populate_tree() -> None:
    _log.debug("Populating tree")

    parsed_url = urlparse(admin_endpoint.current.value)

    _ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    _ssl_context.check_hostname = False
    _ssl_context.verify_mode = ssl.CERT_OPTIONAL    #  ssl.CERT_REQUIRED
    _ssl_context.load_verify_locations(cafile=os.path.expanduser(ca_cert.current.value))

    # Loads client information from the passed cert and key files. For
    # client side validation.
    _ssl_context.load_cert_chain(certfile=os.path.expanduser(admin_cert.current.value),
                                 keyfile=os.path.expanduser(admin_key.current.value))

    _http_conn = HTTPSConnection(host=parsed_url.hostname,
                                 port=parsed_url.port,
                                 context=_ssl_context)

    _http_conn.connect()
    _http_conn.request("GET", parsed_url.path+"/resources")
    response = _http_conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    text_response.current.value = json.dumps(data, indent=4)
    _http_conn.close()
    this_page.current.update()

    # app.run(host=os.getenv(f"{PREFIX}_HOST"), port=os.getenv(f"{PREFIX}_PORT"), debug=True, ssl_context=(os.getenv(f"{PREFIX}_CLIENT_CERT"), os.getenv(f"{PREFIX}_CLIENT_KEY"), os.getenv(f"{PREFIX}_CA_CERT")))
    # app.run(host=os.getenv(f"{PREFIX}_HOST"), port=os.getenv(f"{PREFIX}_PORT"), debug=True, ssl_context=(os.getenv(f"{PREFIX}_CLIENT_CERT"), os.getenv(f"{PREFIX}_CLIENT_KEY"), os.getenv(f"{PREFIX}_CA_CERT"))





def show_resource_tree_view(page: ft.Page) -> ft.View:
    this_page.current = page

    this_view.current = ft.View("/", scroll=True, controls=[
        ft.AppBar(title=ft.Text("Server Control"),
                  automatically_imply_leading=False,
                  bgcolor=ft.colors.SURFACE_VARIANT),
        ft.TextField(
            label="Admin Certificate", ref=admin_cert, width=500, value="~/tls/certs/admin.crt"),
        ft.TextField(label="Admin Key", ref=admin_key, width=500, value="~/tls/private/admin.pem"),
        ft.TextField(label="CA Certificate", ref=ca_cert, width=500, value="~/tls/certs/ca.crt"),
        ft.TextField(label="Admin Endpoint",
                     ref=admin_endpoint,
                     width=500,
                     value="https://we48687:8090/admin"),
        ft.Column(ref=col_response, controls=[ft.Text(ref=text_response)], scroll=True),
        ft.ElevatedButton("Populate", on_click=lambda _: populate_tree()),
    ])

    return this_view.current
