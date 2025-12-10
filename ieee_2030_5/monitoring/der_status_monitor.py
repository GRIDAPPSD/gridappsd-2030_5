"""
DER Status Monitor

This module provides real-time monitoring of client DER operations.
It captures and logs all DERStatus, DERSettings, DERCapability, and DERAvailability
GET (read) and PUT/POST (write) operations from clients for debugging and analysis purposes.
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

_log = logging.getLogger(__name__)


@dataclass
class DERStatusEvent:
    """Represents a DER operation event from a client."""

    timestamp: str
    client_lfdi: str
    der_path: str
    resource_type: str  # 'DERStatus', 'DERSettings', 'DERCapability', 'DERAvailability'
    operation: str  # 'GET', 'PUT', 'POST'
    data: dict[str, Any] = field(default_factory=dict)
    raw_xml: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "client_lfdi": self.client_lfdi,
            "der_path": self.der_path,
            "resource_type": self.resource_type,
            "operation": self.operation,
            "data": self.data,
            "raw_xml": self.raw_xml,
        }


class DERStatusMonitor:
    """
    Monitors DER operations from clients and provides real-time access
    to events for debugging and analysis.
    """

    def __init__(self, max_events: int = 1000, max_xml_length: int = 2000, max_clients: int = 100):
        self.max_events = max_events
        self.max_xml_length = max_xml_length
        self.max_clients = max_clients
        self._events: deque[DERStatusEvent] = deque(maxlen=max_events)
        self._subscribers: list[Callable[[DERStatusEvent], None]] = []
        self._lock = threading.RLock()
        self._stats = {
            "total_operations": 0,
            "reads": 0,  # GET operations
            "writes": 0,  # PUT/POST operations
            "by_resource_type": {
                "DERStatus": 0,
                "DERSettings": 0,
                "DERCapability": 0,
                "DERAvailability": 0,
                "DefaultDERControl": 0,
                "DERControl": 0,
                "DERProgram": 0,
                "DERControlList": 0,
            },
            "by_operation": {
                "GET": 0,
                "PUT": 0,
                "POST": 0,
            },
            "clients_seen": set(),
            "start_time": time.time(),
        }
        self._enabled = True
        # Track latest status per client/path for quick lookup
        self._latest_by_client: dict[str, dict[str, DERStatusEvent]] = {}

    def enable(self):
        """Enable status monitoring."""
        self._enabled = True
        _log.info("DER status monitoring enabled")

    def disable(self):
        """Disable status monitoring."""
        self._enabled = False
        _log.info("DER status monitoring disabled")

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self._enabled

    def log_operation(
        self,
        client_lfdi: str,
        der_path: str,
        resource_type: str,
        operation: str,
        data: dict[str, Any] | None = None,
        raw_xml: str = "",
    ):
        """
        Log a DER operation event.

        Args:
            client_lfdi: The client's LFDI (Long Form Device Identifier)
            der_path: The DER resource path
            resource_type: Type of resource ('DERStatus', 'DERSettings', etc.)
            operation: HTTP method ('GET', 'PUT', 'POST')
            data: The parsed data as a dictionary
            raw_xml: The raw XML content (will be truncated if too long)
        """
        if not self._enabled:
            return

        # Truncate very long XML for display
        display_xml = raw_xml
        if len(raw_xml) > self.max_xml_length:
            display_xml = raw_xml[: self.max_xml_length] + "... [TRUNCATED]"

        event = DERStatusEvent(
            timestamp=datetime.now().isoformat(),
            client_lfdi=client_lfdi or "unknown",
            der_path=der_path,
            resource_type=resource_type,
            operation=operation.upper(),
            data=data or {},
            raw_xml=display_xml,
        )

        with self._lock:
            self._events.append(event)

            # Update statistics
            self._stats["total_operations"] += 1

            # Track reads vs writes
            if operation.upper() == "GET":
                self._stats["reads"] += 1
            else:
                self._stats["writes"] += 1

            if resource_type in self._stats["by_resource_type"]:
                self._stats["by_resource_type"][resource_type] += 1

            if operation.upper() in self._stats["by_operation"]:
                self._stats["by_operation"][operation.upper()] += 1

            # Cap clients_seen set to prevent unbounded growth
            if len(self._stats["clients_seen"]) < self.max_clients:
                self._stats["clients_seen"].add(client_lfdi or "unknown")

            # Track latest status per client (for writes AND reads of control resources)
            # This helps see both client status updates and what controls they're reading
            should_track = operation.upper() in ("PUT", "POST")
            # Also track GET for control-related paths (dderc, derc) so we can see what clients are polling
            if operation.upper() == "GET" and any(x in der_path for x in ["dderc", "derc", "derp"]):
                should_track = True

            if should_track:
                # Cap the number of tracked clients
                if client_lfdi not in self._latest_by_client:
                    # If we're at capacity, remove oldest client
                    if len(self._latest_by_client) >= self.max_clients:
                        oldest_client = next(iter(self._latest_by_client))
                        del self._latest_by_client[oldest_client]
                    self._latest_by_client[client_lfdi] = {}

                # Cap paths per client to prevent unbounded growth
                max_paths_per_client = 50
                client_paths = self._latest_by_client[client_lfdi]

                # Remove existing entry first to update ordering (move to end = most recent)
                if der_path in client_paths:
                    del client_paths[der_path]
                elif len(client_paths) >= max_paths_per_client:
                    # At capacity, remove oldest path entry
                    oldest_path = next(iter(client_paths))
                    del client_paths[oldest_path]

                client_paths[der_path] = event

            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    subscriber(event)
                except Exception as e:
                    _log.warning(f"Error notifying DER status subscriber: {e}")

        _log.info(f"DER operation logged: {operation} {resource_type} from {client_lfdi} at {der_path} (total: {self._stats['total_operations']})")

    # Backwards compatibility alias
    def log_status_update(
        self,
        client_lfdi: str,
        der_path: str,
        update_type: str,
        data: dict[str, Any] | None = None,
        raw_xml: str = "",
    ):
        """Backwards compatible method - logs as a PUT operation."""
        self.log_operation(client_lfdi, der_path, update_type, "PUT", data, raw_xml)

    def get_recent_events(self, count: int | None = None, operation: str | None = None) -> list[DERStatusEvent]:
        """Get recent events, optionally filtered by operation type."""
        with self._lock:
            if operation:
                events = [e for e in self._events if e.operation == operation.upper()]
            else:
                events = list(self._events)

            if count is not None:
                events = events[-count:]
            return events

    def get_read_events(self, count: int | None = None) -> list[DERStatusEvent]:
        """Get recent GET (read) events."""
        return self.get_recent_events(count, operation="GET")

    def get_write_events(self, count: int | None = None) -> list[DERStatusEvent]:
        """Get recent PUT/POST (write) events."""
        with self._lock:
            events = [e for e in self._events if e.operation in ("PUT", "POST")]
            if count is not None:
                events = events[-count:]
            return events

    def get_events_by_client(self, client_lfdi: str, count: int | None = None) -> list[DERStatusEvent]:
        """Get events for a specific client."""
        with self._lock:
            events = [e for e in self._events if e.client_lfdi == client_lfdi]
            if count is not None:
                events = events[-count:]
            return events

    def get_events_by_type(self, resource_type: str, count: int | None = None) -> list[DERStatusEvent]:
        """Get events of a specific resource type."""
        with self._lock:
            events = [e for e in self._events if e.resource_type == resource_type]
            if count is not None:
                events = events[-count:]
            return events

    def get_latest_by_client(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Get the latest write status for each client/path combination."""
        with self._lock:
            result = {}
            for client_lfdi, paths in self._latest_by_client.items():
                result[client_lfdi] = {path: event.to_dict() for path, event in paths.items()}
            return result

    def get_stats(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        with self._lock:
            uptime = time.time() - self._stats["start_time"]
            stats = {
                "total_operations": self._stats["total_operations"],
                "reads": self._stats["reads"],
                "writes": self._stats["writes"],
                "by_resource_type": dict(self._stats["by_resource_type"]),
                "by_operation": dict(self._stats["by_operation"]),
                "clients_seen": list(self._stats["clients_seen"]),
                "start_time": self._stats["start_time"],
                "uptime_seconds": uptime,
                "operations_per_minute": (self._stats["total_operations"] / max(uptime, 1)) * 60,
                "enabled": self._enabled,
                "unique_clients": len(self._stats["clients_seen"]),
                "event_count": len(self._events),
                # Capacity info
                "max_events": self.max_events,
                "max_clients": self.max_clients,
                "tracked_clients": len(self._latest_by_client),
            }
            return stats

    def subscribe(self, callback: Callable[[DERStatusEvent], None]):
        """Subscribe to real-time status update events."""
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[DERStatusEvent], None]):
        """Unsubscribe from status update events."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def clear_events(self):
        """Clear all stored events."""
        with self._lock:
            self._events.clear()
            self._latest_by_client.clear()
            self._stats = {
                "total_operations": 0,
                "reads": 0,
                "writes": 0,
                "by_resource_type": {
                    "DERStatus": 0,
                    "DERSettings": 0,
                    "DERCapability": 0,
                    "DERAvailability": 0,
                    "DefaultDERControl": 0,
                    "DERControl": 0,
                    "DERProgram": 0,
                    "DERControlList": 0,
                },
                "by_operation": {
                    "GET": 0,
                    "PUT": 0,
                    "POST": 0,
                },
                "clients_seen": set(),
                "start_time": time.time(),
            }

    def search_events(
        self,
        query: str | None = None,
        client_filter: str | None = None,
        type_filter: str | None = None,
        operation_filter: str | None = None,
        count: int | None = None,
    ) -> list[DERStatusEvent]:
        """
        Search events by content, client, type, or operation.

        Args:
            query: Search query (case-insensitive) for raw XML content
            client_filter: Filter by client LFDI (partial match)
            type_filter: Filter by resource type
            operation_filter: Filter by operation ('GET', 'PUT', 'POST', 'READ', 'WRITE')
            count: Maximum number of events to return (most recent)

        Returns:
            List of matching events
        """
        results = []

        with self._lock:
            for event in self._events:
                # Check client filter
                if client_filter and client_filter.lower() not in event.client_lfdi.lower():
                    continue

                # Check type filter
                if type_filter and type_filter != event.resource_type:
                    continue

                # Check operation filter
                if operation_filter:
                    op = operation_filter.upper()
                    if op == "READ":
                        if event.operation != "GET":
                            continue
                    elif op == "WRITE":
                        if event.operation not in ("PUT", "POST"):
                            continue
                    elif event.operation != op:
                        continue

                # Check query in raw XML
                if query and query.lower() not in event.raw_xml.lower():
                    continue

                results.append(event)

        # Apply count limit if specified (return most recent)
        if count is not None and len(results) > count:
            results = results[-count:]

        return results


# Global DER status monitor instance
_der_monitor_instance: DERStatusMonitor | None = None
_der_monitor_lock = threading.Lock()


def get_der_status_monitor() -> DERStatusMonitor:
    """Get the global DER status monitor instance."""
    global _der_monitor_instance
    with _der_monitor_lock:
        if _der_monitor_instance is None:
            _der_monitor_instance = DERStatusMonitor()
        return _der_monitor_instance


def log_der_status_update(
    client_lfdi: str,
    der_path: str,
    update_type: str,
    data: dict[str, Any] | None = None,
    raw_xml: str = "",
):
    """
    Convenience function to log a DER status update (backwards compatible).

    This function should be called from DER request handlers to capture
    client status updates.
    """
    monitor = get_der_status_monitor()
    monitor.log_status_update(client_lfdi, der_path, update_type, data, raw_xml)


def log_der_operation(
    client_lfdi: str,
    der_path: str,
    resource_type: str,
    operation: str,
    data: dict[str, Any] | None = None,
    raw_xml: str = "",
):
    """
    Log a DER operation (GET, PUT, or POST).

    Args:
        client_lfdi: The client's LFDI
        der_path: The DER resource path
        resource_type: Type of resource ('DERStatus', 'DERSettings', etc.)
        operation: HTTP method ('GET', 'PUT', 'POST')
        data: The parsed data as a dictionary
        raw_xml: The raw XML content
    """
    monitor = get_der_status_monitor()
    monitor.log_operation(client_lfdi, der_path, resource_type, operation, data, raw_xml)


if __name__ == "__main__":
    # Test the monitor
    monitor = get_der_status_monitor()

    # Log some test events
    monitor.log_operation(
        client_lfdi="ABC123",
        der_path="/der/0/dstat",
        resource_type="DERStatus",
        operation="GET",
        data={},
        raw_xml="",
    )

    monitor.log_operation(
        client_lfdi="ABC123",
        der_path="/der/0/dstat",
        resource_type="DERStatus",
        operation="PUT",
        data={"operationalModeStatus": 1, "stateOfChargeStatus": 85},
        raw_xml="<DERStatus>...</DERStatus>",
    )

    monitor.log_operation(
        client_lfdi="ABC123",
        der_path="/der/0/ders",
        resource_type="DERSettings",
        operation="PUT",
        data={"setMaxW": 5000},
        raw_xml="<DERSettings>...</DERSettings>",
    )

    # Print stats
    print(f"Events: {len(monitor.get_recent_events())}")
    print(f"Read events: {len(monitor.get_read_events())}")
    print(f"Write events: {len(monitor.get_write_events())}")
    print(f"Stats: {monitor.get_stats()}")
    print(f"Latest by client: {monitor.get_latest_by_client()}")
