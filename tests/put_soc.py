from pathlib import Path

from ieee_2030_5.client import IEEE2030_5_Client

server = "WE48687"
port = 8090
ca_path = (Path("~/tls") / "certs/ca.crt").expanduser()
public = (Path("~/tls") / "certs/dev1.crt").expanduser()
private = (Path("~/tls") / "private/dev1.pem").expanduser()

client = IEEE2030_5_Client(cafile=ca_path, server_hostname=server, keyfile=private, certfile=public, server_ssl_port=port, debug=True)

dcap = client.device_capability()
der_list = client.der_list()

client.disconnect()

