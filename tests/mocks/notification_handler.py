"""
Mock notification handler for IEEE 2030.5 server-to-client notifications.

This module provides a mock implementation of notification handling that can be used
to test scenarios where the server needs to push updates to clients.
"""

import logging
import threading
from datetime import datetime
from typing import Any, Callable

import ieee_2030_5.models as m

_log = logging.getLogger(__name__)


class MockNotificationHandler:
    """
    Mock implementation of notification handler for testing server-to-client updates.

    This class simulates the IEEE 2030.5 notification mechanism where the server
    can push updates to clients. It maintains a list of subscribers and can
    broadcast notifications to all subscribed clients.

    Attributes:
        notifications: List of all notifications sent
        subscribers: Dictionary mapping client IDs to notification callbacks
    """

    def __init__(self):
        self.notifications = []
        self.subscribers = {}
        self._lock = threading.Lock()
        _log.info("MockNotificationHandler initialized")

    def subscribe(self, client_id: str, callback: Callable[[m.Notification], None]):
        """
        Subscribe a client to receive notifications.

        Args:
            client_id: Unique identifier for the client
            callback: Function to call when notification is sent
        """
        with self._lock:
            self.subscribers[client_id] = callback
            _log.info(f"Client {client_id} subscribed to notifications")

    def unsubscribe(self, client_id: str):
        """
        Unsubscribe a client from receiving notifications.

        Args:
            client_id: Unique identifier for the client
        """
        with self._lock:
            if client_id in self.subscribers:
                del self.subscribers[client_id]
                _log.info(f"Client {client_id} unsubscribed from notifications")

    def send_notification(self, resource: Any, subscription_uri: str = "/sub/test"):
        """
        Send a notification to all subscribed clients.

        Args:
            resource: The updated resource to notify about
            subscription_uri: URI of the subscription
        """
        notification = m.Notification(
            subscribedResource=getattr(resource, "href", "/resource"),
            subscriptionURI=subscription_uri,
            status=0,
            Resource=[resource],
        )

        with self._lock:
            self.notifications.append((notification, datetime.now()))

            # Notify all subscribers
            for client_id, callback in self.subscribers.items():
                try:
                    callback(notification)
                    _log.debug(f"Sent notification to client {client_id}")
                except Exception as e:
                    _log.error(f"Error sending notification to client {client_id}: {e}")

        _log.info(f"Notification sent for resource {notification.subscribedResource}")

    def get_notifications_for_client(self, client_id: str) -> list[tuple[m.Notification, datetime]]:
        """
        Get all notifications that were sent while a client was subscribed.

        Args:
            client_id: Unique identifier for the client

        Returns:
            List of (notification, timestamp) tuples
        """
        with self._lock:
            # In a real implementation, this would track which notifications
            # were sent to which clients. For testing, return all.
            return list(self.notifications)

    def clear_notifications(self):
        """Clear all stored notifications."""
        with self._lock:
            self.notifications.clear()
            _log.info("Cleared all notifications")

    def get_subscriber_count(self) -> int:
        """Get the number of currently subscribed clients."""
        with self._lock:
            return len(self.subscribers)
