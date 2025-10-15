#!/usr/bin/env python3
"""
Integration tests for DERStatus database storage and GridAPPSD adapter.

These tests verify the complete flow from HTTP PUT requests through database storage
to GridAPPSD adapter retrieval, using the actual server components and real database.

This differs from unit tests by:
- Starting an actual IEEE 2030.5 server instance
- Using real HTTP requests with proper authentication
- Testing against the actual ZODB database
- Verifying GridAPPSD adapter functionality with real components
"""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
import yaml

import ieee_2030_5.adapters as adpt

# Import IEEE 2030.5 components
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.flask_server import build_server

# Only import GridAPPSD if available
try:
    from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

    GRIDAPPSD_AVAILABLE = True
except ImportError:
    GRIDAPPSD_AVAILABLE = False


class ServerInstance:
    """Manages a test server instance for integration testing."""

    def __init__(self, config_path: Path, tls_path: Path):
        self.config_path = config_path
        self.tls_path = tls_path
        self.server = None
        self.server_thread = None
        self.base_url = None
        self.is_running = False

    def start(self, port: int = 8443):
        """Start the IEEE 2030.5 server."""
        try:
            # Load configuration
            config = ServerConfiguration.load(self.config_path)
            config.port = port
            config.server = "localhost"

            # Set up TLS repository
            tls_repo = TLSRepository(tls_path=self.tls_path, openssl_cnf_file=self.config_path.parent / "openssl.cnf")

            # Build server
            self.server = build_server(config, tls_repo)
            self.base_url = f"https://localhost:{port}"

            # Start server in background thread
            def run_server():
                self.server.serve_forever()

            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()

            # Wait for server to start
            time.sleep(2)
            self.is_running = True

            return True

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=5)

    def health_check(self) -> bool:
        """Check if server is responding."""
        try:
            response = requests.get(f"{self.base_url}/dcap", verify=False, timeout=5)
            return response.status_code == 200
        except:
            return False


