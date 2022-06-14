from __future__ import annotations
import logging
from typing import Dict, Callable

import werkzeug
from flask import request

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.models import DeviceCategoryType
# from ieee_2030_5.server.server_endpoints import ServerEndpoints
# from ieee_2030_5.server.server_endpoints import ServerEndpoints

_log = logging.getLogger(__name__)


class ServerOperation:

    def __init__(self):
        if 'ieee_2030_5_peercert' not in request.environ:
            raise werkzeug.exceptions.Forbidden()

    def head(self, **kwargs):
        raise werkzeug.exceptions.MethodNotAllowed()

    def get(self, **kwargs):
        raise werkzeug.exceptions.MethodNotAllowed()

    def post(self, **kwargs):
        raise werkzeug.exceptions.MethodNotAllowed()

    def delete(self, **kwargs):
        raise werkzeug.exceptions.MethodNotAllowed()

    def put(self, **kwargs):
        raise werkzeug.exceptions.MethodNotAllowed()

    def execute(self, **kwargs):
        methods = {
            'GET': self.get,
            'POST': self.post,
            'DELETE': self.delete,
            'PUT': self.put
        }
        fn = methods.get(request.environ['REQUEST_METHOD'])
        if not fn:
            raise werkzeug.exceptions.MethodNotAllowed()

        return fn(**kwargs)


class RequestOp(ServerOperation):
    def __init__(self, server_endpoints: ServerEndpoints):
        super().__init__()
        self._end_devices = server_endpoints.end_devices
        self._tls_repository = server_endpoints.tls_repo
        self._server_endpoints = server_endpoints

    @property
    def tls_repo(self) -> TLSRepository:
        return self._tls_repository

    @property
    def server_config(self) -> ServerConfiguration:
        return self._server_endpoints.config

    @property
    def lfid(self):
        return self._tls_repository.lfdi(request.environ['ieee_2030_5_subject'])

    @property
    def device_id(self):
        return request.environ.get("ieee_2030_5_subject")

    @property
    def is_admin_client(self) -> bool:
        ed = self._end_devices.get_device_by_lfid(self.lfid)
        return ed.deviceCategory == DeviceCategoryType.OTHER_CLIENT
