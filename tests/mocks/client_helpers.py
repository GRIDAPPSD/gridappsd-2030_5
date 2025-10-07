"""
Helper utilities for client simulation and testing.

This module provides utilities for simulating multiple clients and testing
client-server communication patterns.
"""

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from ieee_2030_5.client import IEEE2030_5_Client

_log = logging.getLogger(__name__)


class MultiClientSimulator:
    """
    Simulates multiple clients for testing server behavior under load.

    This class helps test scenarios where many clients are communicating with
    the server simultaneously, as described in the issue with 40 clients.
    """

    def __init__(self, server_config, tls_repository, num_clients: int = 10):
        """
        Initialize the multi-client simulator.

        Args:
            server_config: Server configuration object
            tls_repository: TLS repository for certificates
            num_clients: Number of clients to simulate
        """
        self.server_config = server_config
        self.tls_repository = tls_repository
        self.num_clients = num_clients
        self.clients = []
        self.client_data = {}
        self._lock = threading.Lock()
        _log.info(f"MultiClientSimulator initialized for {num_clients} clients")

    def create_clients(self) -> list[IEEE2030_5_Client]:
        """
        Create multiple client instances.

        Returns:
            List of IEEE2030_5_Client instances
        """
        host, port = self.server_config.server_hostname.split(":")

        for i in range(self.num_clients):
            try:
                # Use first device config for all clients (in real scenario, each would have unique cert)
                device_id = self.server_config.devices[0].id
                certfile, keyfile = self.tls_repository.get_file_pair(device_id)

                client = IEEE2030_5_Client(
                    server_hostname=host,
                    server_ssl_port=int(port),
                    cafile=self.tls_repository.ca_cert_file,
                    keyfile=Path(keyfile),
                    certfile=Path(certfile),
                )

                self.clients.append(client)
                self.client_data[f"client_{i}"] = {"client": client, "polls": [], "errors": []}

                _log.debug(f"Created client {i+1}/{self.num_clients}")

            except Exception as e:
                _log.error(f"Error creating client {i}: {e}")

        _log.info(f"Created {len(self.clients)} clients")
        return self.clients

    def initialize_all_clients(self):
        """Initialize device capability for all clients."""
        for i, client in enumerate(self.clients):
            try:
                client.device_capability()
                _log.debug(f"Initialized client {i}")
            except Exception as e:
                _log.error(f"Error initializing client {i}: {e}")
                self.client_data[f"client_{i}"]["errors"].append(str(e))

    def poll_all_clients(self, resource_fetcher) -> dict[str, Any]:
        """
        Poll a resource from all clients simultaneously.

        Args:
            resource_fetcher: Function that takes a client and returns resource

        Returns:
            Dictionary mapping client IDs to poll results
        """
        results = {}
        threads = []

        def poll_client(client_id, client):
            try:
                result = resource_fetcher(client)
                with self._lock:
                    results[client_id] = {"success": True, "data": result, "time": datetime.now()}
                    self.client_data[client_id]["polls"].append(results[client_id])
            except Exception as e:
                with self._lock:
                    results[client_id] = {"success": False, "error": str(e), "time": datetime.now()}
                    self.client_data[client_id]["errors"].append(str(e))

        # Start all polls simultaneously
        for i, client in enumerate(self.clients):
            client_id = f"client_{i}"
            thread = threading.Thread(target=poll_client, args=(client_id, client))
            threads.append(thread)
            thread.start()

        # Wait for all polls to complete
        for thread in threads:
            thread.join(timeout=10)

        _log.info(f"Polled {len(results)} clients")
        return results

    def get_successful_polls(self) -> int:
        """Get count of successful polls across all clients."""
        with self._lock:
            return sum(len(data["polls"]) for data in self.client_data.values())

    def get_error_count(self) -> int:
        """Get count of errors across all clients."""
        with self._lock:
            return sum(len(data["errors"]) for data in self.client_data.values())

    def cleanup(self):
        """Disconnect all clients."""
        for i, client in enumerate(self.clients):
            try:
                client.disconnect()
                _log.debug(f"Disconnected client {i}")
            except Exception as e:
                _log.error(f"Error disconnecting client {i}: {e}")

        _log.info(f"Cleaned up {len(self.clients)} clients")


class ClientPollTracker:
    """
    Tracks polling activity and data received by a client.

    This utility helps verify that clients are receiving fresh data
    and not stale values.
    """

    def __init__(self, client_id: str):
        """
        Initialize the tracker.

        Args:
            client_id: Unique identifier for the client
        """
        self.client_id = client_id
        self.poll_history = []
        self._lock = threading.Lock()

    def record_poll(self, resource: Any, timestamp: datetime | None = None):
        """
        Record a poll result.

        Args:
            resource: The resource received from polling
            timestamp: Time of the poll (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            self.poll_history.append({"resource": resource, "timestamp": timestamp})

    def get_poll_count(self) -> int:
        """Get total number of polls recorded."""
        with self._lock:
            return len(self.poll_history)

    def get_value_changes(self, value_extractor) -> list[tuple[Any, datetime]]:
        """
        Get list of value changes over time.

        Args:
            value_extractor: Function to extract value from resource

        Returns:
            List of (value, timestamp) tuples
        """
        with self._lock:
            return [(value_extractor(entry["resource"]), entry["timestamp"]) for entry in self.poll_history]

    def verify_no_stale_data(self, value_extractor) -> tuple[bool, str]:
        """
        Verify that values are changing and not stale.

        Args:
            value_extractor: Function to extract value from resource

        Returns:
            Tuple of (is_fresh, message)
        """
        with self._lock:
            if len(self.poll_history) < 2:
                return True, "Not enough data points to verify"

            values = [value_extractor(entry["resource"]) for entry in self.poll_history]

            # Check if values are changing
            unique_values = set(values)
            if len(unique_values) == 1:
                return False, f"All polls returned same value: {values[0]} (stale data)"

            return True, f"Values changed over {len(unique_values)} unique values"

    def get_latest_poll(self) -> dict | None:
        """Get the most recent poll result."""
        with self._lock:
            if self.poll_history:
                return self.poll_history[-1]
            return None


def simulate_concurrent_client_updates(clients: list[IEEE2030_5_Client], update_function, num_updates: int = 10):
    """
    Simulate concurrent updates from multiple clients.

    Args:
        clients: List of client instances
        update_function: Function that takes (client, update_num) and performs update
        num_updates: Number of updates to perform per client

    Returns:
        Dictionary with results
    """
    results = {"successful": 0, "failed": 0, "errors": []}
    threads = []
    lock = threading.Lock()

    def client_update_loop(client, client_idx):
        for update_num in range(num_updates):
            try:
                update_function(client, update_num)
                with lock:
                    results["successful"] += 1
            except Exception as e:
                with lock:
                    results["failed"] += 1
                    results["errors"].append(f"Client {client_idx}, update {update_num}: {str(e)}")

    # Start all clients
    for idx, client in enumerate(clients):
        thread = threading.Thread(target=client_update_loop, args=(client, idx))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join(timeout=30)

    return results