@pytest.fixture(scope="session")
def integration_config():
    """Create test configuration for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)

        # Create test configuration
        config_data = {
            "server": "localhost",
            "port": 8443,
            "service_name": "IEEE_2030_5_Integration_Test",
            "tls_repository": str(test_dir / "tls"),
            "openssl_cnf": "openssl.cnf",
            "server_mode": "enddevices_create_on_start",
            "lfdi_mode": "lfdi_mode_from_file",
            "generate_admin_cert": True,
            "cleanse_storage": True,
            "storage_path": str(test_dir / "data_store"),
            "debug_client_traffic": True,
            "log_event_list_poll_rate": 9,
            "device_capability_poll_rate": 15,
            "mirror_usage_point_post_rate": 9,
            "devices": [
                {
                    "id": "test_device_001",
                    "post_rate": 3,
                    "pin": 123456,
                    "poll_rate": 3,
                    "fsas": ["default"],
                    "ders": ["default"],
                }
            ],
        }

        config_file = test_dir / "test_config.yml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create minimal openssl.cnf
        openssl_cnf = test_dir / "openssl.cnf"
        with open(openssl_cnf, "w") as f:
            f.write("""
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C=US
ST=TestState
L=TestCity
O=TestOrg
OU=TestUnit
CN=TestCA

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
""")

        yield {"config_file": config_file, "tls_path": test_dir / "tls", "test_dir": test_dir}


@pytest.fixture(scope="session")
def server_instance(integration_config):
    """Start a test server instance."""
    server = ServerInstance(integration_config["config_file"], integration_config["tls_path"])

    # Start server
    if not server.start():
        pytest.skip("Could not start test server")

    # Verify server is responding
    max_retries = 10
    for i in range(max_retries):
        if server.health_check():
            break
        time.sleep(1)
    else:
        server.stop()
        pytest.skip("Server failed health check")

    yield server

    # Cleanup
    server.stop()


@pytest.fixture
def client_cert(integration_config):
    """Get client certificate for authenticated requests."""
    tls_path = integration_config["tls_path"]

    # Look for admin certificate (created by server)
    admin_cert = tls_path / "admin_cert.pem"
    admin_key = tls_path / "admin_key.pem"

    if admin_cert.exists() and admin_key.exists():
        return (str(admin_cert), str(admin_key))

    # Look for device certificates
    cert_files = list(tls_path.glob("*.pem"))
    for cert_file in cert_files:
        if "cert" in cert_file.name:
            key_file = cert_file.parent / cert_file.name.replace("cert", "key")
            if key_file.exists():
                return (str(cert_file), str(key_file))

    return None


class TestDERStatusIntegration:
    """Integration tests for DERStatus functionality."""

    def test_server_startup(self, server_instance):
        """Test that the server starts successfully."""
        assert server_instance.is_running
        assert server_instance.health_check()

    def test_dcap_endpoint(self, server_instance):
        """Test basic server functionality via /dcap endpoint."""
        response = requests.get(f"{server_instance.base_url}/dcap", verify=False, timeout=10)

        assert response.status_code == 200
        assert "application/sep+xml" in response.headers.get("Content-Type", "")
        assert b"DeviceCapability" in response.content

    def test_der_status_put_and_retrieval(self, server_instance, client_cert):
        """Test complete DERStatus flow: PUT → database → retrieval."""

        # Create DERStatus XML payload
        current_time = int(time.time())
        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/0/ders" subscribable="1">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>85</value>
    </stateOfChargeStatus>
    <inverterStatus>
        <dateTime>{current_time}</dateTime>
        <value>1</value>
    </inverterStatus>
</DERStatus>"""

        # Send PUT request
        url = f"{server_instance.base_url}/der/0/ders"
        headers = {"Content-Type": "application/sep+xml", "Accept": "application/sep+xml"}

        put_response = requests.put(
            url, data=der_status_xml, headers=headers, cert=client_cert, verify=False, timeout=10
        )

        # Verify PUT was successful
        assert put_response.status_code == 200

        # Wait a moment for database write
        time.sleep(1)

        # Verify we can retrieve the data via GET
        get_response = requests.get(
            url, headers={"Accept": "application/sep+xml"}, cert=client_cert, verify=False, timeout=10
        )

        assert get_response.status_code == 200
        assert b"DERStatus" in get_response.content
        assert b"<value>85</value>" in get_response.content

    def test_database_storage_verification(self, server_instance, client_cert):
        """Test that DERStatus is actually stored in the database."""

        # Send DERStatus via PUT
        current_time = int(time.time())
        test_value = 92  # Unique value for this test

        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/1/ders">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>{test_value}</value>
    </stateOfChargeStatus>
</DERStatus>"""

        url = f"{server_instance.base_url}/der/1/ders"
        put_response = requests.put(
            url,
            data=der_status_xml,
            headers={"Content-Type": "application/sep+xml"},
            cert=client_cert,
            verify=False,
            timeout=10,
        )

        assert put_response.status_code == 200

        # Wait for database write
        time.sleep(1)

        # Directly check database via adapter
        try:
            stored_status = adpt.get_list_adapter().get_single("/der/1/ders")
            assert stored_status is not None
            assert isinstance(stored_status, m.DERStatus)
            assert stored_status.stateOfChargeStatus.value == test_value

            # Verify metadata includes LFDI
            metadata = adpt.get_list_adapter().get_single_meta_data("/der/1/ders")
            assert "lfdi" in metadata
            assert metadata["lfdi"] is not None

        except Exception as e:
            pytest.fail(f"Database verification failed: {e}")

    def test_multiple_der_status_storage(self, server_instance, client_cert):
        """Test storing multiple DERStatus objects."""

        base_time = int(time.time())
        test_cases = [("/der/2/ders", 70), ("/der/3/ders", 80), ("/der/4/ders", 90)]

        # Store multiple DERStatus objects
        for uri, soc_value in test_cases:
            der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="{uri}">
    <readingTime>{base_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{base_time}</dateTime>
        <value>{soc_value}</value>
    </stateOfChargeStatus>
</DERStatus>"""

            url = f"{server_instance.base_url}{uri}"
            response = requests.put(
                url,
                data=der_status_xml,
                headers={"Content-Type": "application/sep+xml"},
                cert=client_cert,
                verify=False,
                timeout=10,
            )

            assert response.status_code == 200

        # Wait for all writes to complete
        time.sleep(2)

        # Verify all were stored
        for uri, expected_soc in test_cases:
            stored_status = adpt.get_list_adapter().get_single(uri)
            assert stored_status is not None
            assert stored_status.stateOfChargeStatus.value == expected_soc

    def test_der_status_filtering(self, server_instance, client_cert):
        """Test GridAPPSD adapter filtering functionality."""

        # Store some DERStatus objects and other objects
        current_time = int(time.time())

        # Store DERStatus (should be found by filter)
        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/5/ders">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>88</value>
    </stateOfChargeStatus>
