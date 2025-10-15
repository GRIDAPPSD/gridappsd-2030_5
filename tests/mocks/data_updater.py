"""
Mock data updater for simulating server-side data updates.

This module provides utilities to simulate server-side data updates and track
how those updates propagate to clients.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable

_log = logging.getLogger(__name__)


class MockDataUpdater:
    """
    Mock implementation for simulating periodic server-side data updates.

    This class can be used to test scenarios where the server continuously
    updates data and clients need to poll or receive notifications.

    Attributes:
        update_interval: Interval in seconds between updates
        is_running: Whether the updater is currently running
        updates_sent: Number of updates sent
        update_callbacks: List of callbacks to invoke on each update
    """

    def __init__(self, update_interval: int = 3):
        """
        Initialize the data updater.

        Args:
            update_interval: Interval in seconds between updates (default: 3s)
        """
        self.update_interval = update_interval
        self.is_running = False
        self.updates_sent = 0
        self.update_callbacks = []
        self._thread = None
        self._lock = threading.Lock()
        self._update_history = []
        _log.info(f"MockDataUpdater initialized with {update_interval}s interval")

    def register_callback(self, callback: Callable[[Any], None]):
        """
        Register a callback to be invoked on each update.

        Args:
            callback: Function to call with update data
        """
        with self._lock:
            self.update_callbacks.append(callback)
            _log.debug(f"Registered update callback, total: {len(self.update_callbacks)}")

    def unregister_callback(self, callback: Callable[[Any], None]):
        """
        Unregister a callback.

        Args:
            callback: Function to remove from callbacks
        """
        with self._lock:
            if callback in self.update_callbacks:
                self.update_callbacks.remove(callback)
                _log.debug(f"Unregistered update callback")

    def start(self, data_generator: Callable[[], Any]):
        """
        Start sending periodic updates.

        Args:
            data_generator: Function that generates update data
        """
        if self.is_running:
            _log.warning("MockDataUpdater already running")
            return

        self.is_running = True
        self._thread = threading.Thread(
            target=self._update_loop, args=(data_generator,), daemon=True
        )
        self._thread.start()
        _log.info(f"MockDataUpdater started with {self.update_interval}s interval")

    def stop(self):
        """Stop sending updates."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        _log.info(f"MockDataUpdater stopped after sending {self.updates_sent} updates")

    def _update_loop(self, data_generator: Callable[[], Any]):
        """Internal update loop."""
        while self.is_running:
            try:
                # Generate update data
                update_data = data_generator()
                timestamp = datetime.now()

                # Record update
                with self._lock:
                    self._update_history.append((update_data, timestamp))
                    self.updates_sent += 1

                    # Invoke all callbacks
                    for callback in self.update_callbacks:
                        try:
                            callback(update_data)
                        except Exception as e:
                            _log.error(f"Error in update callback: {e}")

                _log.debug(f"Sent update #{self.updates_sent} at {timestamp}")

            except Exception as e:
                _log.error(f"Error in update loop: {e}")

            time.sleep(self.update_interval)

    def get_update_count(self) -> int:
        """Get the number of updates sent."""
        with self._lock:
            return self.updates_sent

    def get_update_history(self) -> list[tuple[Any, datetime]]:
        """
        Get the history of all updates sent.

        Returns:
            List of (data, timestamp) tuples
        """
        with self._lock:
            return list(self._update_history)

    def clear_history(self):
        """Clear the update history."""
        with self._lock:
            self._update_history.clear()
            self.updates_sent = 0
            _log.info("Cleared update history")


class IntervalBasedUpdater:
    """
    Utility class for testing different update intervals (3s, 1min, 15min).

    This class helps test the scenario described in the issue where clients
    expect updates at different intervals but don't receive them.
    """

    def __init__(self):
        self.updaters = {}
        self._lock = threading.Lock()

    def create_updater(self, name: str, interval: int) -> MockDataUpdater:
        """
        Create a named updater with specific interval.

        Args:
            name: Name for this updater (e.g., "3s", "1min", "15min")
            interval: Update interval in seconds

        Returns:
            MockDataUpdater instance
        """
        updater = MockDataUpdater(update_interval=interval)
        with self._lock:
            self.updaters[name] = updater
        _log.info(f"Created updater '{name}' with {interval}s interval")
        return updater

    def start_all(self, data_generator: Callable[[], Any]):
        """
        Start all updaters.

        Args:
            data_generator: Function that generates update data
        """
        with self._lock:
            for name, updater in self.updaters.items():
                updater.start(data_generator)
                _log.info(f"Started updater '{name}'")

    def stop_all(self):
        """Stop all updaters."""
        with self._lock:
            for name, updater in self.updaters.items():
                updater.stop()
                _log.info(f"Stopped updater '{name}'")

    def get_updater(self, name: str) -> MockDataUpdater | None:
        """Get an updater by name."""
        with self._lock:
            return self.updaters.get(name)

    def get_all_update_counts(self) -> dict[str, int]:
        """Get update counts for all updaters."""
        with self._lock:
            return {name: updater.get_update_count() for name, updater in self.updaters.items()}
