import logging
import ssl
import typing

from typing import Optional
from pathlib import Path

import gunicorn
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from icecream import ic
import uvicorn

from IEEE2030_5 import ConfigObj, TLSRepository
from IEEE2030_5.endpoints import dcap

__all__ = ["run_server"]


templates = Jinja2Templates(directory="templates")


class AdminPages:
    def __init__(self, config: ConfigObj):
        self._config = config

    def render(self, request: Request, page: str = None):
        ic(request)
        ic(page)
        template_page = f"admin/{page}.html" if page is not None else "admin/helloworld.html"
        template_dict = dict(request=request)

        if page == 'clients':
            template_dict['connected'] = [1,2,3]
            template_dict['registered'] = [4,5,6]

        return templates.TemplateResponse(template_page,
                                          template_dict)


class IEEE2030_5Response(Response):
    media_type = "application/xml"  # "application/sep+xml"

    def render(self, content: str) -> bytes:
        return content.encode("utf-8")


def run_server(config: ConfigObj, tlsrepo: TLSRepository):

    app = FastAPI()
    admin = AdminPages(config)

    app.add_api_route("/dcap", dcap, response_class=IEEE2030_5Response)
    app.add_api_route("/admin/", admin.render, response_class=HTMLResponse)
    app.add_api_route("/admin/{page}", admin.render, response_class=HTMLResponse)

    # app.openapi()
    gunicorn.
    uvicorn.run(app,
                host="0.0.0.0",
                port=8000,
                # reload=True,
                ssl_cert_reqs=ssl.CERT_REQUIRED,
                ssl_certfile=tlsrepo.server_cert_file,
                ssl_keyfile=tlsrepo.server_key_file) # , reload=True)