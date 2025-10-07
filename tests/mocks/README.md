# Mock Infrastructure for IEEE 2030.5 Testing

This directory contains mock implementations and utilities for testing server-to-client communication in IEEE 2030.5 implementations.

## Purpose

These mocks address the reported issues with server-to-client communication:
1. Clients not receiving data at expected intervals (3s, 1min, 15min)
2. Clients receiving stale data even when server values change
3. Not all clients receiving updates when multiple clients are connected

## Components

### MockNotificationHandler (`notification_handler.py`)

Simulates the notification mechanism for pushing updates from server to clients.

**Key Features:**
- Subscribe/unsubscribe clients to receive notifications
- Broadcast notifications to all subscribed clients
- Track notification history

**Usage:**
```python
from tests.mocks import MockNotificationHandler

handler = MockNotificationHandler()

# Subscribe a client
def on_notification(notification):
    print(f"Received: {notification.subscribedResource}")

handler.subscribe("client1", on_notification)

# Send notification
handler.send_notification(resource)
```

### MockSubscriptionManager (`subscription_manager.py`)

Manages client subscriptions to resources and tracks resource updates.

**Key Features:**
- Create and remove subscriptions
- Track which clients subscribe to which resources
- Record resource updates
- Get subscription statistics

**Usage:**
```python
from tests.mocks import MockSubscriptionManager

manager = MockSubscriptionManager()

# Create subscription
sub = manager.create_subscription(
    subscribed_resource="/mup/test",
    notification_uri="/notify/client1",
    client_id="client1"
)

# Record resource update
manager.record_resource_update("/mup/test", updated_resource)

# Get subscribers
subs = manager.get_subscriptions_for_resource("/mup/test")
```

### MockDataUpdater (`data_updater.py`)

Simulates periodic server-side data updates.

**Key Features:**
- Send updates at configurable intervals
- Support multiple callbacks for each update
- Track update history
- Start/stop update generation

**Usage:**
```python
from tests.mocks import MockDataUpdater

updater = MockDataUpdater(update_interval=3)  # 3 second interval

def data_generator():
    return {"value": get_current_value()}

def on_update(data):
    print(f"Update: {data}")

updater.register_callback(on_update)
updater.start(data_generator)

# Later...
updater.stop()
```

### IntervalBasedUpdater (`data_updater.py`)

Utility for testing multiple update intervals simultaneously (e.g., 3s, 1min, 15min).

**Usage:**
```python
from tests.mocks import IntervalBasedUpdater

interval_updater = IntervalBasedUpdater()
updater_3s = interval_updater.create_updater("3s", interval=3)
updater_1min = interval_updater.create_updater("1min", interval=60)
updater_15min = interval_updater.create_updater("15min", interval=900)

# Start all
interval_updater.start_all(data_generator)

# Later...
interval_updater.stop_all()
```

### MultiClientSimulator (`client_helpers.py`)

Simulates multiple clients for load testing and concurrent access scenarios.

**Key Features:**
- Create multiple client instances
- Poll resources from all clients simultaneously
- Track individual client statistics
- Simulate concurrent updates

**Usage:**
```python
from tests.mocks import MultiClientSimulator

simulator = MultiClientSimulator(server_config, tls_repo, num_clients=40)
simulator.create_clients()
simulator.initialize_all_clients()

# Poll all clients
results = simulator.poll_all_clients(
    lambda client: client.mirror_usage_point_list()
)

# Cleanup
simulator.cleanup()
```

### ClientPollTracker (`client_helpers.py`)

Tracks polling activity and verifies data freshness.

**Key Features:**
- Record poll results with timestamps
- Track value changes over time
- Verify that data is not stale
- Get statistics on polling behavior

**Usage:**
```python
from tests.mocks import ClientPollTracker

tracker = ClientPollTracker("client1")

# Record polls
for _ in range(10):
    resource = client.mirror_usage_point_list()
    tracker.record_poll(resource)

# Verify freshness
is_fresh, msg = tracker.verify_no_stale_data(
    lambda r: r.MirrorUsagePoint[0].MirrorMeterReading.Reading.value
)
assert is_fresh, msg
```

## Test Files

### `test_server_client_communication.py`

Integration tests for server-client communication using real client instances.

**Test Scenarios:**
- Single client receives updates
- Multiple clients receive updates simultaneously
- Poll rate configuration
- Continuous polling receives all updates
- 40-client scenario (scaled down for performance)
- Different poll intervals (3s, 1min, 15min)
- Data freshness with rapid updates

### `test_server_notification_mocks.py`

Unit tests for the mock infrastructure components.

**Test Scenarios:**
- Basic notification handler functionality
- Multiple clients receiving notifications
- Subscription tracking
- Resource update recording
- Periodic data updates
- Integrated notification flow
- Stale data detection
- 40-client notification scenario

## Running Tests

```bash
# Run all server-client communication tests
pytest tests/test_server_client_communication.py -v

# Run mock infrastructure tests
pytest tests/test_server_notification_mocks.py -v

# Run specific test
pytest tests/test_server_client_communication.py::test_40_clients_scenario -v
```

## Integration with Real Implementation

These mocks are designed to be used in tests while the real implementation can follow similar patterns:

1. **Notification Mechanism**: The real server should implement a notification system similar to `MockNotificationHandler`
2. **Subscription Management**: Track client subscriptions like `MockSubscriptionManager`
3. **Data Updates**: Ensure data is updated and propagated like `MockDataUpdater`

## Issue Resolution

These mocks help identify and test solutions for the reported issues:

1. **No Data at Expected Intervals**: Tests verify that updates are sent at configured intervals
2. **Stale Data**: Tests verify that clients receive fresh data, not cached/old values
3. **Incomplete Client Updates**: Tests verify all clients receive updates, not just a subset

## Contributing

When adding new test scenarios:
1. Use existing mocks where possible
2. Add new mocks to this directory if needed
3. Document usage in this README
4. Add integration tests in `test_server_client_communication.py`
5. Add unit tests for new mocks in `test_server_notification_mocks.py`
