from pathlib import Path

import pytest

from IEEE2030_5.client import IEEE2030_5_Client


SERVER_CA_CERT = Path("~/tls/certs/ca.crt").expanduser().resolve()

@pytest.fixture()
def client() -> IEEE2030_5_Client:
    yield IEEE2030_5_Client(cafile=SERVER_CA_CERT, ssl_port=8000)


def test_comm_002(client):
    """
    Purpose
Verify ability for client to connect to server using out-of-band (OOB) configured IP address, port number, and dcap path.
Setup
1. Server network/dcap related configuration (IP address, port number and dcap location) is known and available.
2. Client can configure its connection to use the Server network/dcap information.
Procedure
1. [T] Record the Client/Server communications.
2. [C] Configure the network/dcap related information to use the Server information and perform an HTTP GET operation on the DeviceCapability resource.
3. [S] Receive the incoming DeviceCapability HTTP GET request and respond back with the appropriate resource and response.
4. [C] Process the DeviceCapability response form the Server and perform additional HTTP GETs on one of the found resources.
5. [S] Receive the incoming HTTP GET request and send back the requested resource information as the HTTP GET response.
Pass/Fail Criteria
 [C] Client successfully uses the correct network/dcap information that is associated with the Server.
 [C] Client successfully issues HTTP GET on the DeviceCapability using the Server network/dcap information.
 [S] Server successfully responds to each of the HTTP GET request from the Client and returns the correct HTTP response and codes.
 [C] Client successfully issues additional HTTP GETs on one of the resources found in the DeviceCapability resource.
    """
    capability = client.request_device_capability()
    print(capability.EndDeviceListLink.href)

def test_comm_003(client):
    """
    COMM-003 - Basic Security [C,A,S]
Purpose
Verify ability to connect to server using HTTPS and IEEE 2030.5 permissible cypher suite.
The basic security test verifies that the Client can correctly communicate with an IEEE 2030.5 server using basic security requirements. For example, the HTTPS, TLS 1.2, TLS_ECDHE_ECDSA_WITH_AES_128_CCM_8 cipher suite. TLS authentications are tested based on requirements specified in the IEEE 2030.5 Application Protocol Specification.
Setup
1. Server and Client support the TLS based HTTP communication as specified in the Requirements, including the use of mandatory TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite.
2. Server is configured to use either the default TLS port (443) or another port. Client is configured to use the supported TLS port and IP address from the Server.
3. Client can send and receive TLS based HTTPS messages as specified in the requirements, including the use of mandatory TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite.
Procedure
1. [T] Record the Client/Server communications.
2. [C] Using the known IP address, port number, and DeviceCapability URI, send a TLS based HTTP GET request to the Server.
3. [S] Successfully receive the TLS based HTTP GET request and respond with the DeviceCapability resource payload through the TLS port number.
Pass/Fail Criteria
 [C] The Client successfully established a TLS HTTP session by conforming to the requirements specified in RFC 5246, section 7.4. Verify by inspecting the TLS packets, including verification that TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite was used. Successfully sent a TLS based HTTP GET request to the Server DeviceCapability resource using the known IP address, port number, and DeviceCapability URI.
 [S] Server successfully established a TLS HTTP session by conforming to the requirements specified in RFC 5246, section 7.4. Verify by inspecting the TLS packets, including verification that TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite was used. Successfully received the TLS based HTTP GET request and responded with the DeviceCapability resource payload as the HTTP GET response.
    """
    raise NotImplemented()


