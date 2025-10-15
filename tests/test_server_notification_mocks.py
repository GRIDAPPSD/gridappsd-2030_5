"""
Tests for server notification mechanisms using mocks.

This module tests the notification and subscription infrastructure that the server
should use to push updates to clients, addressing the issues where:
- Clients don't receive notifications at expected intervals
- Clients receive stale data even when server values change
"""

import logging
import time
from datetime import datetime

import pytest

import ieee_2030_5.models as m
from tests.mocks import MockDataUpdater, MockNotificationHandler, MockSubscriptionManager

_log = logging.getLogger(__name__)


@pytest.fixture
def notification_handler():
    """Fixture providing notification handler"""
    return MockNotificationHandler()


@pytest.fixture
def subscription_manager():
    """Fixture providing subscription manager"""
    return MockSubscriptionManager()


@pytest.fixture
def data_updater():
    """Fixture providing data updater"""
    updater = MockDataUpdater(update_interval=1)
    yield updater
    if updater.is_running:
        updater.stop()


def test_notification_handler_basic(notification_handler):
    """Test basic notification handler functionality"""
    # Arrange: Subscribe a client
    notifications_received = []

    def callback(notification):
        notifications_received.append(notification)

    notification_handler.subscribe("client1", callback)

    # Act: Send a notification
    resource = m.MirrorUsagePoint(
        mRID="TEST001",
        description="Test MirrorUsagePoint",
        href="/mup/test001",
    )
    notification_handler.send_notification(resource)

    # Assert: Client should receive notification
    assert len(notifications_received) == 1
    assert notifications_received[0].subscribedResource == "/mup/test001"


def test_multiple_clients_receive_notifications(notification_handler):
    """Test that multiple clients can subscribe and receive notifications"""
    # Arrange: Subscribe multiple clients
    client_notifications = {"client1": [], "client2": [], "client3": []}

    for client_id in client_notifications.keys():

        def make_callback(cid):
            return lambda notif: client_notifications[cid].append(notif)

        notification_handler.subscribe(client_id, make_callback(client_id))

    # Act: Send notification
    resource = m.MirrorUsagePoint(mRID="TEST002", description="Test", href="/mup/test002")
    notification_handler.send_notification(resource)

    # Assert: All clients should receive notification
    assert all(len(notifs) == 1 for notifs in client_notifications.values())
    assert notification_handler.get_subscriber_count() == 3


def test_subscription_manager_tracks_subscriptions(subscription_manager):
    """Test that subscription manager correctly tracks subscriptions"""
    # Arrange & Act: Create subscriptions
    sub1 = subscription_manager.create_subscription("/mup/test", "/notify/client1", "client1")
    sub2 = subscription_manager.create_subscription("/mup/test", "/notify/client2", "client2")

    # Assert: Subscriptions should be tracked
    subs = subscription_manager.get_subscriptions_for_resource("/mup/test")
    assert len(subs) == 2
    assert subscription_manager.get_subscription_count() == 2


def test_subscription_manager_records_updates(subscription_manager):
    """Test that subscription manager records resource updates"""
    # Arrange: Create subscription
    subscription_manager.create_subscription("/mup/test", "/notify/client1", "client1")

    # Act: Record updates
    resource1 = m.MirrorUsagePoint(mRID="TEST003", description="Update 1")
    resource2 = m.MirrorUsagePoint(mRID="TEST003", description="Update 2")

    subscription_manager.record_resource_update("/mup/test", resource1)
    time.sleep(0.1)
    subscription_manager.record_resource_update("/mup/test", resource2)

    # Assert: Updates should be recorded
    updates = subscription_manager.get_updates_for_resource("/mup/test")
    assert len(updates) == 2
    assert updates[0][0].description == "Update 1"
    assert updates[1][0].description == "Update 2"


