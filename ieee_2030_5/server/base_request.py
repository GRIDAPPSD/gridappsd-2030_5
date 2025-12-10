from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

import werkzeug
from flask import Response, request

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.hrefs import SEP, PathComponent

if TYPE_CHECKING:
    import ieee_2030_5.server.server_endpoints as eps

from ieee_2030_5.types_ import SEP_XML
from ieee_2030_5.utils import dataclass_to_xml

_log = logging.getLogger(__name__)

# DER-related path prefixes for monitoring
# Uses SEP constant from hrefs module for consistency
# Includes both slash-separated (/der/) and underscore-separated (der_) formats
DER_MONITOR_PATHS = (
    f"/{PathComponent.DER}/",  # /der/
    f"/{PathComponent.DER_PROGRAM}/",  # /derp/
    f"/{PathComponent.EDEV}/",  # /edev/
    f"/{PathComponent.DER}{SEP}",  # /der_
    f"{PathComponent.DER}{SEP}",  # der_
    f"{SEP}{PathComponent.DER}{SEP}",  # _der_
    f"{SEP}{PathComponent.DER_PROGRAM}{SEP}",  # _derp_
    f"{SEP}{PathComponent.DER_STATUS}",  # _ders
    f"{SEP}{PathComponent.DER_SETTINGS}",  # _derg
    f"{SEP}{PathComponent.DER_AVAILABILITY}",  # _dera
    f"{SEP}{PathComponent.DER_CAPABILITY}",  # _dercap
    f"{SEP}{PathComponent.DDERC}",  # _dderc
    f"{SEP}{PathComponent.DERC}",  # _derc
)
DER_RESOURCE_TYPES = (
    "DER", "DERStatus", "DERSettings", "DERCapability", "DERAvailability",
    "DERProgram", "DERProgramList", "DERControl", "DERControlList",
    "DefaultDERControl", "DERCurve", "DERCurveList"
)


class ServerOperation:
    def __init__(self):
        if "ieee_2030_5_peercert" not in request.environ:
            raise werkzeug.exceptions.Forbidden()
        self._headers = {"Content-Type": SEP_XML}
        self._environ = request.environ

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
        methods = {"GET": self.get, "POST": self.post, "DELETE": self.delete, "PUT": self.put}

        fn = methods.get(request.environ["REQUEST_METHOD"])
        if not fn:
            raise werkzeug.exceptions.MethodNotAllowed()

        return fn(**kwargs)


class RequestOp(ServerOperation):
    def __init__(self, server_endpoints: eps.ServerEndpoints):
        super().__init__()
        self._tls_repository = server_endpoints.tls_repo
        self._server_endpoints = server_endpoints

    @property
    def tls_repo(self) -> TLSRepository:
        return self._tls_repository

    @property
    def server_config(self) -> ServerConfiguration:
        return self._server_endpoints.config

    @property
    def lfdi(self):
        return request.environ["ieee_2030_5_lfdi"]  # self._tls_repository.lfdi(request.environ['ieee_2030_5_subject'])

    @property
    def device_id(self):
        return request.environ.get("ieee_2030_5_subject")

    def get_path(self, required_prefix: str | None = None) -> str:
        """
        Retrieve the context web request environment PATH_INFO with optional required_prefix
        argument.  If that argument is specified then it will be validated against PATH_INFO.  The
        function will raise a ValueError if the PATH_INFO does not start with required_prefix.

        Args:
            required_prefix:

        Returns:
            The path specified in request.environ['PATH_INFO'
        """

        pth = request.environ["PATH_INFO"]

        if required_prefix and not pth.startswith(required_prefix):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        return pth

    def build_response_from_dataclass(self, obj: dataclass, log_operation: bool = True) -> Response:
        """Build a Flask response from a dataclass and optionally log to DER monitor."""
        if log_operation:
            self._log_der_operation(request.method, response_obj=obj)
        return Response(dataclass_to_xml(obj), headers=self._headers)

    def _log_der_operation(self, operation: str, response_obj=None, raw_xml: str = ""):
        """Log DER operations to the monitoring system."""
        try:
            path = request.path
            # Only log DER-related paths
            if not any(path.startswith(p) or p in path for p in DER_MONITOR_PATHS):
                return

            from ieee_2030_5.monitoring import get_der_status_monitor

            monitor = get_der_status_monitor()

            # Determine resource type from response object or path
            resource_type = "Unknown"
            data = {}

            if response_obj is not None:
                resource_type = type(response_obj).__name__
                if hasattr(response_obj, '__dataclass_fields__'):
                    try:
                        data = asdict(response_obj)
                    except Exception:
                        pass

            monitor.log_operation(
                client_lfdi=getattr(self, 'lfdi', None) or "unknown",
                der_path=path,
                resource_type=resource_type,
                operation=operation,
                data=data,
                raw_xml=raw_xml,
            )
        except Exception as e:
            _log.debug(f"Failed to log DER operation: {e}")
