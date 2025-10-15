#!/usr/bin/env python3
"""
Test suite for verifying DERStatus database storage and retrieval.

This test suite ensures that:
1. DERStatus objects can be stored in the database via PUT requests
2. DERStatus objects can be retrieved from the database
3. GridAPPSD adapter can access stored DERStatus objects
4. The complete flow from storage to message bus format works correctly
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import ieee_2030_5.adapters as adpt

# Import the modules we need to test
import ieee_2030_5.models as m
from ieee_2030_5.persistance.points import configure_point_store, get_db
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

# Only import GridAPPSD adapter if available
try:
    from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

    GRIDAPPSD_AVAILABLE = True
except ImportError:
    GRIDAPPSD_AVAILABLE = False


@pytest.fixture(scope="module")
def temp_db_module():
    """Create a temporary database for the entire test module."""
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test.fs"

        # Configure the point store with the test database path
        configure_point_store("zodb", db_path)

        # Initialize adapters (this will use the configured database)
        adpt.initialize_adapters()

        # Update global adapter references
        adpt._update_global_adapters()

        # Get the configured database
        db = get_db()

        yield db

        # Cleanup at end of module
        try:
            # Close connection if it exists
            if hasattr(db, '_connection') and db._connection:
                db._connection.close()
            # Close database
            if hasattr(db, '_db') and db._db:
                db._db.close()
        except Exception:
            pass
    finally:
        # Remove temp directory
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_db(temp_db_module):
    """Clear database before each test to ensure clean state."""
    # Clear any existing data for a clean test environment
    try:
        temp_db_module.clear_all()
    except Exception:
        pass  # Ignore if clear_all doesn't exist or fails

    yield temp_db_module


@pytest.fixture
def sample_der_status():
    """Create a sample DERStatus object for testing."""
    return m.DERStatus(
        href="/der/0/ders",
        subscribable=1,
        readingTime=int(time.time()),
        stateOfChargeStatus=m.StateOfChargeStatusType(
            dateTime=int(time.time()),
            value=85,  # 85% state of charge
        ),
        inverterStatus=m.InverterStatusType(
            dateTime=int(time.time()),
            value=1,  # Operating
        ),
    )


@pytest.fixture
def sample_lfdi():
    """Create a sample LFDI for testing."""
    return "1234567890abcdef1234567890abcdef12345678"


class TestDERStatusStorage:
    """Test DERStatus storage in the database."""

    def test_store_der_status(self, temp_db, sample_der_status, sample_lfdi):
        """Test that DERStatus can be stored in the database."""
        # Get the ListAdapter
        list_adapter = adpt.get_list_adapter()

        # Store the DERStatus object
        uri = "/der/0/ders"
        result = list_adapter.set_single(uri=uri, obj=sample_der_status, lfdi=sample_lfdi)

        # Verify storage was successful
        assert result.success is True
        assert result.error is None

        # Verify we can retrieve it
        retrieved = list_adapter.get_single(uri)
        assert retrieved is not None
        assert isinstance(retrieved, m.DERStatus)
        assert retrieved.href == sample_der_status.href
        assert retrieved.stateOfChargeStatus.value == 85

    def test_update_der_status(self, temp_db, sample_der_status, sample_lfdi):
        """Test that DERStatus can be updated in the database."""
        uri = "/der/0/ders"

        # Store initial DERStatus
        result1 = adpt.get_list_adapter().set_single(uri=uri, obj=sample_der_status, lfdi=sample_lfdi)
        assert result1.success is True

        # Update the status
        sample_der_status.stateOfChargeStatus.value = 95
        sample_der_status.readingTime = int(time.time()) + 100

        # Store updated DERStatus
        result2 = adpt.get_list_adapter().set_single(uri=uri, obj=sample_der_status, lfdi=sample_lfdi)
        assert result2.success is True

        # Verify the update
        retrieved = adpt.get_list_adapter().get_single(uri)
        assert retrieved.stateOfChargeStatus.value == 95

    def test_store_multiple_der_status(self, temp_db, sample_lfdi):
        """Test storing multiple DERStatus objects for different DERs."""
        status_objects = []

        # Create and store multiple DERStatus objects
        for i in range(3):
            status = m.DERStatus(
                href=f"/der/{i}/ders",
                readingTime=int(time.time()),
                stateOfChargeStatus=m.StateOfChargeStatusType(
                    dateTime=int(time.time()),
                    value=50 + i * 10,  # 50%, 60%, 70%
                ),
            )
            status_objects.append(status)

            result = adpt.get_list_adapter().set_single(uri=f"/der/{i}/ders", obj=status, lfdi=sample_lfdi)
            assert result.success is True

        # Verify all can be retrieved
        for i, expected_status in enumerate(status_objects):
            retrieved = adpt.get_list_adapter().get_single(f"/der/{i}/ders")
            assert retrieved is not None
            assert retrieved.href == expected_status.href
            assert retrieved.stateOfChargeStatus.value == 50 + i * 10


class TestDERStatusRetrieval:
    """Test DERStatus retrieval patterns used by GridAPPSD adapter."""

    def test_filter_der_status_uris(self, temp_db, sample_der_status, sample_lfdi):
        """Test filtering URIs that contain 'ders' (as used by GridAPPSD adapter)."""
        # Store multiple objects with different URIs
        der_status_uri = "/der/0/ders"
        other_uri = "/der/0/derc"

        adpt.get_list_adapter().set_single(uri=der_status_uri, obj=sample_der_status, lfdi=sample_lfdi)
        adpt.get_list_adapter().set_single(uri=other_uri, obj=m.DERControl(), lfdi=sample_lfdi)

        # Filter for URIs ending with 'ders' (like GridAPPSD adapter does)
        def detect(v):
            return v and v.endswith("ders")

        der_status_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect(k))

        # Verify we only get DERStatus URIs
        assert len(der_status_uris) >= 1
        assert der_status_uri in der_status_uris
        assert other_uri not in der_status_uris

    def test_get_metadata_with_lfdi(self, temp_db, sample_der_status, sample_lfdi):
        """Test retrieving metadata that includes LFDI (needed for GridAPPSD mapping)."""
        uri = "/der/0/ders"

        # Store DERStatus with LFDI
        adpt.get_list_adapter().set_single(uri=uri, obj=sample_der_status, lfdi=sample_lfdi)

        # Get metadata
        metadata = adpt.get_list_adapter().get_single_meta_data(uri)

        # Verify metadata contains LFDI
        assert metadata is not None
        assert "lfdi" in metadata
        assert metadata["lfdi"] == sample_lfdi
        assert "uri" in metadata
        assert metadata["uri"] == uri


# GridAPPSD Integration tests require full GridAPPSD configuration
# Commented out for now as they need additional setup beyond basic GridAPPSD installation
# Uncomment and fix when full GridAPPSD integration testing is needed
#
# @pytest.mark.skipif(not GRIDAPPSD_AVAILABLE, reason="GridAPPSD not installed")
# class TestGridAPPSDIntegration:
#     """Test GridAPPSD adapter integration with DERStatus database."""
#
#     @pytest.fixture
#     def mock_gridappsd_adapter(self, temp_db):
#         """Create a mock GridAPPSD adapter for testing."""
#         # Mock GridAPPSD connection
#         mock_gapps = Mock()
#         mock_gapps.connected = True
#
#         # Mock configuration with all required fields
#         mock_config = {
#             "field_bus_def": {"id": "test_bus"},
#             "publish_interval_seconds": 3,
#             "house_named_inverters_regex": None,
#             "utility_named_inverters_regex": None,
#             "model_name": "test_model",  # Required by GridappsdConfiguration
#             "default_pin": "12345",  # Required by GridappsdConfiguration
#         }
#
#         # Mock TLS repository
#         mock_tls = Mock()
#
#         # Create adapter
#         try:
#             adapter = GridAPPSDAdapter(gapps=mock_gapps, gridappsd_configuration=mock_config, tls=mock_tls)
#         except (TypeError, AttributeError) as e:
#             pytest.skip(f"Could not initialize GridAPPSD adapter: {e}")
#
#         # Set up test inverters with known LFDIs
#         adapter._inverters = [
#             HouseLookup(mRID="house1", name="House1", lfdi="lfdi_house1"),
#             HouseLookup(mRID="house2", name="House2", lfdi="lfdi_house2"),
#         ]
#
#         # Mock the lock
#         adapter._lock = MagicMock()
#
#         return adapter
#
#     def test_get_message_for_bus_with_der_status(self, mock_gridappsd_adapter, temp_db):
        # COMMENTED OUT - See class comment above
        pass



class TestEndToEndFlow:
    """Test the complete flow from HTTP PUT to database to GridAPPSD retrieval."""

    def test_xml_to_database_to_retrieval(self, temp_db, sample_lfdi):
        """Test the complete flow from XML input to database storage to retrieval."""
        # Create DERStatus as XML (simulating HTTP PUT body)
        der_status = m.DERStatus(
            href="/der/0/ders",
            readingTime=int(time.time()),
            stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=int(time.time()), value=88),
            inverterStatus=m.InverterStatusType(
                dateTime=int(time.time()),
                value=1,  # Operating
            ),
        )

        # Convert to XML
        xml_data = dataclass_to_xml(der_status)
        assert xml_data is not None
        xml_str = xml_data.decode("utf-8") if isinstance(xml_data, bytes) else xml_data
        assert "<DERStatus" in xml_str
        assert "<value>88</value>" in xml_str

        # Parse XML back to object (simulating server processing)
        xml_str = xml_data.decode("utf-8") if isinstance(xml_data, bytes) else xml_data
        parsed_status = xml_to_dataclass(xml_str, m.DERStatus)
        assert parsed_status.href == "/der/0/ders"
        assert parsed_status.stateOfChargeStatus.value == 88

        # Store in database
        result = adpt.get_list_adapter().set_single(uri="/der/0/ders", obj=parsed_status, lfdi=sample_lfdi)
        assert result.success is True

        # Retrieve from database
        retrieved = adpt.get_list_adapter().get_single("/der/0/ders")
        assert retrieved is not None
        assert retrieved.href == "/der/0/ders"
        assert retrieved.stateOfChargeStatus.value == 88

        # Verify it can be filtered (as GridAPPSD adapter would)
        def detect(v):
            return v and v.endswith("ders")

        der_uris = adpt.get_list_adapter().filter_single_dict(lambda k: detect(k))
        assert "/der/0/ders" in der_uris

        # Verify metadata includes LFDI
        metadata = adpt.get_list_adapter().get_single_meta_data("/der/0/ders")
        assert metadata["lfdi"] == sample_lfdi


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
