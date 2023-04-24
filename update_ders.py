import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import requests

warnings.filterwarnings("ignore")
ieee_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ieee_dir))
import ieee_2030_5.models as m
from ieee_2030_5 import dataclass_to_xml, xml_to_dataclass

session = requests.Session()
session.cert = ('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem')
session.verify = "/home/os2004/tls/certs/ca.pem"

def get_url(endpoint) -> str:
    if endpoint.startswith('/'):
        endpoint = endpoint[1:]
    return f"https://127.0.0.1:7443/admin/{endpoint}"

#resp = session.get("https://127.0.0.1:7443/admin?path=/enddevices")

#end_devices = xml_to_dataclass(resp.text, m.EndDeviceList)

current_time = int(time.mktime(datetime.utcnow().timetuple()))

resp = session.get(get_url("enddevices"))

if not resp.ok:
    print("Getting End Device Error")
    print(resp.text)
    sys.exit()
    

enddevices: m.EndDeviceList = xml_to_dataclass(resp.text)

resp = session.get(get_url("derp"))

if not resp.ok:
    print("Getting DER Program List Error")
    print(resp.text)
    sys.exit()

derps: m.DERProgramList = xml_to_dataclass(resp.text)

for index, derp in enumerate(derps.DERProgram):
    print(f"DERP: {index} {derp}")
    
# Grab the first one
update_derp = derps.DERProgram[0]
    

for index, ed in enumerate(enddevices.EndDevice):
    # Retrieve ders with edev index
    resp = session.get(get_url(f"ders/{index}"))
    if not resp.ok:
        print(f"Getting DER/{index} Error")
        print(resp.text)
        sys.exit()

    ders: m.DERList = xml_to_dataclass(resp.text)
    
    for der_index, der in enumerate(ders.DER):
        print(f"Before: {der.CurrentDERProgramLink.href}")
        resp = session.put(get_url(f"/edev/{index}/ders/{der_index}/current_derp"), 
                           dataclass_to_xml(update_derp))
        print(f"Update response: {resp.status_code}")
        
        resp = session.get(get_url(f"/edev/{index}/ders/{der_index}/current_derp"))
        
        if not resp.ok:
            print(f"Error getting current_program")
            print(resp.text)
            sys.exit()
        
        der_program: m.DERProgram = xml_to_dataclass(resp.text)
        print(f"After: {der_program.href}")
        
#print(resp)