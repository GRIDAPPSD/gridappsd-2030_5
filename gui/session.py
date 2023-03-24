import requests

backend_session = requests.Session()

backend_session.cert = ('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem')
backend_session.verify = "/home/os2004/tls/certs/ca.pem"

def endpoint(endpoint: str) -> str:
    base_url = "https://127.0.0.1:7443/admin"
    return f"{base_url}/{endpoint}"