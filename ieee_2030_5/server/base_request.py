from __future__ import annotations
import logging
from typing import Dict, Callable

import werkzeug
from flask import request

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.models import DeviceCategoryType
from ieee_2030_5.models.end_devices import EndDevices

_log = logging.getLogger(__name__)


class ServerOperation:

    def __init__(self):
        if 'ieee_2030_5_peercert' not in request.environ:
            raise werkzeug.exceptions.Forbidden()

    def head(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def get(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def post(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def delete(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def put(self):
        raise werkzeug.exceptions.MethodNotAllowed()

    def execute(self):
        methods = {
            'GET': self.get,
            'POST': self.post,
            'DELETE': self.delete,
            'PUT': self.put
        }
        _log.debug(f"Request method is {request.environ['REQUEST_METHOD']}")
        fn = methods.get(request.environ['REQUEST_METHOD'])
        if not fn:
            raise werkzeug.exceptions.MethodNotAllowed()

        return fn()


class RequestOp(ServerOperation):
    def __init__(self, end_devices: EndDevices, tls_repo: TLSRepository, server_endpoints: ServerEndpoints):
        super().__init__()
        self._end_devices = end_devices
        self._tls_repository = tls_repo
        self._server_endpoint = server_endpoints
        # required so we don't have to maintain a duplicate list for removing endpoints from flask,
        # this will make the server easier to use
        self._endpoint_map: Dict[str, str] = {}

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

    def add_endpoint(self, endpoint: str, view_func: Callable, post: bool = False,
                     get: bool = True, put: bool = False, delete: bool = False):
        _log.debug(f"Adding endpoint {endpoint}, function {view_func.__name__}")
        self._endpoint_map[endpoint] = view_func.__name__
        methods = []
        if get:
            methods.append("GET")
        if post:
            methods.append("POST")
        if delete:
            methods.append("DELETE")
        if put:
            methods.append("PUT")

        # TODO: What happens if no methods specified?
        self._server_endpoint.add_endpoint(endpoint, view_func, methods=methods)

    def remove_endpoint(self, endpoint: str):
        _log.debug(f"Removing endpoint {endpoint}")
        self._server_endpoint.remove_endpoint(self._endpoint_map[endpoint])
        self._endpoint_map.pop(endpoint)

from ieee_2030_5.server.server_endpoints import ServerEndpoints
