"""
Mock subscription manager for IEEE 2030.5 resource subscriptions.

This module provides a mock implementation of subscription management that can be used
to test client subscription scenarios.
"""

import logging
import threading
from datetime import datetime
from typing import Any

import ieee_2030_5.models as m

_log = logging.getLogger(__name__)


class MockSubscriptionManager:
    """
    Mock implementation of subscription manager for testing.

    This class manages client subscriptions to resources and tracks when resources
    are updated so that subscribed clients can be notified.

    Attributes:
        subscriptions: Dictionary mapping resource hrefs to lists of subscriptions
        resource_updates: Dictionary tracking updates to subscribed resources
    """

    def __init__(self):
        self.subscriptions = {}
        self.resource_updates = {}
        self._lock = threading.Lock()
        _log.info("MockSubscriptionManager initialized")

    def create_subscription(
        self, subscribed_resource: str, notification_uri: str, client_id: str
    ) -> m.Subscription:
        """
        Create a subscription for a client to a resource.

        Args:
            subscribed_resource: href of the resource to subscribe to
            notification_uri: URI where notifications should be sent
            client_id: Unique identifier for the subscribing client

        Returns:
            The created Subscription object
        """
        subscription = m.Subscription(
            subscribedResource=subscribed_resource,
            notificationURI=notification_uri,
            href=f"/sub/{client_id}/{subscribed_resource.replace('/', '_')}",
        )

        with self._lock:
            if subscribed_resource not in self.subscriptions:
                self.subscriptions[subscribed_resource] = []

            self.subscriptions[subscribed_resource].append((client_id, subscription))
            _log.info(f"Created subscription for client {client_id} to {subscribed_resource}")

        return subscription

    def remove_subscription(self, subscription_href: str):
        """
        Remove a subscription.

        Args:
            subscription_href: href of the subscription to remove
        """
        with self._lock:
            for resource, subs in self.subscriptions.items():
                self.subscriptions[resource] = [
                    (cid, sub) for cid, sub in subs if sub.href != subscription_href
                ]
            _log.info(f"Removed subscription {subscription_href}")

    def get_subscriptions_for_resource(self, resource_href: str) -> list[tuple[str, m.Subscription]]:
        """
        Get all subscriptions for a specific resource.

        Args:
            resource_href: href of the resource

        Returns:
            List of (client_id, subscription) tuples
        """
        with self._lock:
            return list(self.subscriptions.get(resource_href, []))

    def record_resource_update(self, resource_href: str, updated_resource: Any):
        """
        Record that a resource has been updated.

        This would trigger notifications to be sent to subscribed clients.

        Args:
            resource_href: href of the updated resource
            updated_resource: The updated resource object
        """
        with self._lock:
            if resource_href not in self.resource_updates:
                self.resource_updates[resource_href] = []

            self.resource_updates[resource_href].append((updated_resource, datetime.now()))

            # Get subscribers for this resource
            subscribers = self.subscriptions.get(resource_href, [])
            _log.info(
                f"Resource {resource_href} updated, notifying {len(subscribers)} subscribers"
            )

    def get_updates_for_resource(self, resource_href: str) -> list[tuple[Any, datetime]]:
        """
        Get all recorded updates for a resource.

        Args:
            resource_href: href of the resource

        Returns:
            List of (resource, timestamp) tuples
        """
        with self._lock:
            return list(self.resource_updates.get(resource_href, []))

    def clear_updates(self):
        """Clear all recorded resource updates."""
        with self._lock:
            self.resource_updates.clear()
            _log.info("Cleared all resource updates")

    def get_subscription_count(self) -> int:
        """Get total number of active subscriptions."""
        with self._lock:
            return sum(len(subs) for subs in self.subscriptions.values())
