# ieee_2030_5/persistance/points.py
"""
Provides a key/value store interface for setting retrieving points from a datastore.
This implementation uses ZODB for persistent storage with built-in concurrency control.
ZODB provides MVCC (Multi-Version Concurrency Control) which handles concurrent access
automatically and safely.
"""
import atexit
import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern
from contextlib import contextmanager
import transaction
from ZODB import FileStorage, DB
from ZODB.Connection import Connection
from persistent.mapping import PersistentMapping
_log = logging.getLogger(__name__)

class ZODBPointStore:
    """Thread-safe point store using ZODB for persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("~/.ieee_2030_5_data/points.fs").expanduser().resolve()

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._storage = FileStorage.FileStorage(str(db_path))
        self._db = DB(self._storage)
        self._local = threading.local()

        # Cache for compiled regex patterns
        self._pattern_cache: Dict[str, Pattern] = {}

        # For thread-safe access to the pattern cache
        self._lock = threading.RLock()

        # Initialize root object if needed
        with self._get_connection() as conn:
            if not hasattr(conn.root(), 'points'):
                conn.root.points = PersistentMapping()
                transaction.commit()

        # Register cleanup
        atexit.register(self.close)

    @contextmanager
    def _get_connection(self) -> Connection:
        """Get a thread-local connection to the database."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = self._db.open()

        conn = self._local.connection
        try:
            yield conn
        except Exception:
            transaction.abort()
            raise

    def set_point(self, key: str, value: bytes) -> None:
        """
        Set a point into the key/value store. Both key and value must be serializable.

        Args:
            key: The key to store the value under
            value: The bytes value to store

        Example:
            set_point("_e55a4c7a-c006-4596-b658-e23bc771b5cb.angle", b"data")
            set_point("known_mrids", b'["_4da919f1-762f-4755-b674-5faccf3faec6"]')
        """
        normalized_key = key.replace('/', '^^^^')

        try:
            with self._get_connection() as conn:
                conn.root.points[normalized_key] = value
                transaction.commit()
                _log.debug(f"Set point: {key} -> {len(value)} bytes")
        except Exception as e:
            _log.error(f"Failed to set point {key}: {e}")
            transaction.abort()
            raise

    def get_point(self, key: str) -> Optional[bytes]:
        """
        Retrieve a point from the key/value store.

        Args:
            key: The key to retrieve

        Returns:
            The stored bytes value, or None if key doesn't exist
        """
        normalized_key = key.replace('/', '^^^^')

        try:
            with self._get_connection() as conn:
                result = conn.root.points.get(normalized_key)
                _log.debug(f"Get point: {key} -> {'found' if result else 'not found'}")
                return result
        except Exception as e:
            _log.error(f"Failed to get point {key}: {e}")
            return None

    def delete_point(self, key: str) -> bool:
        """
        Delete a point from the store.

        Args:
            key: The key to delete

        Returns:
            True if the key existed and was deleted, False otherwise
        """
        normalized_key = key.replace('/', '^^^^')

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

    def get_hrefs(self) -> List[str]:
        """
        Get all stored href keys.

        Returns:
            List of all keys in the store
        """
        try:
            with self._get_connection() as conn:
                keys = [key.replace('^^^^', '/') for key in conn.root.points.keys()]
                _log.debug(f"Retrieved {len(keys)} hrefs")
                return keys
        except Exception as e:
            _log.error(f"Failed to get hrefs: {e}")
            return []

    def get_keys_matching(self, pattern: str) -> List[str]:
        """
        Get all keys that match a specified pattern.

        Args:
            pattern: String pattern to match keys against. Supports:
                    - Exact match: "key"
                    - Prefix match: "prefix*"
                    - Suffix match: "*suffix"
                    - Contains match: "*part*"
                    - Regular expression: "re:pattern"

        Returns:
            List of matching keys
        """
        try:
            # Get all keys first
            all_keys = self.get_hrefs()
            matching_keys = []

            # Handle different pattern types
            if pattern.startswith('re:'):
                # Regular expression pattern
                regex = pattern[3:]
                with self._lock:
                    if regex not in self._pattern_cache:
                        self._pattern_cache[regex] = re.compile(regex)
                    compiled_re = self._pattern_cache[regex]

                matching_keys = [key for key in all_keys if compiled_re.search(key)]

            elif pattern.startswith('*') and pattern.endswith('*'):
                # Contains pattern
                substr = pattern[1:-1]
                matching_keys = [key for key in all_keys if substr in key]

            elif pattern.startswith('*'):
                # Suffix pattern
                suffix = pattern[1:]
                matching_keys = [key for key in all_keys if key.endswith(suffix)]

            elif pattern.endswith('*'):
                # Prefix pattern
                prefix = pattern[:-1]
                matching_keys = [key for key in all_keys if key.startswith(prefix)]

            else:
                # Exact match
                if pattern in all_keys:
                    matching_keys = [pattern]

            _log.debug(f"Found {len(matching_keys)} keys matching pattern '{pattern}'")
            return matching_keys

        except Exception as e:
            _log.error(f"Failed to get keys matching pattern '{pattern}': {e}")
            return []

    def clear_all(self) -> None:
        """Clear all points from the store. Use with caution!"""
        try:
            with self._get_connection() as conn:
                conn.root.points.clear()
                transaction.commit()
                _log.info("Cleared all points from store")
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
            _log.error(f"Failed to get point count: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists in the store."""
        normalized_key = key.replace('/', '^^^^')
        try:
            with self._get_connection() as conn:
                exists = normalized_key in conn.root.points
                _log.debug(f"Point exists check: {key} -> {exists}")
                return exists
        except Exception as e:
            _log.error(f"Failed to check point existence {key}: {e}")
            return False

    def bulk_set(self, points: dict) -> None:
        """
        Set multiple points in a single transaction.

        Args:
            points: Dictionary of key-value pairs to store
        """
        try:
            with self._get_connection() as conn:
                for key, value in points.items():
                    normalized_key = key.replace('/', '^^^^')
                    conn.root.points[normalized_key] = value
                transaction.commit()
                _log.debug(f"Bulk set {len(points)} points")
        except Exception as e:
            _log.error(f"Failed to bulk set points: {e}")
            transaction.abort()
            raise

    def bulk_get(self, keys: List[str]) -> dict:
        """
        Get multiple points in a single transaction.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary of key-value pairs found
        """
        result = {}
        try:
            with self._get_connection() as conn:
                for key in keys:
                    normalized_key = key.replace('/', '^^^^')
                    if normalized_key in conn.root.points:
                        result[key] = conn.root.points[normalized_key]
                _log.debug(f"Bulk get {len(result)}/{len(keys)} points")
                return result
        except Exception as e:
            _log.error(f"Failed to bulk get points: {e}")
            return {}

    def close(self) -> None:
        """Close the database connection and storage."""
        try:
            # Close thread-local connections
            if hasattr(self._local, 'connection'):
                self._local.connection.close()

            self._db.close()
            self._storage.close()
            _log.info("ZODB point store closed")
        except Exception as e:
            _log.error(f"Error closing ZODB point store: {e}")

# Global instance
_db_instance = None
_db_lock = threading.Lock()

def get_db() -> ZODBPointStore:
    """Get the global database instance (thread-safe singleton)."""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = ZODBPointStore()
    return _db_instance

# Backward-compatible API functions
def set_point(key: str, value: bytes) -> None:
    """
    Set a point into the key/value store. Both key and value must be serializable.
    Example:
        set_point("_e55a4c7a-c006-4596-b658-e23bc771b5cb.angle", b"data")
        set_point("known_mrids", b'["_4da919f1-762f-4755-b674-5faccf3faec6"]')
    """
    get_db().set_point(key, value)

def get_point(key: str) -> Optional[bytes]:
    """
    Retrieve a point from the key/value store. If the key doesn't exist returns None.
    """
    return get_db().get_point(key)

def get_hrefs() -> List[str]:
    """Get all stored href keys."""
    return get_db().get_hrefs()

def get_keys_matching(pattern: str) -> List[str]:
    """Get all keys matching a pattern."""
    return get_db().get_keys_matching(pattern)

def delete_point(key: str) -> bool:
    """Delete a point from the store."""
    return get_db().delete_point(key)

def clear_all_points() -> None:
    """Clear all points from the store. Use with caution!"""
    get_db().clear_all()

def point_exists(key: str) -> bool:
    """Check if a key exists in the store."""
    return get_db().exists(key)

def point_count() -> int:
    """Get the number of stored points."""
    return get_db().count()

# Enhanced transaction support for complex operations
@contextmanager
def atomic_operation():
    """
    Context manager for atomic operations across multiple point operations.

    Example:
        with atomic_operation():
            set_point("key1", b"value1")
            set_point("key2", b"value2")
            # Both operations committed together, or both rolled back on error
    """
    db = get_db()
    try:
        with db._get_connection():
            yield
            transaction.commit()
    except Exception:
        transaction.abort()
        raise

if __name__ == '__main__':
    # Test the new implementation
    print("Testing ZODB points store...")

    # Test basic operations
    set_point("foo", b"bar")
    set_point("bim", b"baf")
    set_point("single:test", b"single value")
    set_point("single:test_other", b"other single value")
    set_point("single:der_status", b"status data")

    print(f"foo = {get_point('foo')}")
    print(f"bim = {get_point('bim')}")
    print(f"Count: {point_count()}")
    print(f"HREFs: {get_hrefs()}")

    # Test pattern matching
    print(f"Keys matching 'single:*': {get_keys_matching('single:*')}")
    print(f"Keys matching '*test*': {get_keys_matching('*test*')}")

    # Test atomic operations
    try:
        with atomic_operation():
            set_point("atomic1", b"value1")
            set_point("atomic2", b"value2")
            # Both committed together
    except Exception as e:
        print(f"Atomic operation failed: {e}")

    # Test bulk operations
    db = get_db()
    db.bulk_set({
        "bulk1": b"value1",
        "bulk2": b"value2",
        "bulk3": b"value3"
    })

    bulk_result = db.bulk_get(["bulk1", "bulk2", "nonexistent"])
    print(f"Bulk get result: {bulk_result}")

    print("ZODB points store test completed.")
