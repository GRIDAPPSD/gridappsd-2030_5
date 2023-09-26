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

def get_der_list() -> m.DERList:
    href = endpoint('der')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_der(item: m.DER) -> m.DER:
    item_xml = dataclass_to_xml(item)
        
    if item.href:
        _log.debug("PUTTING data")
        response = backend_session.put(endpoint('der'), data=item_xml)
    else:
        _log.debug("POSTING data")
        response = backend_session.post(endpoint('der'), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_enddevice_list() -> m.EndDeviceList:
    href = endpoint('enddevice')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_enddevice(item: m.EndDevice) -> m.EndDevice:
    item_xml = dataclass_to_xml(item)
        
    if item.href:
        _log.debug("PUTTING data")
        response = backend_session.put(endpoint('enddevices'), data=item_xml)
    else:
        _log.debug("POSTING data")
        response = backend_session.post(endpoint('enddevices'), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_fsa_list() -> m.FunctionSetAssignmentsList:
    href = endpoint('fsa')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_fsa(fsa: m.FunctionSetAssignments) -> m.FunctionSetAssignments:
    item_xml = dataclass_to_xml(fsa)
        
    if fsa.href:
        _log.debug("PUTTING data")
        response = backend_session.put(endpoint('fsa'), data=item_xml)
    else:
        _log.debug("POSTING data")
        response = backend_session.post(endpoint('fsa'), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_program_list() -> m.DERProgramList:
    href = endpoint('programs')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_program(program: m.DERProgram) -> m.DERProgram:
    slug = "programs"
    item = program
    item_xml = dataclass_to_xml(program)
    
        
    if item.href:
        _log.debug(f"PUTTING {item.__class__.__name__} data: {item_xml}")
        response = backend_session.put(endpoint(slug), data=item_xml)
    else:
        _log.debug(f"POSTING {item.__class__.__name__} data: {item_xml}")
        response = backend_session.post(endpoint(slug), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)


def get_control_list() -> m.DERControlList:
    href = endpoint('controls')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)


def send_control(control: m.DERControl) -> m.DERControl:
    slug = "controls"
    item = control
    item_xml = dataclass_to_xml(control)
        
    if item.href:
        _log.debug(f"PUTTING {item.__class__.__name__} data: {item_xml}")
        response = backend_session.put(endpoint(slug), data=item_xml)
    else:
        _log.debug(f"POSTING {item.__class__.__name__} data: {item_xml}")
        response = backend_session.post(endpoint(slug), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_curve_list() -> m.DERCurveList:
    href = endpoint('curves')
    list_params = list_parameters()
    return xml_to_dataclass(backend_session.get(href, params=list_params).text)

def send_curve(curve: m.DERCurve) -> m.DERCurve:
    slug = "curves"
    item = curve
    item_xml = dataclass_to_xml(curve)
        
    if curve.href:
        _log.debug("PUTTING data")
        response = backend_session.put(endpoint(slug), data=item_xml)
    else:
        _log.debug("POSTING data")
        response = backend_session.post(endpoint(slug), data=item_xml)
    
    _log.debug(response.text)
    
    return xml_to_dataclass(response.text)

def get_enddevice_list() -> m.EndDeviceList:
    return xml_to_dataclass(backend_session.get(endpoint('enddevices')).text)

def get_cert_list():
    certs = backend_session.get(endpoint('certs')).json()
    return certs