def test_comm_004(client):
    """
    COMM-004 - Advanced Security [C, A, S]
Purpose
Verify ability to detect errors in certificate chain of peer and reject the connection.
The advanced security test verifies that the Client can communicate with the IEEE 2030.5 server using basic TLS/security requirements and can also handle more challenging requirements, including invalid scenarios. For example, handling broken connections, invalid certificates, and invalid root CA.
Setup
1. Server and Client support the TLS based HTTP communication as specified in the Requirements, including the use of mandatory TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite and send TLS Alerts for error situations.
2. Server is configured to use either the default TLS port (443) or another port. Client is configured to use the supported TLS port and IP address from the Server.
3. Client can send and receive TLS based HTTPS messages as specified in the requirements, including the use of mandatory TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite and send TLS Alerts for error situations.
4. Server and Client support two, three, and four chain length TLS certs where:
 Certificate chain length two: SERCA -> Device Certificate
 Certificate chain length three: SERCA->MICA->Device Certificate
 Certificate chain length four: SERCA->MCA->MICA->Device Certificate
Refer to the IEEE 2030.5 standard, Certificate Management section.
5. Additional TLS certs with following attributes:
 Invalid MICA Extended Key Critical value
 Invalid MICA Name Non-Critical Value
 Invalid MICA Policy Mapping Non-Critical value
 Self-signed device certificate
Procedure
1. [T] Record the Client/Server communications.
2. [T] Configure with TLS cert, chain length two: SERCA->Device Certificate, to establish a new TLS session.
3. [C] Using the known IP address, port number, and DeviceCapability URI, send a TLS based HTTP GET request to the Server.
4. [S] Successfully receive the TLS based HTTP GET request and respond with the DeviceCapability resource payload through the TLS port number.
5. [T] Configure with TLS cert, chain length three: SERCA->MICA->Device Certificate, and start a new TLS session establishment and repeat test steps 2 and 3.
6. [T] Configure with TLS cert, chain length four: SERCA->MCA->MICA->Device certificate and start a new TLS session establishment and repeat test steps 2 and 3.
7. [T] Configure with TLS cert, Invalid MICA Extended Key Critical, and stat a new TLS session establishment and repeat test steps 2 and 3.
8. [T] Configure with TLS cert, Invalid MICA Name Non-Critical and stat a new TLS session establishment and repeat test steps 2 and 3.
9. [T] Configure with TLS cert, Invalid MICA Policy Mapping Non-Critical, and stat a new TLS session establishment and repeat test steps 2 and 3.
10. [T] Configure with TLS cert, Self-signed Cert, and stat a new TLS session establishment and repeat test steps 2 and 3.
Pass/Fail Criteria
 [T] The testing device successfully configured itself to use certificate chain length of two (SERCA->Device Certificate).
 [C] The Client successfully established a TLS HTTP session using TLS cert chain length of two by conforming to the requirements specified in RFC 5246, section 7.4. Verify by inspecting the TLS packets, including verification that TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite was used and cert chain length. Successfully sent a TLS based HTTP GET request to the Server DeviceCapability resource using the known IP address, port number, and DeviceCapability URI.
 [S] Server successfully established a TLS HTTP session using TLS cert chain length of two by conforming to the requirements specified in RFC 5246, section 7.4. Verify by inspecting the TLS packets, including verification that TLS_ECDHE_ECDSA_WITH _AES_128_CCM_8 cipher suite was used and cert chain length. Successfully received the TLS based HTTP GET request and responded with the DeviceCapability resource payload as the HTTP GET response.
 [U] The testing device successfully configured itself to use a certificate chain length of three (SERCA->MICA->Device Certificate). The Client and Server successfully passed Criteria 2 and 3, respectively, where chain length is three, instead of two.
 [U] The testing device successfully configured itself to use certificate chain length of four (SERCA->MCA->MICA->Device Certificate). The Client and Server successfully passed Criteria 2 and 3, respectively, where chain length is four, instead of two.
 [U] The testing device successfully configured itself to use an Invalid MICA Extended Key Critical cert but failed to receive a TLS connection. The device uder test responded with a TLS Alert indicating the invalid cert and failed to establish TLS connection with the testing device.
 [U] The testing device successfully configured itself to use an Invalid MICA Name Non-Critical cert but failed to receive a TLS connection. The device under test responded with a TLS Alert indicating the invalid cert and failed to establish TLS connection with Client.
 [U] The testing device successfully configured itself to use an Invalid MICA Policy Mapping Non-Critical cert but failed to receive a TLS connection. The device under test responded with a TLS Alert indicating the invalid cert and failed to establish TLS connection with the testing device.
 [U] The testing device successfully configured itself to use a self-signed cert but failed to receive a TLS connection. The device under test responded with a TLS Alert indicating the invalid cert and failed to establish TLS connection with testing device.
    """
    raise NotImplemented()



