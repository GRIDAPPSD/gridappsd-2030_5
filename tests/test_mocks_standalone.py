"""
Standalone tests for mock infrastructure that don't require server setup.

These tests verify the mock implementations work correctly without needing
a running IEEE 2030.5 server.
"""

import logging
import time
from datetime import datetime

import pytest

# Import only what we need for the mocks - avoid importing full server
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mocks.notification_handler import MockNotificationHandler
from tests.mocks.subscription_manager import MockSubscriptionManager
from tests.mocks.data_updater import MockDataUpdater, IntervalBasedUpdater

_log = logging.getLogger(__name__)


# Simple mock resource for testing
class MockResource:
    def __init__(self, mrid: str, value: int, href: str = None):
        self.mRID = mrid
        self.value = value
        self.href = href or f"/resource/{mrid}"
        self.description = f"Mock resource with value {value}"


def test_notification_handler_basic():
    """Test basic notification handler functionality"""
    handler = MockNotificationHandler()

    # Subscribe a client
    notifications_received = []

    def callback(notification):
        notifications_received.append(notification)

    handler.subscribe("client1", callback)

    # Send a notification
    resource = MockResource("TEST001", 100)
    handler.send_notification(resource)

    # Verify
    assert len(notifications_received) == 1
    assert handler.get_subscriber_count() == 1


def test_notification_handler_multiple_clients():
    """Test that multiple clients can subscribe and receive notifications"""
    handler = MockNotificationHandler()

    # Subscribe multiple clients
    client_notifications = {"client1": [], "client2": [], "client3": []}

    for client_id in client_notifications.keys():

        def make_callback(cid):
            return lambda notif: client_notifications[cid].append(notif)

        handler.subscribe(client_id, make_callback(client_id))

    # Send notification
    resource = MockResource("TEST002", 200)
    handler.send_notification(resource)

    # Verify all clients received notification
    assert all(len(notifs) == 1 for notifs in client_notifications.values())
    assert handler.get_subscriber_count() == 3


def test_notification_handler_unsubscribe():
    """Test unsubscribing clients"""
    handler = MockNotificationHandler()

    notifications = []
    handler.subscribe("client1", lambda n: notifications.append(n))
    handler.subscribe("client2", lambda n: notifications.append(n))

    assert handler.get_subscriber_count() == 2

    # Unsubscribe one client
    handler.unsubscribe("client1")
    assert handler.get_subscriber_count() == 1

    # Send notification - only one client should receive it
    handler.send_notification(MockResource("TEST", 100))
    assert len(notifications) == 1


def test_subscription_manager_tracks_subscriptions():
    """Test that subscription manager correctly tracks subscriptions"""
    manager = MockSubscriptionManager()

    # Create subscriptions
    manager.create_subscription("/mup/test", "/notify/client1", "client1")
    manager.create_subscription("/mup/test", "/notify/client2", "client2")

    # Verify tracking
    subs = manager.get_subscriptions_for_resource("/mup/test")
    assert len(subs) == 2
    assert manager.get_subscription_count() == 2


def test_subscription_manager_records_updates():
    """Test that subscription manager records resource updates"""
    manager = MockSubscriptionManager()

    # Create subscription
    manager.create_subscription("/mup/test", "/notify/client1", "client1")

    # Record updates
    resource1 = MockResource("TEST003", 100)
    resource2 = MockResource("TEST003", 200)

    manager.record_resource_update("/mup/test", resource1)
    time.sleep(0.1)
    manager.record_resource_update("/mup/test", resource2)

    # Verify
    updates = manager.get_updates_for_resource("/mup/test")
    assert len(updates) == 2
    assert updates[0][0].value == 100
    assert updates[1][0].value == 200


def test_subscription_manager_remove_subscription():
    """Test removing subscriptions"""
    manager = MockSubscriptionManager()

    # Create subscription
    sub = manager.create_subscription("/mup/test", "/notify/client1", "client1")
    assert manager.get_subscription_count() == 1

    # Remove it
    manager.remove_subscription(sub.href)
    assert manager.get_subscription_count() == 0


def test_data_updater_sends_periodic_updates():
    """Test that data updater sends updates at specified intervals"""
    updater = MockDataUpdater(update_interval=1)

    # Setup callback to track updates
    updates_received = []

    def callback(data):
        updates_received.append((data, datetime.now()))

    updater.register_callback(callback)

    # Start updater
    counter = {"value": 0}

    def data_generator():
        counter["value"] += 1
        return {"update_num": counter["value"], "timestamp": datetime.now()}

    updater.start(data_generator)

    # Wait for updates
    time.sleep(3.5)
    updater.stop()

    # Verify
    assert len(updates_received) >= 3, f"Expected at least 3 updates, got {len(updates_received)}"
    assert updater.get_update_count() >= 3


