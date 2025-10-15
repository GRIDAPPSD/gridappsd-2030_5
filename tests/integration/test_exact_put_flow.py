#!/usr/bin/env python3
"""
Test the exact PUT flow from the captured request data to database storage.

This test simulates the exact HTTP PUT request that was captured:
- Path: /der_10_ders (custom underscore format)
- LFDI: 8c0caca6961d3ddb1faca475cd14ec6df32c846a
- CN: _CA0A0024-DA79-4395-9B05-6A7B9DE0AED9
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import ieee_2030_5.adapters as adpt
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.persistance.points import ZODBPointStore
from ieee_2030_5.server.derfs import DERRequests
from ieee_2030_5.utils import xml_to_dataclass


@pytest.fixture(scope="session")
def exact_flow_database():
    """Set up database for exact flow testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "exact_flow_test.fs"
        db = ZODBPointStore(db_path)

        # Replace global database
        original_db = getattr(adpt.ListAdapter, "_db", None)
        adpt.get_list_adapter()._db = db
        adpt.initialize_adapters()

        yield db

        # Restore
        if original_db:
            adpt.get_list_adapter()._db = original_db

        try:
            if hasattr(db, "_storage"):
                db._storage.close()
            if hasattr(db, "_db"):
                db._db.close()
        except Exception:
            pass


