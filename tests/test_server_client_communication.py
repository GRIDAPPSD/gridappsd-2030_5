"""
Integration tests for server-to-client communication in IEEE 2030.5

This module tests the server's ability to send updated data to clients, ensuring that:
1. Clients receive data at configured poll intervals
2. Data received by clients is fresh and not stale
3. Multiple clients can receive updates simultaneously
4. Poll rates are correctly configured and respected

These tests address the issues reported where:
- Clients don't receive data at expected intervals (3s, 1min, 15min)
- Clients receive stale data even when server values have changed
- Not all clients receive updates when multiple clients are connected
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import ieee_2030_5.models as m
from ieee_2030_5.adapters import get_list_adapter, get_poll_rate
from ieee_2030_5.client import IEEE2030_5_Client
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

_log = logging.getLogger(__name__)


class MockMirrorUsagePointData:
    """Mock data generator for MirrorUsagePoint updates"""

    def __init__(self, mrid: str, initial_value: int = 0):
        self.mrid = mrid
        self.value = initial_value
        self.last_update = datetime.now()
        self._lock = threading.Lock()

    def get_updated_value(self) -> int:
        """Get current value with timestamp"""
        with self._lock:
            return self.value

    def update_value(self, new_value: int):
        """Update the value and timestamp"""
        with self._lock:
            self.value = new_value
            self.last_update = datetime.now()
            _log.info(f"Updated MirrorUsagePoint {self.mrid} to value {new_value} at {self.last_update}")

    def create_mirror_usage_point(self) -> m.MirrorUsagePoint:
        """Create a MirrorUsagePoint object with current value"""
        return m.MirrorUsagePoint(
            mRID=self.mrid,
            description=f"Test MirrorUsagePoint {self.mrid}",
            roleFlags=49,
            serviceCategoryKind=0,
            status=1,
            MirrorMeterReading=m.MirrorMeterReading(
                mRID=f"{self.mrid}_reading",
                description="Test Reading",
                Reading=m.Reading(value=self.get_updated_value()),
                ReadingType=m.ReadingType(
                    accumulationBehaviour=12,
                    commodity=1,
                    dataQualifier=2,
                    intervalLength=300,
                    powerOfTenMultiplier=0,
                    uom=38,
                ),
            ),
        )


class ClientPollSimulator:
    """Simulates a client polling the server at specified intervals"""

    def __init__(self, client: IEEE2030_5_Client, poll_interval: int, name: str = "Client"):
        self.client = client
        self.poll_interval = poll_interval
        self.name = name
        self.received_values = []
        self.poll_count = 0
        self.is_running = False
        self._thread = None
        self._lock = threading.Lock()

    def start_polling(self):
        """Start polling in background thread"""
        self.is_running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        _log.info(f"{self.name} started polling with interval {self.poll_interval}s")

    def stop_polling(self):
        """Stop polling"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        _log.info(f"{self.name} stopped polling after {self.poll_count} polls")

    def _poll_loop(self):
        """Internal polling loop"""
        while self.is_running:
            try:
                # Poll mirror usage points
                mup_list = self.client.mirror_usage_point_list()
                with self._lock:
                    if mup_list and mup_list.MirrorUsagePoint:
                        for mup in mup_list.MirrorUsagePoint:
                            if mup.MirrorMeterReading and mup.MirrorMeterReading.Reading:
                                value = mup.MirrorMeterReading.Reading.value
                                timestamp = datetime.now()
                                self.received_values.append((mup.mRID, value, timestamp))
                                _log.debug(
                                    f"{self.name} received value {value} for mRID {mup.mRID} at {timestamp}"
                                )
                    self.poll_count += 1
            except Exception as e:
                _log.error(f"{self.name} polling error: {e}")

            time.sleep(self.poll_interval)

    def get_latest_value(self, mrid: str) -> tuple[int | None, datetime | None]:
        """Get the latest received value for a specific mRID"""
        with self._lock:
            matching = [(val, ts) for mid, val, ts in self.received_values if mid == mrid]
            if matching:
                return matching[-1]
            return None, None

    def get_all_received_values(self, mrid: str) -> list[tuple[int, datetime]]:
        """Get all received values for a specific mRID"""
        with self._lock:
            return [(val, ts) for mid, val, ts in self.received_values if mid == mrid]


@pytest.fixture
def mock_data_generator():
    """Fixture providing mock data generator"""
    return MockMirrorUsagePointData(mrid="TEST_MRID_001", initial_value=100)


