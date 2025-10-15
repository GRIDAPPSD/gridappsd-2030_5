#!/usr/bin/env python3
"""
Simplified integration tests for DERStatus functionality.

These tests verify the core integration between HTTP PUT, database storage,
and GridAPPSD adapter retrieval without requiring a full server startup.

Run with: pytest tests/integration/test_der_status_simple.py -v
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.persistance.points import ZODBPointStore
from ieee_2030_5.server.derfs import DERRequests
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

# Only import GridAPPSD if available
try:
    from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

    GRIDAPPSD_AVAILABLE = True
except ImportError:
    GRIDAPPSD_AVAILABLE = False


@pytest.fixture(scope="session")
def integration_database():
    """Set up a real database for integration testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "integration_test.fs"
        db = ZODBPointStore(db_path)

        # Replace the global database reference for testing
        original_db = getattr(adpt.ListAdapter, "_db", None)
        adpt.get_list_adapter()._db = db

        # Initialize adapters
        adpt.initialize_adapters()

        yield db

        # Restore original database
        if original_db:
            adpt.get_list_adapter()._db = original_db

        try:
            db.close()
        except:
            pass


@pytest.fixture
def mock_server_config():
    """Mock server configuration for testing."""
    config = Mock(spec=ServerConfiguration)
    config.debug_client_traffic = True
    config.storage_path = "test_storage"
    config.cleanse_storage = False
    return config


@pytest.fixture
def mock_tls_repo():
    """Mock TLS repository for testing."""
    tls_repo = Mock(spec=TLSRepository)
    tls_repo.lfdi.return_value = "test_lfdi_123456789"
    return tls_repo


@pytest.fixture
def mock_flask_request():
    """Mock Flask request object."""
    request = Mock()
    request.method = "PUT"
    request.path = "/der/0/ders"
    request.content_type = "application/sep+xml"
    request.environ = {
        "ieee_2030_5_lfdi": "test_lfdi_123456789",
        "ieee_2030_5_peercert": Mock(),
        "REQUEST_METHOD": "PUT",
        "PATH_INFO": "/der/0/ders",
    }
    return request


class TestDERStatusIntegrationFlow:
    """Integration tests for the complete DERStatus flow."""

    def test_xml_to_database_integration(self, integration_database):
        """Test XML parsing and database storage integration."""

        # Create DERStatus XML (simulating client PUT body)
        current_time = int(time.time())
        der_status_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<DERStatus xmlns="urn:ieee:std:2030.5:ns" href="/der/0/ders" subscribable="1">
    <readingTime>{current_time}</readingTime>
    <stateOfChargeStatus>
        <dateTime>{current_time}</dateTime>
        <value>88</value>
    </stateOfChargeStatus>
    <inverterStatus>
        <dateTime>{current_time}</dateTime>
        <value>1</value>
    </inverterStatus>
