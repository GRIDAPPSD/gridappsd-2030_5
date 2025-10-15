"""
Tests for client extension methods needed for testing server-client communication.

This module verifies that the IEEE2030_5_Client has necessary methods for
creating and updating resources during testing.
"""

import logging

import pytest

import ieee_2030_5.models as m
from ieee_2030_5.client import IEEE2030_5_Client
from tests.mocks import ClientPollTracker, MultiClientSimulator

_log = logging.getLogger(__name__)


def test_client_can_poll_mirror_usage_points(first_client):
    """Test that client can poll mirror usage point list"""
    # Arrange: Initialize client
    first_client.device_capability()

    # Act: Poll mirror usage points
    mup_list = first_client.mirror_usage_point_list()

    # Assert: Should get a valid response
    assert mup_list is not None
    assert isinstance(mup_list, m.MirrorUsagePointList)


def test_client_poll_tracker_records_polls(first_client):
    """Test that ClientPollTracker correctly records polling activity"""
    # Arrange
    first_client.device_capability()
    tracker = ClientPollTracker("test_client")

    # Act: Perform multiple polls
    for _ in range(5):
        mup_list = first_client.mirror_usage_point_list()
        tracker.record_poll(mup_list)

    # Assert: Tracker should have recorded all polls
    assert tracker.get_poll_count() == 5
    latest = tracker.get_latest_poll()
    assert latest is not None


def test_multi_client_simulator_creates_clients(server_startup):
    """Test that MultiClientSimulator can create multiple clients"""
    # Arrange
    repo, servercfg = server_startup
    simulator = MultiClientSimulator(servercfg, repo, num_clients=3)

    try:
        # Act
        clients = simulator.create_clients()

        # Assert
        assert len(clients) == 3
        assert all(isinstance(c, IEEE2030_5_Client) for c in clients)

    finally:
        simulator.cleanup()


def test_multi_client_simulator_polls_all_clients(server_startup):
    """Test that MultiClientSimulator can poll from all clients"""
    # Arrange
    repo, servercfg = server_startup
    simulator = MultiClientSimulator(servercfg, repo, num_clients=3)

    try:
        simulator.create_clients()
        simulator.initialize_all_clients()

        # Act: Poll all clients
        results = simulator.poll_all_clients(lambda client: client.mirror_usage_point_list())

        # Assert: All clients should successfully poll
        assert len(results) == 3
        successful = sum(1 for r in results.values() if r["success"])
        assert successful == 3, f"Only {successful}/3 clients successfully polled"

    finally:
        simulator.cleanup()


def test_client_receives_device_capability_with_poll_rate(first_client):
    """Test that client receives poll rate in device capability"""
    # Act
    dcap = first_client.device_capability()

    # Assert
    assert dcap is not None
    assert hasattr(dcap, "pollRate")
    assert dcap.pollRate is not None
    assert dcap.pollRate > 0


def test_multiple_clients_can_access_same_resources(first_client, admin_client):
    """Test that multiple clients can access the same resources"""
    # Arrange: Initialize both clients
    first_client.device_capability()
    admin_client.device_capability()

    # Act: Both clients poll same resource
    mup_list_1 = first_client.mirror_usage_point_list()
    mup_list_2 = admin_client.mirror_usage_point_list()

    # Assert: Both should get valid responses
    assert mup_list_1 is not None
    assert mup_list_2 is not None
    assert isinstance(mup_list_1, m.MirrorUsagePointList)
    assert isinstance(mup_list_2, m.MirrorUsagePointList)


def test_client_poll_tracker_detects_value_changes(first_client):
    """Test that ClientPollTracker can detect when values change"""
    # Arrange
    first_client.device_capability()
    tracker = ClientPollTracker("test_client")

    # Create a mock list with changing values
    class MockMUPList:
        def __init__(self, value):
            self.value = value

    # Act: Record polls with different values
    for i in range(5):
        mock_list = MockMUPList(value=100 + i * 10)
        tracker.record_poll(mock_list)

    # Get value changes
    changes = tracker.get_value_changes(lambda r: r.value)

    # Assert: Should detect all different values
    assert len(changes) == 5
    values = [val for val, _ in changes]
    assert values == [100, 110, 120, 130, 140]


def test_client_poll_tracker_detects_stale_data(first_client):
    """Test that ClientPollTracker can detect stale data"""
    # Arrange
    tracker = ClientPollTracker("test_client")

    class MockResource:
        def __init__(self, value):
            self.value = value

    # Act: Record polls with same value (stale data)
    for _ in range(5):
        mock_resource = MockResource(value=100)  # Same value every time
        tracker.record_poll(mock_resource)

    # Verify stale data detection
    is_fresh, msg = tracker.verify_no_stale_data(lambda r: r.value)

    # Assert: Should detect stale data
    assert not is_fresh, "Should detect stale data"
    assert "stale data" in msg.lower()


def test_client_poll_tracker_passes_fresh_data_check(first_client):
    """Test that ClientPollTracker passes check when data is fresh"""
    # Arrange
    tracker = ClientPollTracker("test_client")

    class MockResource:
        def __init__(self, value):
            self.value = value

    # Act: Record polls with changing values (fresh data)
    for i in range(5):
        mock_resource = MockResource(value=100 + i * 10)
        tracker.record_poll(mock_resource)

    # Verify fresh data detection
    is_fresh, msg = tracker.verify_no_stale_data(lambda r: r.value)

    # Assert: Should recognize fresh data
    assert is_fresh, f"Should detect fresh data: {msg}"
    assert "changed" in msg.lower()


def test_multi_client_simulator_tracks_errors(server_startup):
    """Test that MultiClientSimulator tracks errors correctly"""
    # Arrange
    repo, servercfg = server_startup
    simulator = MultiClientSimulator(servercfg, repo, num_clients=2)

    try:
        simulator.create_clients()
        simulator.initialize_all_clients()

        # Act: Poll with a function that raises an error for one client
        call_count = {"count": 0}

        def failing_fetcher(client):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise ValueError("Simulated error")
            return client.mirror_usage_point_list()

        results = simulator.poll_all_clients(failing_fetcher)

        # Assert: Should track the error
        assert len(results) == 2
        failed = sum(1 for r in results.values() if not r["success"])
        assert failed == 1, "Should have 1 failed poll"
        assert simulator.get_error_count() >= 1

    finally:
        simulator.cleanup()


@pytest.mark.parametrize("num_clients", [1, 5, 10])
def test_multi_client_simulator_scales(server_startup, num_clients):
    """Test that MultiClientSimulator works with different numbers of clients"""
    # Arrange
    repo, servercfg = server_startup
    simulator = MultiClientSimulator(servercfg, repo, num_clients=num_clients)

    try:
        # Act
        clients = simulator.create_clients()
        simulator.initialize_all_clients()

        # Assert
        assert len(clients) == num_clients

        # Verify all can poll
        results = simulator.poll_all_clients(lambda c: c.mirror_usage_point_list())
        successful = sum(1 for r in results.values() if r["success"])
        assert successful == num_clients, f"Only {successful}/{num_clients} clients successful"

    finally:
        simulator.cleanup()