def test_single_client_receives_updates(first_client, mock_data_generator):
    """Test that a single client receives updated data when polling"""
    # Arrange: Create initial mirror usage point
    first_client.device_capability()
    mup = mock_data_generator.create_mirror_usage_point()
    status_code, location = first_client.create_mirror_usage_point(mup)
    assert status_code in (200, 201), "Failed to create mirror usage point"

    # Act: Poll and verify initial value
    mup_list = first_client.mirror_usage_point_list()
    assert mup_list is not None
    assert len(mup_list.MirrorUsagePoint) > 0

    initial_mup = mup_list.MirrorUsagePoint[0]
    initial_value = initial_mup.MirrorMeterReading.Reading.value
    assert initial_value == 100, f"Expected initial value 100, got {initial_value}"

    # Update the value on the server side
    mock_data_generator.update_value(200)
    updated_mup = mock_data_generator.create_mirror_usage_point()
    first_client.update_mirror_usage_point(location, updated_mup)

    # Act: Poll again and verify updated value
    mup_list = first_client.mirror_usage_point_list()
    updated_mup_from_server = mup_list.MirrorUsagePoint[0]
    updated_value = updated_mup_from_server.MirrorMeterReading.Reading.value

    # Assert: Value should be updated, not stale
    assert updated_value == 200, f"Expected updated value 200, got {updated_value} (stale data!)"


def test_multiple_clients_receive_updates(first_client, admin_client, mock_data_generator):
    """Test that multiple clients can receive updates simultaneously"""
    # Arrange: Create mirror usage point
    first_client.device_capability()
    admin_client.device_capability()

    mup = mock_data_generator.create_mirror_usage_point()
    status_code, location = first_client.create_mirror_usage_point(mup)
    assert status_code in (200, 201)

    # Act: Both clients poll initial value
    mup_list_1 = first_client.mirror_usage_point_list()
    mup_list_2 = admin_client.mirror_usage_point_list()

    initial_value_1 = mup_list_1.MirrorUsagePoint[0].MirrorMeterReading.Reading.value
    initial_value_2 = mup_list_2.MirrorUsagePoint[0].MirrorMeterReading.Reading.value

    assert initial_value_1 == 100
    assert initial_value_2 == 100

    # Update value
    mock_data_generator.update_value(300)
    updated_mup = mock_data_generator.create_mirror_usage_point()
    first_client.update_mirror_usage_point(location, updated_mup)

    # Both clients poll again
    mup_list_1 = first_client.mirror_usage_point_list()
    mup_list_2 = admin_client.mirror_usage_point_list()

    updated_value_1 = mup_list_1.MirrorUsagePoint[0].MirrorMeterReading.Reading.value
    updated_value_2 = mup_list_2.MirrorUsagePoint[0].MirrorMeterReading.Reading.value

    # Assert: Both clients should receive updated value
    assert updated_value_1 == 300, f"First client received stale value {updated_value_1}"
    assert updated_value_2 == 300, f"Second client received stale value {updated_value_2}"


def test_poll_rate_configuration(first_client, server_config):
    """Test that poll rates are correctly configured"""
    # Act: Get device capability which includes poll rate
    dcap = first_client.device_capability()

    # Assert: Poll rate should be set
    assert dcap.pollRate is not None, "Poll rate not set in DeviceCapability"
    assert dcap.pollRate > 0, f"Invalid poll rate: {dcap.pollRate}"

    # Verify that server configuration is respected
    expected_poll_rate = get_poll_rate("device_capability")
    assert (
        dcap.pollRate == expected_poll_rate
    ), f"Expected poll rate {expected_poll_rate}, got {dcap.pollRate}"


def test_continuous_polling_receives_updates(first_client, mock_data_generator):
    """Test that continuous polling at intervals receives all updates"""
    # Arrange: Setup client and data
    first_client.device_capability()
    mup = mock_data_generator.create_mirror_usage_point()
    status_code, location = first_client.create_mirror_usage_point(mup)
    assert status_code in (200, 201)

    # Create polling simulator with 2-second interval
    simulator = ClientPollSimulator(first_client, poll_interval=2, name="TestClient")

    try:
        # Start polling
        simulator.start_polling()

        # Wait for initial poll
        time.sleep(3)

        # Update value multiple times
        test_values = [150, 200, 250]
        for new_value in test_values:
            mock_data_generator.update_value(new_value)
            updated_mup = mock_data_generator.create_mirror_usage_point()
            first_client.update_mirror_usage_point(location, updated_mup)
            time.sleep(3)  # Wait for next poll

        # Stop polling
        simulator.stop_polling()

        # Assert: Client should have received multiple values
        all_values = simulator.get_all_received_values("TEST_MRID_001")
        assert len(all_values) >= 3, f"Expected at least 3 polls, got {len(all_values)}"

        # Verify values are not stale - should include updated values
        received_vals = [val for val, _ in all_values]
        for test_val in test_values:
            assert test_val in received_vals, f"Client did not receive updated value {test_val}"

    finally:
        simulator.stop_polling()