def test_data_updater_sends_periodic_updates(data_updater):
    """Test that data updater sends updates at specified intervals"""
    # Arrange: Setup callback to track updates
    updates_received = []

    def callback(data):
        updates_received.append((data, datetime.now()))

    data_updater.register_callback(callback)

    # Act: Start updater with data generator
    counter = {"value": 0}

    def data_generator():
        counter["value"] += 1
        return {"update_num": counter["value"], "timestamp": datetime.now()}

    data_updater.start(data_generator)

    # Wait for several updates (1s interval, so wait 3.5s for at least 3 updates)
    time.sleep(3.5)
    data_updater.stop()

    # Assert: Should have received multiple updates
    assert len(updates_received) >= 3, f"Expected at least 3 updates, got {len(updates_received)}"
    assert data_updater.get_update_count() >= 3


def test_data_updater_multiple_callbacks(data_updater):
    """Test that data updater notifies all registered callbacks"""
    # Arrange: Register multiple callbacks
    callback1_data = []
    callback2_data = []

    def callback1(data):
        callback1_data.append(data)

    def callback2(data):
        callback2_data.append(data)

    data_updater.register_callback(callback1)
    data_updater.register_callback(callback2)

    # Act: Start and run updater
    counter = {"value": 0}

    def data_generator():
        counter["value"] += 1
        return {"value": counter["value"]}

    data_updater.start(data_generator)
    time.sleep(2.5)  # Wait for at least 2 updates
    data_updater.stop()

    # Assert: Both callbacks should receive updates
    assert len(callback1_data) >= 2
    assert len(callback2_data) >= 2
    assert len(callback1_data) == len(callback2_data)


def test_integrated_notification_subscription_update(
    notification_handler, subscription_manager, data_updater
):
    """
    Integration test: Updates trigger notifications to subscribed clients.

    This simulates the complete flow:
    1. Clients subscribe to resources
    2. Server updates resources periodically
    3. Subscribed clients receive notifications
    """
    # Arrange: Setup clients with subscriptions and notification callbacks
    client_data = {"client1": [], "client2": []}

    for client_id in client_data.keys():
        # Subscribe to resource
        subscription_manager.create_subscription("/mup/shared", f"/notify/{client_id}", client_id)

        # Setup notification callback

        def make_callback(cid):
            return lambda notif: client_data[cid].append(notif)

        notification_handler.subscribe(client_id, make_callback(client_id))

    # Act: Start periodic updates that trigger notifications
    update_counter = {"value": 100}

    def data_generator():
        update_counter["value"] += 10
        resource = m.MirrorUsagePoint(
            mRID="SHARED001",
            description=f"Value {update_counter['value']}",
            href="/mup/shared",
        )
        # Record update in subscription manager
        subscription_manager.record_resource_update("/mup/shared", resource)
        # Send notification
        notification_handler.send_notification(resource)
        return resource

    data_updater.start(data_generator)
    time.sleep(3.5)  # Wait for 3+ updates
    data_updater.stop()

    # Assert: Both clients should receive notifications
    assert len(client_data["client1"]) >= 3, f"Client1 received {len(client_data['client1'])} notifications"
    assert len(client_data["client2"]) >= 3, f"Client2 received {len(client_data['client2'])} notifications"

    # Verify data is fresh (increasing values)
    client1_resources = [n.Resource[0] for n in client_data["client1"]]
    descriptions = [r.description for r in client1_resources]

    # Should see increasing values
    assert "Value 110" in descriptions
    assert "Value 120" in descriptions or "Value 130" in descriptions


