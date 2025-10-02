"""
ZODB implementation of the point store interface.
Refactored from the original points.py implementation.
"""

import atexit
import logging
import threading
from contextlib import contextmanager
from pathlib import Path

import transaction
from persistent.mapping import PersistentMapping
from ZODB import DB, FileStorage
from ZODB.Connection import Connection

from .base import PointStoreBase

_log = logging.getLogger(__name__)


class ZODBPointStore(PointStoreBase):
    """Thread-safe point store using ZODB for persistence."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path("~/.ieee_2030_5_data/points.fs").expanduser().resolve()

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._storage = FileStorage.FileStorage(str(db_path))
        self._db = DB(self._storage)
        self._local = threading.local()

        # For thread-safe access to shared resources
        self._lock = threading.RLock()

        # Initialize root object if needed
        with self._get_connection() as conn:
            if not hasattr(conn.root(), "points"):
                conn.root.points = PersistentMapping()
                transaction.commit()

        # Register cleanup
        atexit.register(self.close)

    @contextmanager
    def _get_connection(self) -> Connection:
        """Get a thread-local connection to the database."""
        if not hasattr(self._local, "connection"):
            self._local.connection = self._db.open()

        conn = self._local.connection
        try:
            yield conn
        except Exception:
            transaction.abort()
            raise

    def set_point(self, key: str, value: bytes, synchronous: bool = False) -> None:
        """Set a point into the key/value store.

        Args:
            key: The key to store the value under
            value: The bytes value to store
            synchronous: Ignored for ZODB (always synchronous), kept for compatibility
        """
        normalized_key = key.replace("/", "^^^^")

        try:
            with self._get_connection() as conn:
                conn.root.points[normalized_key] = value
                transaction.commit()
                _log.debug(f"Set point: {key} -> {len(value)} bytes")
        except Exception as e:
            _log.error(f"Failed to set point {key}: {e}")
            transaction.abort()
            raise

    def get_point(self, key: str) -> bytes | None:
        """Retrieve a point from the key/value store."""
        normalized_key = key.replace("/", "^^^^")

        try:
            with self._get_connection() as conn:
                result = conn.root.points.get(normalized_key)
                _log.debug(f"Get point: {key} -> {'found' if result else 'not found'}")
                return result
        except Exception as e:
            _log.error(f"Failed to get point {key}: {e}")
            return None

    def delete_point(self, key: str) -> bool:
        """Delete a point from the store."""
        normalized_key = key.replace("/", "^^^^")

        try:
            with self._get_connection() as conn:
                if normalized_key in conn.root.points:
                    del conn.root.points[normalized_key]
                    transaction.commit()
                    _log.debug(f"Deleted point: {key}")
                    return True
                else:
                    _log.debug(f"Point not found for deletion: {key}")
                    return False
        except Exception as e:
            _log.error(f"Failed to delete point {key}: {e}")
            transaction.abort()
            raise

    def get_hrefs(self) -> list[str]:
        """Get all stored href keys."""
        try:
            with self._get_connection() as conn:
                keys = [key.replace("^^^^", "/") for key in conn.root.points.keys()]
                _log.debug(f"Retrieved {len(keys)} hrefs")
                return keys
        except Exception as e:
            _log.error(f"Failed to get hrefs: {e}")
            return []

    def get_keys_matching(self, pattern: str) -> list[str]:
        """Get all keys that match a pattern."""
        try:
            with self._get_connection() as conn:
                all_keys = list(conn.root.points.keys())

                # Normalize the pattern for matching against stored keys
                normalized_pattern = pattern.replace("/", "^^^^")

                # Simple pattern matching for "prefix*" patterns
                if normalized_pattern.endswith("*"):
                    prefix = normalized_pattern[:-1]
                    matching_keys = [key for key in all_keys if key.startswith(prefix)]
                else:
                    matching_keys = [key for key in all_keys if key == normalized_pattern]

                # Convert back from normalized format
                result_keys = [key.replace("^^^^", "/") for key in matching_keys]
                _log.debug(f"Pattern '{pattern}' matched {len(result_keys)} keys")
                return result_keys
        except Exception as e:
            _log.error(f"Failed to get keys matching '{pattern}': {e}")
            return []

    def clear_all(self) -> None:
        """Clear all points from the store. Use with caution!"""
        try:
            with self._get_connection() as conn:
                conn.root.points.clear()
                transaction.commit()
                _log.info("Cleared all points from ZODB store")
        except Exception as e:
            _log.error(f"Failed to clear all points: {e}")
            transaction.abort()
            raise

    def count(self) -> int:
        """Get the number of stored points."""
        try:
            with self._get_connection() as conn:
                count = len(conn.root.points)
                _log.debug(f"Point count: {count}")
                return count
        except Exception as e:
            _log.error(f"Failed to count points: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists in the store."""
        normalized_key = key.replace("/", "^^^^")

        try:
            with self._get_connection() as conn:
                exists = normalized_key in conn.root.points
                _log.debug(f"Key exists: {key} -> {exists}")
                return exists
        except Exception as e:
            _log.error(f"Failed to check if key exists {key}: {e}")
            return False

    def bulk_set(self, items: dict[str, bytes]) -> None:
        """Set multiple points in a single transaction."""
        try:
            with self._get_connection() as conn:
                for key, value in items.items():
                    normalized_key = key.replace("/", "^^^^")
                    conn.root.points[normalized_key] = value
                transaction.commit()
                _log.debug(f"Bulk set {len(items)} points")
        except Exception as e:
            _log.error(f"Failed to bulk set points: {e}")
            transaction.abort()
            raise

    def bulk_get(self, keys: list[str]) -> dict[str, bytes]:
        """Get multiple points in a single operation."""
        try:
            with self._get_connection() as conn:
                result = {}
                for key in keys:
                    normalized_key = key.replace("/", "^^^^")
                    if normalized_key in conn.root.points:
                        result[key] = conn.root.points[normalized_key]
                _log.debug(f"Bulk get {len(result)}/{len(keys)} points")
                return result
        except Exception as e:
            _log.error(f"Failed to bulk get points: {e}")
            return {}

    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic operations across multiple point operations."""
        try:
            with self._get_connection():
                yield
                transaction.commit()
        except Exception:
            transaction.abort()
            raise

    def close(self) -> None:
        """Close the database connection and storage."""
        try:
            # Close thread-local connections
            if hasattr(self._local, "connection"):
                self._local.connection.close()

            self._db.close()
            self._storage.close()
            _log.info("ZODB point store closed")
        except Exception as e:
            _log.error(f"Error closing ZODB point store: {e}")