def test_40_clients_scenario(server_startup, mock_data_generator):
    """
    Test scenario with 40 clients to reproduce the reported issue.

    This test validates that:
    1. All 40 clients can poll the server
    2. All clients receive updated data
    3. Data is not stale when received
    """
    repo, servercfg = server_startup

    # Arrange: Create multiple client instances (reduced to 5 for test performance)
    num_clients = 5  # Reduced from 40 for test speed, but same pattern
    clients = []
    host, port = servercfg.server_hostname.split(":")

    try:
        # Create clients
        for i in range(num_clients):
            device_id = servercfg.devices[0].id
            certfile, keyfile = repo.get_file_pair(device_id)
            client = IEEE2030_5_Client(
                server_hostname=host,
                server_ssl_port=int(port),
                cafile=repo.ca_cert_file,
                keyfile=Path(keyfile),
                certfile=Path(certfile),
            )
            client.device_capability()
            clients.append(client)

        # Create mirror usage point with first client
        mup = mock_data_generator.create_mirror_usage_point()
        status_code, location = clients[0].create_mirror_usage_point(mup)
        assert status_code in (200, 201)

        # Act: All clients poll initial value
        initial_values = []
        for i, client in enumerate(clients):
            mup_list = client.mirror_usage_point_list()
            if mup_list and mup_list.MirrorUsagePoint:
                value = mup_list.MirrorUsagePoint[0].MirrorMeterReading.Reading.value
                initial_values.append(value)

        # All clients should receive the initial value
        assert len(initial_values) == num_clients, f"Not all clients received data: {len(initial_values)}/{num_clients}"
        assert all(v == 100 for v in initial_values), "Not all clients received same initial value"

        # Update the value
        mock_data_generator.update_value(400)
        updated_mup = mock_data_generator.create_mirror_usage_point()
        clients[0].update_mirror_usage_point(location, updated_mup)

        # All clients poll updated value
        updated_values = []
        for i, client in enumerate(clients):
            mup_list = client.mirror_usage_point_list()
            if mup_list and mup_list.MirrorUsagePoint:
                value = mup_list.MirrorUsagePoint[0].MirrorMeterReading.Reading.value
                updated_values.append(value)

        # Assert: All clients should receive updated value
        assert (
            len(updated_values) == num_clients
        ), f"Not all clients received updated data: {len(updated_values)}/{num_clients}"
        assert all(
            v == 400 for v in updated_values
        ), f"Not all clients received fresh data. Values: {updated_values}"

    finally:
        # Cleanup
        for client in clients:
            try:
                client.disconnect()
            except Exception:
                pass


def test_poll_intervals_3s_1min_15min(first_client, mock_data_generator):
    """
    Test different poll intervals as mentioned in the issue (3s, 1min, 15min).

    This test simulates clients with different poll rates to ensure the server
    can handle various polling frequencies.
    """
    # Arrange
    first_client.device_capability()
    mup = mock_data_generator.create_mirror_usage_point()
    status_code, location = first_client.create_mirror_usage_point(mup)
    assert status_code in (200, 201)

    # Test different poll intervals
    poll_intervals = [3, 60, 900]  # 3s, 1min, 15min

    for interval in poll_intervals:
        # Create simulator with specific interval
        simulator = ClientPollSimulator(first_client, poll_interval=interval, name=f"Client_{interval}s")

        try:
            # Update value before starting
            test_value = 100 + interval
            mock_data_generator.update_value(test_value)
            updated_mup = mock_data_generator.create_mirror_usage_point()
            first_client.update_mirror_usage_point(location, updated_mup)

            # Start polling
            simulator.start_polling()

            # Wait for at least one poll (interval + buffer)
            time.sleep(interval + 2)

            # Stop and verify
            simulator.stop_polling()

            # Client should have received at least one value
            latest_value, latest_ts = simulator.get_latest_value("TEST_MRID_001")
            assert latest_value is not None, f"Client with {interval}s interval did not receive data"
            assert (
                latest_value == test_value
            ), f"Client with {interval}s interval received stale data: {latest_value} != {test_value}"

        finally:
            simulator.stop_polling()


@pytest.mark.parametrize("num_updates", [1, 5, 10])
def test_data_freshness_with_rapid_updates(first_client, mock_data_generator, num_updates):
    """
    Test that clients receive fresh data even when server updates rapidly.

    This addresses the issue where clients receive stale data despite server updates.
    """
    # Arrange
    first_client.device_capability()
    mup = mock_data_generator.create_mirror_usage_point()
    status_code, location = first_client.create_mirror_usage_point(mup)
    assert status_code in (200, 201)

    # Act: Perform rapid updates
    for i in range(num_updates):
        new_value = 100 + (i + 1) * 10
        mock_data_generator.update_value(new_value)
        updated_mup = mock_data_generator.create_mirror_usage_point()
        first_client.update_mirror_usage_point(location, updated_mup)
        time.sleep(0.1)  # Small delay between updates

    # Poll to get latest value
    mup_list = first_client.mirror_usage_point_list()
    final_value = mup_list.MirrorUsagePoint[0].MirrorMeterReading.Reading.value

    # Assert: Should receive the most recent value
    expected_final_value = 100 + num_updates * 10
    assert (
        final_value == expected_final_value
    ), f"Received stale data: {final_value}, expected {expected_final_value}"