def test_stale_data_detection(subscription_manager):
    """
    Test to detect when clients would receive stale data.

    This test simulates the issue where server updates data but clients
    receive old values.
    """
    # Arrange: Create subscription
    subscription_manager.create_subscription("/mup/test", "/notify/client", "client")

    # Act: Record multiple updates with timestamps
    update_values = [100, 200, 300, 400]
    update_times = []

    for value in update_values:
        resource = m.MirrorUsagePoint(
            mRID="TEST_STALE",
            description=f"Value {value}",
            MirrorMeterReading=m.MirrorMeterReading(
                mRID="READING_STALE", Reading=m.Reading(value=value)
            ),
        )
        subscription_manager.record_resource_update("/mup/test", resource)
        update_times.append(datetime.now())
        time.sleep(0.1)

    # Get all updates
    updates = subscription_manager.get_updates_for_resource("/mup/test")

    # Assert: Should have all updates in chronological order
    assert len(updates) == 4
    for i in range(len(updates)):
        resource, timestamp = updates[i]
        expected_value = update_values[i]
        actual_value = resource.MirrorMeterReading.Reading.value
        assert (
            actual_value == expected_value
        ), f"Update {i}: Expected value {expected_value}, got {actual_value} (stale!)"


def test_interval_based_updates_3s_1min_15min(notification_handler):
    """
    Test different update intervals as mentioned in the issue.

    This test simulates the scenario where server should send updates at
    3 seconds, 1 minute, and 15 minutes intervals.
    """
    from tests.mocks.data_updater import IntervalBasedUpdater

    # Arrange: Create updaters for different intervals
    interval_updater = IntervalBasedUpdater()
    updater_3s = interval_updater.create_updater("3s", interval=1)  # Use 1s for test speed
    updater_1min = interval_updater.create_updater("1min", interval=2)  # Use 2s for test speed

    # Track notifications for each interval
    notifications_3s = []
    notifications_1min = []

    # Subscribe clients to each interval
    notification_handler.subscribe("client_3s", lambda n: notifications_3s.append(n))
    notification_handler.subscribe("client_1min", lambda n: notifications_1min.append(n))

    # Create data generators that send notifications
    def make_generator(interval_name):
        counter = {"value": 0}

        def generator():
            counter["value"] += 1
            resource = m.MirrorUsagePoint(
                mRID=f"MUP_{interval_name}_{counter['value']}",
                description=f"{interval_name} update {counter['value']}",
                href=f"/mup/{interval_name}",
            )
            # Send notification through handler
            notification_handler.send_notification(resource)
            return resource

        return generator

    # Act: Start updaters
    updater_3s.start(make_generator("3s"))
    updater_1min.start(make_generator("1min"))

    # Wait for updates
    time.sleep(5)

    # Stop updaters
    updater_3s.stop()
    updater_1min.stop()

    # Assert: Different intervals should send different number of updates
    # 1s interval over 5s should send ~5 updates
    # 2s interval over 5s should send ~2-3 updates
    assert len(notifications_3s) >= 4, f"3s interval: expected >= 4 updates, got {len(notifications_3s)}"
    assert len(notifications_1min) >= 2, f"1min interval: expected >= 2 updates, got {len(notifications_1min)}"
    assert len(notifications_3s) > len(notifications_1min), "Higher frequency should send more updates"


def test_40_clients_notification_scenario(notification_handler):
    """
    Test scenario with 40 clients receiving notifications.

    This simulates the reported issue where not all 40 clients receive updates.
    """
    num_clients = 40
    client_notifications = {f"client_{i}": [] for i in range(num_clients)}

    # Subscribe all clients
    for client_id in client_notifications.keys():

        def make_callback(cid):
            return lambda notif: client_notifications[cid].append(notif)

        notification_handler.subscribe(client_id, make_callback(client_id))

    # Send multiple notifications
    num_updates = 5
    for i in range(num_updates):
        resource = m.MirrorUsagePoint(
            mRID=f"SHARED_{i}",
            description=f"Update {i}",
            href="/mup/shared",
        )
        notification_handler.send_notification(resource)
        time.sleep(0.1)

    # Assert: ALL clients should receive ALL updates
    for client_id, notifications in client_notifications.items():
        assert len(notifications) == num_updates, (
            f"{client_id} only received {len(notifications)}/{num_updates} updates"
        )

    # Verify correct subscriber count
    assert notification_handler.get_subscriber_count() == num_clients
