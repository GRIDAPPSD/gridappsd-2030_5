import logging
import os
import urllib.parse
from enum import Enum

import requests

import ieee_2030_5.models as m
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

_log = logging.getLogger(__name__)

backend_session = requests.Session()
ADMIN_URL = ""

class SaveRequestMethod(Enum):
    POST = "POST"
    PUT = "PUT"
    
def setup_backend_session():
    global backend_session, ADMIN_URL
    
    if not ADMIN_URL:    
        backend_session.cert = (os.getenv("2030_5_CLIENT_CERT"), os.getenv("2030_5_CLIENT_KEY"))
        backend_session.verify = os.getenv("2030_5_CA_CERT")
        ADMIN_URL = f"https://{os.getenv('2030_5_HOST')}:{os.getenv('2030_5_PORT')}/admin" 

def list_endpoint(endpoint: str, start: int = 0, after: int = 0, limit: int = 0) -> str:
    setup_backend_session()
    base_url = ADMIN_URL
    while endpoint.startswith('/'):
        endpoint = endpoint[1:]
    endpoint = urllib.parse.quote(endpoint)
    endpoint += f"?s={start}&a={after}&l={limit}"
    return f"{base_url}/{endpoint}"
        

def list_parameters(start: int = 0, after: int = 0, limit: int = 0):
    return dict(s=start, a=after, l=limit)
def endpoint(endpoint: str) -> str:
    setup_backend_session()
    base_url = ADMIN_URL
    while endpoint.startswith('/'):
        endpoint = endpoint[1:]
    endpoint = urllib.parse.quote(endpoint)
    return f"{base_url}/{endpoint}"

def get_default_controls() -> None:
    pass

def get_curves() -> m.DERCurveList:
    href = endpoint('curves')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_curve(curve: m.DERCurve) -> m.DERCurve:
    curve_xml = dataclass_to_xml(curve)
        
    if curve.href:
        _log.debug("PUTTING data")
        response = backend_session.put(endpoint('curves'), data=curve_xml)
    else:
        _log.debug("POSTING data")
        response = backend_session.post(endpoint('curves'), data=curve_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_end_devices() -> m.EndDeviceList:
    
    return xml_to_dataclass(backend_session.get(endpoint('enddevices')).text)

def get_certs():
    certs = backend_session.get(endpoint('certs')).json()
    return certs