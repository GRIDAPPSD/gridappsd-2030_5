# ieee_2030_5/persistance/points.py
"""
Provides a configurable key/value store interface for setting retrieving points from a datastore.
Supports both ZODB and SQLite backends, configurable via configuration.
"""

import logging
import threading
from contextlib import contextmanager
from pathlib import Path

from .base import PointStoreBase
from .sqlite_store import SQLitePointStore
from .zodb_store import ZODBPointStore

_log = logging.getLogger(__name__)


def create_point_store(backend: str = "zodb", db_path: Path | None = None) -> PointStoreBase:
    """
    Factory function to create a point store based on backend type.

    Args:
        backend: Backend type ("zodb" or "sqlite")
        db_path: Optional path to database file

    Returns:
        PointStore instance

    Raises:
        ValueError: If backend type is not supported
    """
    backend = backend.lower()

    if backend == "zodb":
        return ZODBPointStore(db_path)
    elif backend == "sqlite":
        return SQLitePointStore(db_path)
    else:
        raise ValueError(f"Unsupported point store backend: {backend}")


# Global instance and configuration
_db_instance = None
_db_lock = threading.Lock()
_backend_type = "zodb"  # Default backend
_db_path = None


def configure_point_store(backend: str = "zodb", db_path: Path | None = None) -> None:
    """
    Configure the global point store backend.
    Must be called before first use of get_db().

    Args:
        backend: Backend type ("zodb" or "sqlite")
        db_path: Optional path to database file
    """
    global _backend_type, _db_path, _db_instance

    with _db_lock:
        if _db_instance is not None:
            _log.warning("Point store already initialized, configuration change requires restart")
            return

        _backend_type = backend
        _db_path = db_path
        _log.info(f"Point store configured for backend: {backend}")


def get_db() -> PointStoreBase:
    """Get the global database instance (thread-safe singleton)."""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = create_point_store(_backend_type, _db_path)
                _log.info(f"Initialized {_backend_type} point store")
    return _db_instance


def reset_db() -> None:
    """Reset the global database instance. Use for testing."""
    global _db_instance
    with _db_lock:
        if _db_instance is not None:
            _db_instance.close()
            _db_instance = None


# Backward-compatible API functions
def set_point(key: str, value: bytes) -> None:
    """
    Set a point into the key/value store. Both key and value must be serializable.
    Example:
        set_point("_e55a4c7a-c006-4596-b658-e23bc771b5cb.angle", b"data")
        set_point("known_mrids", b'["_4da919f1-762f-4755-b674-5faccf3faec6"]')
    """
    get_db().set_point(key, value)


def get_point(key: str) -> bytes | None:
    """
    Retrieve a point from the key/value store. If the key doesn't exist returns None.
    """
    return get_db().get_point(key)


def get_hrefs() -> list[str]:
    """Get all stored href keys."""
    return get_db().get_hrefs()


def get_keys_matching(pattern: str) -> list[str]:
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


def bulk_set_points(items: dict[str, bytes]) -> None:
    """Set multiple points in a single operation."""
    get_db().bulk_set(items)


def bulk_get_points(keys: list[str]) -> dict[str, bytes]:
    """Get multiple points in a single operation."""
    return get_db().bulk_get(keys)


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
    with db.atomic_operation():
        yield


if __name__ == "__main__":
    # Test both implementations
    print("Testing configurable point store...")

    # Test SQLite
    print("\n=== Testing SQLite Backend ===")
    configure_point_store("sqlite")

    set_point("sqlite_test", b"sqlite_value")
    print(f"sqlite_test = {get_point('sqlite_test')}")
    print(f"Count: {point_count()}")

    reset_db()  # Clear for next test

    # Test ZODB
    print("\n=== Testing ZODB Backend ===")
    configure_point_store("zodb")

    set_point("zodb_test", b"zodb_value")
    print(f"zodb_test = {get_point('zodb_test')}")
    print(f"Count: {point_count()}")

    print("\nConfigurable point store test completed.")