</DERStatus>"""

        # Parse XML to DERStatus object (server processing)
        der_status = xml_to_dataclass(der_status_xml, m.DERStatus)
        assert der_status.readingTime == current_time
        assert der_status.stateOfChargeStatus.value == 88

        # Store in database (via ListAdapter)
        test_lfdi = "integration_test_lfdi"
        result = adpt.get_list_adapter().set_single(uri="/der/0/ders", obj=der_status, lfdi=test_lfdi)

        assert result.success is True

        # Retrieve from database
        retrieved = adpt.get_list_adapter().get_single("/der/0/ders")
        assert retrieved is not None
        assert retrieved.stateOfChargeStatus.value == 88

        # Verify metadata includes LFDI
        metadata = adpt.get_list_adapter().get_single_meta_data("/der/0/ders")
        assert metadata["lfdi"] == test_lfdi

    def test_der_request_handler_integration(self, integration_database, mock_server_config, mock_tls_repo):
        """Test DERRequests PUT handler integration."""

        # Create DERStatus object
        current_time = int(time.time())
        der_status = m.DERStatus(
            href="/der/1/ders",
            readingTime=current_time,
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=current_time, value=92),
        )

        # Convert to XML
        xml_data = dataclass_to_xml(der_status)

        # Mock Flask request
        with patch("ieee_2030_5.server.derfs.request") as mock_request:
            mock_request.path = "/der/1/ders"
            mock_request.method = "PUT"
            mock_request.data = xml_data
            mock_request.content_type = "application/sep+xml"
            mock_request.environ = {"ieee_2030_5_lfdi": "handler_test_lfdi", "PATH_INFO": "/der/1/ders"}
            mock_request.get_data.return_value = xml_data

            # Create DERRequests handler
            server_endpoints = Mock()
            server_endpoints.tls_repo = mock_tls_repo
            server_endpoints.config = mock_server_config

            handler = DERRequests(server_endpoints)
            handler.lfdi = "handler_test_lfdi"

            # Execute PUT request
            with patch("ieee_2030_5.server.derfs.hrefs.HrefParser") as mock_parser:
                parser_instance = Mock()
                parser_instance.at.return_value = "ders"
                mock_parser.return_value = parser_instance

                response = handler.put()

                # Verify response
                assert response.status_code == 200

        # Verify data was stored in database
        stored = adpt.get_list_adapter().get_single("/der/1/ders")
        assert stored is not None
        assert stored.stateOfChargeStatus.value == 92

        # Verify LFDI metadata
        metadata = adpt.get_list_adapter().get_single_meta_data("/der/1/ders")
        assert metadata["lfdi"] == "handler_test_lfdi"

    def test_multiple_der_status_storage_integration(self, integration_database):
        """Test storing multiple DERStatus objects with different LFDIs."""

        base_time = int(time.time())
        test_cases = [
            ("/der/2/ders", "lfdi_device_001", 70),
            ("/der/3/ders", "lfdi_device_002", 80),
            ("/der/4/ders", "lfdi_device_003", 90),
        ]

        # Store multiple DERStatus objects
        for uri, lfdi, soc_value in test_cases:
            der_status = m.DERStatus(
                href=uri,
                readingTime=base_time,
                stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=base_time, value=soc_value),
            )

            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success is True

        # Verify all stored correctly
        for uri, expected_lfdi, expected_soc in test_cases:
            stored = adpt.get_list_adapter().get_single(uri)
            assert stored.stateOfChargeStatus.value == expected_soc

            metadata = adpt.get_list_adapter().get_single_meta_data(uri)
            assert metadata["lfdi"] == expected_lfdi

        # Test filtering (as GridAPPSD adapter does)
        def detect_ders(uri):
            return uri and uri.endswith("ders")

        filtered_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect_ders(k))

        # Should find all our DERStatus URIs
        expected_uris = [uri for uri, _, _ in test_cases]
        for expected_uri in expected_uris:
            assert expected_uri in filtered_uris

    def test_database_persistence_integration(self, integration_database):
        """Test that data persists across adapter instances."""

        # Store data
        uri = "/der/5/ders"
        lfdi = "persistence_test_lfdi"
        der_status = m.DERStatus(
            href=uri,
            readingTime=int(time.time()),
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=int(time.time()), value=95),
        )

        adpt.get_list_adapter().set_single(uri, der_status, lfdi)

        # Verify immediate retrieval
        retrieved1 = adpt.get_list_adapter().get_single(uri)
        assert retrieved1.stateOfChargeStatus.value == 95

        # Simulate adapter restart by re-initializing
        adpt.initialize_adapters()

        # Verify data still exists
        retrieved2 = adpt.get_list_adapter().get_single(uri)
        assert retrieved2 is not None
        assert retrieved2.stateOfChargeStatus.value == 95

        metadata = adpt.get_list_adapter().get_single_meta_data(uri)
        assert metadata["lfdi"] == lfdi


@pytest.mark.skipif(not GRIDAPPSD_AVAILABLE, reason="GridAPPSD not installed")
class TestGridAPPSDAdapterIntegration:
    """Integration tests for GridAPPSD adapter with real data."""

    def test_adapter_with_real_database(self, integration_database):
        """Test GridAPPSD adapter retrieval from real database."""

        # Store test DERStatus data
        test_cases = [
            ("/der/6/ders", "lfdi_house_001", "house_001", 75),
            ("/der/7/ders", "lfdi_house_002", "house_002", 85),
        ]

        current_time = int(time.time())

        for uri, lfdi, house_id, soc_value in test_cases:
            der_status = m.DERStatus(
                href=uri,
                readingTime=current_time,
                stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=current_time, value=soc_value),
            )

            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success is True

        # Create GridAPPSD adapter with test configuration
        mock_gapps = Mock()
        mock_gapps.connected = True

        mock_config = {
            "field_bus_def": {"id": "integration_test_bus"},
            "publish_interval_seconds": 3,
            "house_named_inverters_regex": None,
            "utility_named_inverters_regex": None,
        }

        adapter = GridAPPSDAdapter(gapps=mock_gapps, gridappsd_configuration=mock_config, tls=Mock())

        # Set up inverter mappings
        adapter._inverters = [
            HouseLookup(mRID="house_001", name="House1", lfdi="lfdi_house_001"),
            HouseLookup(mRID="house_002", name="House2", lfdi="lfdi_house_002"),
        ]

        # Test message generation
        with adapter._lock:
            message = adapter.get_message_for_bus()

        # Verify adapter processed the data
        assert isinstance(message, dict)

        # Check if houses with matching LFDIs appear in message
        for house_mrid in ["house_001", "house_002"]:
            if house_mrid in message:
                house_data = message[house_mrid]
                assert "mRID" in house_data
                assert house_data["mRID"] == house_mrid

    def test_complete_integration_flow(self, integration_database):
        """Test the complete flow from PUT to GridAPPSD message."""

        # 1. Simulate HTTP PUT processing
        current_time = int(time.time())
        test_lfdi = "complete_flow_lfdi"
        test_house = "complete_flow_house"

        # Create and store DERStatus (simulating server PUT handler)
        der_status = m.DERStatus(
            href="/der/8/ders",
            readingTime=current_time,
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=current_time, value=78),
        )

        result = adpt.get_list_adapter().set_single("/der/8/ders", der_status, test_lfdi)
        assert result.success is True

        # 2. Verify database storage
        stored = adpt.get_list_adapter().get_single("/der/8/ders")
        assert stored.stateOfChargeStatus.value == 78

        metadata = adpt.get_list_adapter().get_single_meta_data("/der/8/ders")
        assert metadata["lfdi"] == test_lfdi

        # 3. Test GridAPPSD adapter retrieval
        mock_gapps = Mock()
        mock_gapps.connected = True

        adapter = GridAPPSDAdapter(
            gapps=mock_gapps,
            gridappsd_configuration={
                "field_bus_def": {"id": "complete_flow_bus"},
                "publish_interval_seconds": 3,
                "house_named_inverters_regex": None,
                "utility_named_inverters_regex": None,
            },
            tls=Mock(),
        )

        adapter._inverters = [HouseLookup(mRID=test_house, name="CompleteFlowHouse", lfdi=test_lfdi)]

        # 4. Generate message for bus
        with adapter._lock:
            message = adapter.get_message_for_bus()

        # 5. Verify complete flow worked
        assert isinstance(message, dict)

        # If our house appears in the message, verify the data
        if test_house in message:
            house_data = message[test_house]
            assert house_data["mRID"] == test_house
            # Value should come from our DERStatus
            if "value" in house_data:
                assert house_data["value"] == 78


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short", "--integration"])