class TestExactPUTFlow:
    """Test the exact PUT flow from captured request to database."""

    def test_exact_der_status_put_flow(self, exact_flow_database):
        """Test the complete flow using exact captured request data."""

        print("\n🔍 Testing Exact PUT Flow")
        print("=" * 50)

        # Exact data from the captured request
        captured_data = {
            "timestamp": "2025-08-19T19:42:04.775782",
            "request_id": "ebe644e5",
            "type": "REQUEST",
            "lfdi": "8c0caca6961d3ddb1faca475cd14ec6df32c846a",
            "cn": "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9",
            "method": "PUT",
            "path": "/der_10_ders",  # Custom underscore format
            "content_type": "application/sep+xml",
            "body": """<DERStatus xmlns="urn:ieee:std:2030.5:ns">
  <readingTime>1755657724</readingTime>
  <stateOfChargeStatus>
    <dateTime>-2209075200</dateTime>
    <value>6600</value>
  </stateOfChargeStatus>
</DERStatus>""",
        }

        print("📋 Request Details:")
        print(f"  - Path: {captured_data['path']}")
        print(f"  - LFDI: {captured_data['lfdi']}")
        print(f"  - CN: {captured_data['cn']}")
        print("  - SOC Value: 6600")

        # Step 1: Parse the XML (simulating server XML processing)
        print("\n1️⃣ Parsing DERStatus XML...")
        der_status_xml = captured_data["body"]
        der_status = xml_to_dataclass(der_status_xml, m.DERStatus)

        print("✅ Parsed DERStatus:")
        print(f"  - Reading Time: {der_status.readingTime}")
        print(f"  - SOC Value: {der_status.stateOfChargeStatus.value}")
        print(f"  - SOC DateTime: {der_status.stateOfChargeStatus.dateTime}")

        # Step 2: Store in database using exact path and LFDI
        print("\n2️⃣ Storing in database...")
        uri = captured_data["path"]  # /der_10_ders
        lfdi = captured_data["lfdi"]

        result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
        print(f"✅ Storage result: {result.success}")
        assert result.success is True

        # Step 3: Verify data is stored correctly
        print("\n3️⃣ Verifying storage...")
        stored = adpt.get_list_adapter().get_single(uri)
        assert stored is not None
        assert isinstance(stored, m.DERStatus)
        assert stored.stateOfChargeStatus.value == 6600
        print("✅ Data verified in database")

        # Step 4: Check metadata
        print("\n4️⃣ Checking metadata...")
        metadata = adpt.get_list_adapter().get_single_meta_data(uri)
        assert metadata["lfdi"] == lfdi
        print(f"✅ LFDI mapping verified: {metadata['lfdi']}")

        # Step 5: Test GridAPPSD adapter filtering
        print("\n5️⃣ Testing GridAPPSD adapter filtering...")

        # Test the exact filter used by GridAPPSD adapter
        def detect_ders(uri_key):
            return uri_key and uri_key.endswith("ders")

        filtered_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect_ders(k))

        print(f"📊 Filtered URIs: {filtered_uris}")
        assert uri in filtered_uris  # /der_10_ders should be found
        print("✅ Custom path format works with GridAPPSD filter")

        # Step 6: Simulate complete GridAPPSD adapter retrieval
        print("\n6️⃣ Simulating GridAPPSD adapter retrieval...")

        # This simulates what get_message_for_bus() does
        message_data = {}

        for uri_key in filtered_uris:
            try:
                # Get metadata
                meta = adpt.get_list_adapter().get_single_meta_data(uri_key)
                status = adpt.get_list_adapter().get_single(uri_key)

                # Simulate inverter lookup (would normally match LFDI to house)
                # For this test, we'll create a mock inverter match
                if meta.get("lfdi") == lfdi:
                    # Mock inverter data
                    mock_inverter = Mock()
                    mock_inverter.mRID = "house_10"
                    mock_inverter.name = "TestHouse10"
                    mock_inverter.lfdi = lfdi

                    # Create message data (as GridAPPSD adapter would)
                    if status.stateOfChargeStatus:
                        message_data[mock_inverter.mRID] = {
                            "mRID": mock_inverter.mRID,
                            "name": mock_inverter.name,
                            "value": status.stateOfChargeStatus.value,
                            "timeStamp": status.readingTime,
                        }

            except Exception as e:
                print(f"⚠️  Error processing {uri_key}: {e}")

        print(f"📊 GridAPPSD message data: {message_data}")
        assert len(message_data) == 1
        assert message_data["house_10"]["value"] == 6600
        print("✅ Complete flow successful!")

        return {
            "stored_der_status": stored,
            "metadata": metadata,
            "filtered_uris": filtered_uris,
            "message_data": message_data,
        }

    def test_custom_path_format_filtering(self, exact_flow_database):
        """Test that custom underscore path format works with filtering."""

        # Store multiple DERStatus objects with custom paths
        test_cases = [
            ("/der_10_ders", "lfdi_test_10", 6600),
            ("/der_15_ders", "lfdi_test_15", 7200),
            ("/der_20_ders", "lfdi_test_20", 5500),
            ("/der_10_derc", "lfdi_test_10_ctrl", 100),  # Should NOT match
            ("/derp_10", "lfdi_test_program", 200),  # Should NOT match
        ]

        print("\n🔍 Testing Custom Path Format Filtering")
        print("=" * 50)

        # Store all test data
        for uri, lfdi, value in test_cases:
            der_status = m.DERStatus(
                href=uri,
                readingTime=1755657724,
                stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=-2209075200, value=value),
            )

            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success is True
            print(f"📝 Stored: {uri} -> SOC: {value}")

        # Test filtering for DERStatus (ends with "ders")
        ders_filter = lambda k: k and k.endswith("ders")
        ders_uris = adpt.get_list_adapter().filter_single_dict(ders_filter)

        print(f"\n📊 DERStatus URIs found: {len(ders_uris)}")
        for uri in ders_uris:
            print(f"  - {uri}")

        # Verify correct filtering
        expected_ders = [uri for uri, _, _ in test_cases if uri.endswith("ders")]
        assert len(ders_uris) == len(expected_ders)

        for expected_uri in expected_ders:
            assert expected_uri in ders_uris

        # Verify excluded URIs
        assert "/der_10_derc" not in ders_uris
        assert "/derp_10" not in ders_uris

        print("✅ Custom underscore format filtering works correctly!")

    def test_mock_http_put_handler(self, exact_flow_database):
        """Test HTTP PUT handler with exact request simulation."""

        print("\n🌐 Testing HTTP PUT Handler Simulation")
        print("=" * 50)

        # Mock server configuration
        mock_config = Mock(spec=ServerConfiguration)
        mock_config.debug_client_traffic = True
        mock_config.storage_path = "test_storage"

        # Mock TLS repository
        mock_tls = Mock(spec=TLSRepository)
        mock_tls.lfdi.return_value = "8c0caca6961d3ddb1faca475cd14ec6df32c846a"

        # Exact XML from captured request
        der_status_xml = """<DERStatus xmlns="urn:ieee:std:2030.5:ns">
  <readingTime>1755657724</readingTime>
  <stateOfChargeStatus>
    <dateTime>-2209075200</dateTime>
    <value>6600</value>
  </stateOfChargeStatus>
</DERStatus>"""

        # Mock Flask request with exact captured data
        with patch("ieee_2030_5.server.derfs.request") as mock_request:
            mock_request.path = "/der_10_ders"  # Custom format
            mock_request.method = "PUT"
            mock_request.data = der_status_xml.encode("utf-8")
            mock_request.content_type = "application/sep+xml"
            mock_request.environ = {
                "ieee_2030_5_lfdi": "8c0caca6961d3ddb1faca475cd14ec6df32c846a",
                "ieee_2030_5_cn": "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9",
                "PATH_INFO": "/der_10_ders",
            }
            mock_request.get_data.return_value = der_status_xml.encode("utf-8")

            # Create DERRequests handler
            server_endpoints = Mock()
            server_endpoints.tls_repo = mock_tls
            server_endpoints.config = mock_config

            handler = DERRequests(server_endpoints)
            handler.lfdi = "8c0caca6961d3ddb1faca475cd14ec6df32c846a"

            # Mock the URL parsing to return "ders" for our custom format
            with patch("ieee_2030_5.server.derfs.hrefs.HrefParser") as mock_parser:
                parser_instance = Mock()
                parser_instance.at.return_value = "ders"  # This identifies it as DERStatus
                mock_parser.return_value = parser_instance

                print("📡 Executing PUT handler...")
                response = handler.put()

                print(f"✅ Response Status: {response.status_code}")
                assert response.status_code == 200

        # Verify data was stored
        stored = adpt.get_list_adapter().get_single("/der_10_ders")
        assert stored is not None
        assert stored.stateOfChargeStatus.value == 6600

        metadata = adpt.get_list_adapter().get_single_meta_data("/der_10_ders")
        assert metadata["lfdi"] == "8c0caca6961d3ddb1faca475cd14ec6df32c846a"

        print("✅ Complete PUT handler flow successful!")


if __name__ == "__main__":
    # Run the exact PUT flow tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
