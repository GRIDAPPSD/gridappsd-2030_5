"""
GridAPPS-D Message Bus Traffic Monitor

This module provides real-time monitoring of GridAPPS-D message bus traffic.
It captures and logs all messages flowing through the system for debugging
and analysis purposes.
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

_log = logging.getLogger(__name__)


@dataclass
class MessageEvent:
    """Represents a message event on the GridAPPS-D message bus."""

    timestamp: str
    topic: str
    message: str
    direction: str  # 'inbound' or 'outbound'
    size: int
    message_type: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "topic": self.topic,
            "message": self.message,
            "direction": self.direction,
            "size": self.size,
            "message_type": self.message_type,
        }


class MessageBusMonitor:
    """
    Monitors GridAPPS-D message bus traffic and provides real-time access
    to message events for debugging and analysis.
    """

    def __init__(self, max_messages: int = 1000, max_message_length: int = 2000):
        self.max_messages = max_messages
        self.max_message_length = max_message_length
        self._messages = deque(maxlen=max_messages)
        self._subscribers = []
        self._lock = threading.RLock()
        self._stats = {
            "total_messages": 0,
            "inbound_messages": 0,
            "outbound_messages": 0,
            "bytes_transferred": 0,
            "topics_seen": set(),
            "start_time": time.time(),
        }
        self._enabled = True

    def enable(self):
        """Enable message monitoring."""
        self._enabled = True
        _log.info("GridAPPS-D message bus monitoring enabled")

    def disable(self):
        """Disable message monitoring."""
        self._enabled = False
        _log.info("GridAPPS-D message bus monitoring disabled")

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self._enabled

    def log_message(self, topic: str, message: str, direction: str = "inbound", message_type: str = "unknown"):
        """
        Log a message event.

        Args:
            topic: The message topic/destination
            message: The message content
            direction: 'inbound' or 'outbound'
            message_type: Type of message (e.g., 'simulation', 'command', etc.)
        """
        if not self._enabled:
            return

        # Truncate very long messages for display
        display_message = message
        if len(message) > self.max_message_length:
            display_message = message[: self.max_message_length] + "... [TRUNCATED]"

        event = MessageEvent(
            timestamp=datetime.now().isoformat(),
            topic=topic,
            message=display_message,
            direction=direction,
            size=len(message),
            message_type=message_type,
        )

        with self._lock:
            self._messages.append(event)

            # Update statistics
            self._stats["total_messages"] += 1
            if direction == "inbound":
                self._stats["inbound_messages"] += 1
            else:
                self._stats["outbound_messages"] += 1
            self._stats["bytes_transferred"] += len(message)
            self._stats["topics_seen"].add(topic)

            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    subscriber(event)
                except Exception as e:
                    _log.warning(f"Error notifying message subscriber: {e}")

        _log.debug(f"Message logged: {direction} on {topic} ({len(message)} bytes)")

    def get_recent_messages(self, count: int | None = None) -> list[MessageEvent]:
        """Get recent messages."""
        with self._lock:
            if count is None:
                return list(self._messages)
            else:
                return list(self._messages)[-count:]

    def get_stats(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        with self._lock:
            uptime = time.time() - self._stats["start_time"]
            stats = self._stats.copy()
            stats["topics_seen"] = list(stats["topics_seen"])
            stats["uptime_seconds"] = uptime
            stats["messages_per_second"] = stats["total_messages"] / max(uptime, 1)
            stats["enabled"] = self._enabled
            return stats

    def subscribe(self, callback: Callable[[MessageEvent], None]):
        """Subscribe to real-time message events."""
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[MessageEvent], None]):
        """Unsubscribe from message events."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def clear_messages(self):
        """Clear all stored messages."""
        with self._lock:
            self._messages.clear()
            self._stats = {
                "total_messages": 0,
                "inbound_messages": 0,
                "outbound_messages": 0,
                "bytes_transferred": 0,
                "topics_seen": set(),
                "start_time": time.time(),
            }

    def search_messages(self, query: str, topic_filter: str | None = None) -> list[MessageEvent]:
        """
        Search messages by content or topic.

        Args:
            query: Search query (case-insensitive)
            topic_filter: Optional topic filter

        Returns:
            List of matching messages
        """
        query_lower = query.lower()
        results = []

        with self._lock:
            for message in self._messages:
                # Check topic filter
                if topic_filter and topic_filter.lower() not in message.topic.lower():
                    continue

                # Check query in topic or message content
                if query_lower in message.topic.lower() or query_lower in message.message.lower():
                    results.append(message)

        return results


# Global message bus monitor instance
_monitor_instance = None
_monitor_lock = threading.Lock()


def get_message_monitor() -> MessageBusMonitor:
    """Get the global message bus monitor instance."""
    global _monitor_instance
    with _monitor_lock:
        if _monitor_instance is None:
            _monitor_instance = MessageBusMonitor()
        return _monitor_instance


def log_gridappsd_message(topic: str, message: str, direction: str = "inbound", message_type: str = "unknown"):
    """
    Convenience function to log a GridAPPS-D message.

    This function should be called from GridAPPS-D adapter code to capture
    message traffic.
    """
    monitor = get_message_monitor()
    monitor.log_message(topic, message, direction, message_type)


# Monkey patch helper for GridAPPS-D integration
def patch_gridappsd_adapter():
    """
    Monkey patch the GridAPPS-D adapter to capture message traffic.

    This should be called during application startup to enable monitoring.
    """
    try:
        # Try to import and patch GridAPPS-D components
        from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter

        # Store original methods
        if not hasattr(GridAPPSDAdapter, "_original_publish_house_aggregates"):
            GridAPPSDAdapter._original_publish_house_aggregates = GridAPPSDAdapter.publish_house_aggregates

        def monitored_publish_house_aggregates(self):
            """Monitored version of publish_house_aggregates."""
            try:
                # Call original method
                result = self._original_publish_house_aggregates()

                # Log the publishing activity
                log_gridappsd_message(
                    topic="house_aggregates",
                    message="Published house aggregate data",
                    direction="outbound",
                    message_type="house_data",
                )

                return result
            except Exception as e:
                log_gridappsd_message(
                    topic="house_aggregates",
                    message=f"Error publishing house aggregates: {e}",
                    direction="outbound",
                    message_type="error",
                )
                raise

        # Apply patch
        GridAPPSDAdapter.publish_house_aggregates = monitored_publish_house_aggregates
        _log.info("GridAPPS-D adapter patched for message monitoring")

    except ImportError:
        _log.warning("GridAPPS-D not available, message monitoring will be limited")
    except Exception as e:
        _log.error(f"Failed to patch GridAPPS-D adapter: {e}")


if __name__ == "__main__":
    # Test the monitor
    monitor = get_message_monitor()

    # Log some test messages
    monitor.log_message("test.topic", "Hello World", "inbound", "test")
    monitor.log_message("simulation.data", '{"voltage": 120.5}', "outbound", "simulation")

    # Print stats
    print(f"Messages: {len(monitor.get_recent_messages())}")
    print(f"Stats: {monitor.get_stats()}")
