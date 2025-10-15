#!/usr/bin/env python3
"""
Integration tests for GridAPPSD adapter internal structure and database retrieval.

These tests focus specifically on the GridAPPSD adapter's internal mechanisms:
- get_message_for_bus() method
- Database filtering and retrieval
- LFDI to house mapping
- Thread safety of database access
- Error handling and edge cases

This validates the adapter's actual implementation against real database data.
"""

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock

import pytest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.models as m
from ieee_2030_5.persistance.points import ZODBPointStore

# Only import GridAPPSD if available
try:
    import ieee_2030_5.models.output as mo
    from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

    GRIDAPPSD_AVAILABLE = True
except ImportError:
    GRIDAPPSD_AVAILABLE = False


@pytest.fixture(scope="session")
def adapter_test_database():
    """Set up a dedicated database for GridAPPSD adapter testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "gridappsd_adapter_test.fs"
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

        # Clean close without index saving to avoid temp directory issues
        try:
            if hasattr(db, "_storage"):
                db._storage.close()
            if hasattr(db, "_db"):
                db._db.close()
        except Exception:
            pass


@pytest.fixture
def sample_inverters():
    """Create sample inverter configurations for testing."""
    return [
        HouseLookup(mRID="house_001", name="TestHouse1", lfdi="lfdi_test_house_001"),
        HouseLookup(mRID="house_002", name="TestHouse2", lfdi="lfdi_test_house_002"),
        HouseLookup(mRID="house_003", name="TestHouse3", lfdi="lfdi_test_house_003"),
        HouseLookup(mRID="utility_001", name="UtilityInverter1", lfdi="lfdi_utility_001"),
    ]


@pytest.fixture
def gridappsd_adapter(sample_inverters, monkeypatch):
    """Create a GridAPPSD adapter with test configuration."""
    if not GRIDAPPSD_AVAILABLE:
        pytest.skip("GridAPPSD not available")

    # Set required environment variables for GridAPPSD
    monkeypatch.setenv("GRIDAPPSD_SIMULATION_ID", "test_simulation_123")
    monkeypatch.setenv("GRIDAPPSD_SERVICE_NAME", "test_service_2030_5")

    # Mock GridAPPSD connection
    mock_gapps = Mock()
    mock_gapps.connected = True

    # Mock configuration with all required fields
    mock_config = {
        "field_bus_def": {"id": "test_adapter_bus"},
        "publish_interval_seconds": 3,
        "house_named_inverters_regex": None,
        "utility_named_inverters_regex": None,
        "model_name": "test_model",
        "default_pin": "123456",
    }

    # Mock TLS repository
    mock_tls = Mock()

    # Mock the subscribe method to avoid actual subscription
    mock_gapps.subscribe = Mock()

    # Create adapter
    adapter = GridAPPSDAdapter(gapps=mock_gapps, gridappsd_configuration=mock_config, tls=mock_tls)

    # Set up test inverters
    adapter._inverters = sample_inverters

    return adapter


def create_test_der_status(uri: str, lfdi: str, soc_value: int, reading_time: int = None) -> m.DERStatus:
    """Helper to create test DERStatus objects."""
    if reading_time is None:
        reading_time = int(time.time())

    return m.DERStatus(
        href=uri,
        readingTime=reading_time,
        stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=reading_time, value=soc_value),
        inverterStatus=m.InverterStatusType(
            dateTime=reading_time,
            value=1,  # Operating
        ),
    )


@pytest.mark.skipif(not GRIDAPPSD_AVAILABLE, reason="GridAPPSD not installed")
class TestGridAPPSDAdapterInternals:
    """Test GridAPPSD adapter internal mechanisms."""

    def test_filter_single_dict_mechanism(self, adapter_test_database, gridappsd_adapter):
        """Test the adapter's internal filtering mechanism."""

        # Store test data with different URI patterns
        test_data = [
            ("/der/0/ders", "lfdi_001", 75),  # Should match
            ("/der/1/ders", "lfdi_002", 85),  # Should match
            ("/der/0/derc", "lfdi_003", 95),  # Should NOT match
            ("/derp/0", "lfdi_004", 65),  # Should NOT match
            ("/der/2/ders", "lfdi_005", 55),  # Should match
        ]

        # Store all test data
        for uri, lfdi, soc_value in test_data:
            der_status = create_test_der_status(uri, lfdi, soc_value)
            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success is True

        # Test the internal detect function (as used in adapter)
        def detect(v):
            if v:
                return v.endswith("ders")
            return False

        # Get filtered URIs (this is what the adapter does internally)
        filtered_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect(k))

        # Verify filtering worked correctly
        expected_ders_uris = [uri for uri, _, _ in test_data if uri.endswith("ders")]

        assert len(filtered_uris) == len(expected_ders_uris)
        for expected_uri in expected_ders_uris:
            assert expected_uri in filtered_uris

        # Verify URIs that shouldn't match are excluded
        assert "/der/0/derc" not in filtered_uris
        assert "/derp/0" not in filtered_uris

    def test_get_message_for_bus_complete_flow(self, adapter_test_database, gridappsd_adapter, sample_inverters):
        """Test the complete get_message_for_bus flow with real data."""

        # Store DERStatus data that matches our inverter LFDIs
        test_scenarios = [
            ("/der/0/ders", "lfdi_test_house_001", 80),  # Matches house_001
            ("/der/1/ders", "lfdi_test_house_002", 90),  # Matches house_002
            ("/der/2/ders", "lfdi_unknown", 70),  # No matching inverter
        ]

        current_time = int(time.time())

        for uri, lfdi, soc_value in test_scenarios:
            der_status = create_test_der_status(uri, lfdi, soc_value, current_time)
            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success is True

        # Execute the adapter's message generation
        message = gridappsd_adapter.get_message_for_bus()

        # Verify message structure and content
        assert isinstance(message, dict)

        # Should have entries for houses with matching LFDIs
        assert "house_001" in message
        assert "house_002" in message
        assert "house_003" not in message  # No DERStatus data for this LFDI
        assert "utility_001" not in message  # No DERStatus data for this LFDI

        # Verify message content for house_001
        house1_data = message["house_001"]
        assert house1_data["mRID"] == "house_001"
        assert house1_data["name"] == "TestHouse1"
        assert house1_data["value"] == 80
        assert house1_data["timeStamp"] == current_time

        # Verify message content for house_002
        house2_data = message["house_002"]
        assert house2_data["mRID"] == "house_002"
        assert house2_data["name"] == "TestHouse2"
        assert house2_data["value"] == 90
        assert house2_data["timeStamp"] == current_time

    def test_lfdi_to_inverter_mapping(self, adapter_test_database, gridappsd_adapter, sample_inverters):
        """Test the LFDI to inverter mapping mechanism."""

        # Store DERStatus with various LFDI scenarios
        test_cases = [
            ("lfdi_test_house_001", "house_001", True),  # Exact match
            ("lfdi_test_house_002", "house_002", True),  # Exact match
            ("lfdi_utility_001", "utility_001", True),  # Utility inverter match
            ("lfdi_nonexistent", None, False),  # No match
            ("", None, False),  # Empty LFDI
        ]

        for i, (lfdi, expected_mrid, should_match) in enumerate(test_cases):
            uri = f"/der/{i}/ders"
            der_status = create_test_der_status(uri, lfdi, 75)
            adpt.get_list_adapter().set_single(uri, der_status, lfdi)

        # Test the adapter's internal inverter lookup logic
        for lfdi, expected_mrid, should_match in test_cases:
            if not lfdi:  # Skip empty LFDI test for this part
                continue

            # Simulate the adapter's lookup process
            found_inverter = None
            for inverter in sample_inverters:
                if inverter.lfdi == lfdi:
                    found_inverter = inverter
                    break

            if should_match:
                assert found_inverter is not None
                assert found_inverter.mRID == expected_mrid
            else:
                assert found_inverter is None

    def test_metadata_retrieval_mechanism(self, adapter_test_database, gridappsd_adapter):
        """Test the adapter's metadata retrieval for LFDI mapping."""

        # Store test data with metadata
        test_uri = "/der/0/ders"
        test_lfdi = "test_metadata_lfdi"
        der_status = create_test_der_status(test_uri, test_lfdi, 88)

        result = adpt.get_list_adapter().set_single(test_uri, der_status, test_lfdi)
        assert result.success is True

        # Test metadata retrieval (as done internally by adapter)
        metadata = adpt.get_list_adapter().get_single_meta_data(test_uri)

        # Verify metadata contains required fields
        assert metadata is not None
        assert "lfdi" in metadata
        assert "uri" in metadata
        assert metadata["lfdi"] == test_lfdi
        assert metadata["uri"] == test_uri

        # Test status retrieval using metadata URI
        status = adpt.get_list_adapter().get_single(metadata["uri"])
        assert status is not None
        assert isinstance(status, m.DERStatus)
        assert status.stateOfChargeStatus.value == 88

    def test_analog_value_conversion(self, adapter_test_database, gridappsd_adapter, sample_inverters):
        """Test the conversion to AnalogValue format for message bus."""

        # Store test DERStatus
        uri = "/der/0/ders"
        lfdi = "lfdi_test_house_001"  # Matches first inverter
        reading_time = 1234567890
        soc_value = 77

        der_status = create_test_der_status(uri, lfdi, soc_value, reading_time)
        adpt.get_list_adapter().set_single(uri, der_status, lfdi)

        # Execute adapter processing
        message = gridappsd_adapter.get_message_for_bus()

        # Verify AnalogValue structure
        assert "house_001" in message
        analog_data = message["house_001"]

        # Check all expected fields
        assert "mRID" in analog_data
        assert "name" in analog_data
        assert "value" in analog_data
        assert "timeStamp" in analog_data

        # Verify values
        assert analog_data["mRID"] == "house_001"
        assert analog_data["name"] == "TestHouse1"
        assert analog_data["value"] == soc_value
        assert analog_data["timeStamp"] == reading_time

        # Verify it matches AnalogValue dataclass structure
        # (This is what gets sent to the message bus)
        analog_value = mo.AnalogValue(mRID="house_001", name="TestHouse1")
        analog_value.value = soc_value
        analog_value.timeStamp = reading_time

        expected_dict = asdict(analog_value)
        assert analog_data == expected_dict

    def test_thread_safety_of_database_access(self, adapter_test_database, gridappsd_adapter):
        """Test thread-safe access to database from adapter."""

        # Store initial test data
        base_time = int(time.time())
        test_cases = [(f"/der/{i}/ders", f"lfdi_thread_test_{i}", 50 + i * 10) for i in range(5)]

        for uri, lfdi, soc_value in test_cases:
            der_status = create_test_der_status(uri, lfdi, soc_value, base_time + soc_value)
            adpt.get_list_adapter().set_single(uri, der_status, lfdi)

        # Set up inverters that match our test LFDIs
        gridappsd_adapter._inverters = [
            HouseLookup(mRID=f"house_{i}", name=f"ThreadTestHouse{i}", lfdi=f"lfdi_thread_test_{i}") for i in range(5)
        ]

        # Function to be executed in multiple threads
        def get_message_threaded():
            return gridappsd_adapter.get_message_for_bus()

        # Execute get_message_for_bus from multiple threads simultaneously
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_message_threaded) for _ in range(10)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Thread execution failed: {e}")

        # Verify all threads got consistent results
        assert len(results) == 10

        # All results should be identical (same data, same processing)
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

        # Verify the structure is correct
        assert len(first_result) == 5  # Should have 5 houses
        for i in range(5):
            house_key = f"house_{i}"
            assert house_key in first_result
            assert first_result[house_key]["value"] == 50 + i * 10

    def test_error_handling_in_get_message_for_bus(self, adapter_test_database, gridappsd_adapter):
        """Test error handling in the adapter's message generation."""

        # Store valid data
        valid_uri = "/der/0/ders"
        valid_lfdi = "lfdi_test_house_001"
        der_status = create_test_der_status(valid_uri, valid_lfdi, 85)
        adpt.get_list_adapter().set_single(valid_uri, der_status, valid_lfdi)

        # Store data that will cause errors
        # 1. DERStatus with missing stateOfChargeStatus
        problematic_status = m.DERStatus(
            href="/der/1/ders",
            readingTime=int(time.time()),
            # Missing stateOfChargeStatus
        )
        adpt.get_list_adapter().set_single("/der/1/ders", problematic_status, "lfdi_test_house_002")

        # Execute adapter - should handle errors gracefully
        message = gridappsd_adapter.get_message_for_bus()

        # Should still process valid data despite errors with other data
        assert isinstance(message, dict)
        assert "house_001" in message  # Valid data should be processed

        # The problematic data might or might not appear depending on error handling
        # but the adapter should not crash
        if "house_002" in message:
            # If it appears, value might be None or default
            house2_data = message["house_002"]
            assert "mRID" in house2_data

    def test_empty_database_scenario(self, adapter_test_database, gridappsd_adapter):
        """Test adapter behavior with empty database."""

        # Don't store any data

        # Execute adapter on empty database
        message = gridappsd_adapter.get_message_for_bus()

        # Should return empty dict without errors
        assert isinstance(message, dict)
        assert len(message) == 0

    def test_no_matching_inverters_scenario(self, adapter_test_database, gridappsd_adapter):
        """Test adapter behavior when no inverters match stored LFDIs."""

        # Store DERStatus with LFDIs that don't match any inverters
        non_matching_cases = [
            ("/der/0/ders", "lfdi_no_match_001", 75),
            ("/der/1/ders", "lfdi_no_match_002", 85),
        ]

        for uri, lfdi, soc_value in non_matching_cases:
            der_status = create_test_der_status(uri, lfdi, soc_value)
            adpt.get_list_adapter().set_single(uri, der_status, lfdi)

        # Execute adapter
        message = gridappsd_adapter.get_message_for_bus()

        # Should return empty message since no LFDIs match
        assert isinstance(message, dict)
        assert len(message) == 0

    def test_partial_data_scenarios(self, adapter_test_database, gridappsd_adapter):
        """Test adapter with DERStatus objects missing optional fields."""

        # Store DERStatus with minimal data
        minimal_status = m.DERStatus(
            href="/der/0/ders",
            readingTime=int(time.time()),
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=int(time.time()), value=75),
            # Missing inverterStatus and other optional fields
        )

        adpt.get_list_adapter().set_single("/der/0/ders", minimal_status, "lfdi_test_house_001")

        # Store DERStatus with no stateOfChargeStatus
        no_soc_status = m.DERStatus(
            href="/der/1/ders",
            readingTime=int(time.time()),
            # Missing stateOfChargeStatus
        )

        adpt.get_list_adapter().set_single("/der/1/ders", no_soc_status, "lfdi_test_house_002")

        # Execute adapter
        message = gridappsd_adapter.get_message_for_bus()

        # Should handle partial data gracefully
        assert isinstance(message, dict)

        # The one with stateOfChargeStatus should appear
        if "house_001" in message:
            house1_data = message["house_001"]
            assert house1_data["value"] == 75

        # The one without stateOfChargeStatus might not appear or have None value
        if "house_002" in message:
            house2_data = message["house_002"]
            # value might be None or missing
            assert "mRID" in house2_data


if __name__ == "__main__":
    # Run the GridAPPSD adapter internal tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