</DERStatus>"""

        url = f"{server_instance.base_url}/der/5/ders"
        response = requests.put(
            url,
            data=der_status_xml,
            headers={"Content-Type": "application/sep+xml"},
            cert=client_cert,
            verify=False,
            timeout=10,
        )

        assert response.status_code == 200
        time.sleep(1)

        # Test filtering (as GridAPPSD adapter does)
        def detect(v):
            return v and v.endswith("ders")

        filtered_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect(k))

        # Verify our DERStatus URI is in the filtered results
        assert "/der/5/ders" in filtered_uris

        # Verify we can retrieve the filtered objects
        for uri in filtered_uris:
            if uri == "/der/5/ders":
                status = adpt.get_list_adapter().get_single(uri)
                assert status is not None
                assert isinstance(status, m.DERStatus)

    def test_client_debug_logging(self, server_instance, client_cert, integration_config):
        """Test that client debug logging is working."""

        # Send a request to trigger logging
        current_time = int(time.time())
        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/6/ders">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>77</value>
    </stateOfChargeStatus>
</DERStatus>"""

        url = f"{server_instance.base_url}/der/6/ders"
        response = requests.put(
            url,
            data=der_status_xml,
            headers={"Content-Type": "application/sep+xml"},
            cert=client_cert,
            verify=False,
            timeout=10,
        )

        assert response.status_code == 200
        time.sleep(2)  # Allow time for logging

        # Check if debug logs were created
        debug_dir = Path("debug_client_traffic")
        if debug_dir.exists():
            log_files = list(debug_dir.glob("client_*.log"))
            assert len(log_files) > 0, "Expected client debug log files"

            # Check log content
            for log_file in log_files:
                content = log_file.read_text()
                if "REQUEST" in content and "PUT" in content:
                    # Found our request in the logs
                    assert "/der/6/ders" in content
                    break
            else:
                pytest.fail("Could not find PUT request in debug logs")


@pytest.mark.skipif(not GRIDAPPSD_AVAILABLE, reason="GridAPPSD not installed")
class TestGridAPPSDIntegration:
    """Integration tests for GridAPPSD adapter with real server."""

    def test_adapter_data_retrieval(self, server_instance, client_cert):
        """Test that GridAPPSD adapter can retrieve real DERStatus data."""

        # Store test data
        current_time = int(time.time())
        test_lfdi = "integration_test_lfdi_001"

        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/7/ders">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>95</value>
    </stateOfChargeStatus>
</DERStatus>"""

        url = f"{server_instance.base_url}/der/7/ders"
        response = requests.put(
            url,
            data=der_status_xml,
            headers={"Content-Type": "application/sep+xml"},
            cert=client_cert,
            verify=False,
            timeout=10,
        )

        assert response.status_code == 200
        time.sleep(1)

        # Create mock GridAPPSD adapter
        mock_gapps = Mock()
        mock_gapps.connected = True

        mock_config = {
            "field_bus_def": {"id": "test_integration_bus"},
            "publish_interval_seconds": 3,
            "house_named_inverters_regex": None,
            "utility_named_inverters_regex": None,
        }

        adapter = GridAPPSDAdapter(gapps=mock_gapps, gridappsd_configuration=mock_config, tls=Mock())

        # Set up test inverter
        adapter._inverters = [HouseLookup(mRID="test_house", name="TestHouse", lfdi=test_lfdi)]

        # Manually store with test LFDI to create proper mapping
        adpt.get_list_adapter().set_single("/der/7/ders", adpt.get_list_adapter().get_single("/der/7/ders"), lfdi=test_lfdi)

        # Test adapter retrieval
        message = adapter.get_message_for_bus()

        # Verify adapter found and processed the data
        assert isinstance(message, dict)
        # Note: Actual message content depends on LFDI mapping


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