def test_data_updater_multiple_callbacks():
    """Test that data updater notifies all registered callbacks"""
    updater = MockDataUpdater(update_interval=1)

    # Register multiple callbacks
    callback1_data = []
    callback2_data = []

    updater.register_callback(lambda data: callback1_data.append(data))
    updater.register_callback(lambda data: callback2_data.append(data))

    # Start updater
    counter = {"value": 0}

    def data_generator():
        counter["value"] += 1
        return {"value": counter["value"]}

    updater.start(data_generator)
    time.sleep(2.5)
    updater.stop()

    # Verify both callbacks received updates
    assert len(callback1_data) >= 2
    assert len(callback2_data) >= 2
    assert len(callback1_data) == len(callback2_data)


def test_data_updater_stop_clears_state():
    """Test that stopping updater clears running state"""
    updater = MockDataUpdater(update_interval=1)

    updater.start(lambda: {"test": True})
    assert updater.is_running

    time.sleep(0.5)
    updater.stop()

    assert not updater.is_running


def test_interval_based_updater():
    """Test creating updaters with different intervals"""
    interval_updater = IntervalBasedUpdater()

    # Create updaters
    updater_3s = interval_updater.create_updater("3s", interval=1)
    updater_1min = interval_updater.create_updater("1min", interval=2)

    assert updater_3s is not None
    assert updater_1min is not None
    assert updater_3s.update_interval == 1
    assert updater_1min.update_interval == 2


def test_integrated_notification_subscription_update():
    """Integration test: Updates trigger notifications to subscribed clients"""
    handler = MockNotificationHandler()
    manager = MockSubscriptionManager()
    updater = MockDataUpdater(update_interval=1)

    # Setup clients with subscriptions
    client_data = {"client1": [], "client2": []}

    for client_id in client_data.keys():
        # Subscribe to resource
        manager.create_subscription("/mup/shared", f"/notify/{client_id}", client_id)

        # Setup notification callback
        def make_callback(cid):
            return lambda notif: client_data[cid].append(notif)

        handler.subscribe(client_id, make_callback(client_id))

    # Start periodic updates
    update_counter = {"value": 100}

    def data_generator():
        update_counter["value"] += 10
        resource = MockResource("SHARED001", update_counter["value"], href="/mup/shared")
        manager.record_resource_update("/mup/shared", resource)
        handler.send_notification(resource)
        return resource

    updater.start(data_generator)
    time.sleep(3.5)
    updater.stop()

    # Verify both clients received notifications
    assert len(client_data["client1"]) >= 3, f"Client1 received {len(client_data['client1'])} notifications"
    assert len(client_data["client2"]) >= 3, f"Client2 received {len(client_data['client2'])} notifications"


def test_40_clients_notification_scenario():
    """Test scenario with 40 clients receiving notifications"""
    handler = MockNotificationHandler()
    num_clients = 40
    client_notifications = {f"client_{i}": [] for i in range(num_clients)}

    # Subscribe all clients
    for client_id in client_notifications.keys():

        def make_callback(cid):
            return lambda notif: client_notifications[cid].append(notif)

        handler.subscribe(client_id, make_callback(client_id))

    # Send multiple notifications
    num_updates = 5
    for i in range(num_updates):
        resource = MockResource(f"SHARED_{i}", 100 + i * 10, href="/mup/shared")
        handler.send_notification(resource)
        time.sleep(0.1)

    # Verify ALL clients received ALL updates
    for client_id, notifications in client_notifications.items():
        assert len(notifications) == num_updates, f"{client_id} only received {len(notifications)}/{num_updates}"

    assert handler.get_subscriber_count() == num_clients


def test_stale_data_detection():
    """Test to detect when clients would receive stale data"""
    manager = MockSubscriptionManager()

    # Create subscription
    manager.create_subscription("/mup/test", "/notify/client", "client")

    # Record multiple updates with different values
    update_values = [100, 200, 300, 400]

    for value in update_values:
        resource = MockResource("TEST_STALE", value)
        manager.record_resource_update("/mup/test", resource)
        time.sleep(0.1)

    # Get all updates
    updates = manager.get_updates_for_resource("/mup/test")

    # Verify chronological order with correct values
    assert len(updates) == 4
    for i, (resource, timestamp) in enumerate(updates):
        expected_value = update_values[i]
        assert resource.value == expected_value, f"Update {i}: expected {expected_value}, got {resource.value} (stale!)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
