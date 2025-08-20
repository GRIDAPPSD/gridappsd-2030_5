"""
SQLite implementation of the point store interface.
"""
import atexit
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import contextmanager

from .base import PointStoreBase

_log = logging.getLogger(__name__)


class SQLitePointStore(PointStoreBase):
    """Thread-safe point store using SQLite for persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("~/.ieee_2030_5_data/points.db").expanduser().resolve()
        elif isinstance(db_path, str):
            db_path = Path(db_path).expanduser().resolve()

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db_path = str(db_path)
        self._local = threading.local()

        # For thread-safe access to shared resources
        self._lock = threading.RLock()
        
        # Track atomic operation state per thread
        self._in_transaction = threading.local()

        # Initialize database schema
        self._init_schema()

        # Register cleanup
        atexit.register(self.close)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local connection to the database."""
        if not hasattr(self._local, 'connection'):
            # WAL mode for better concurrent access
            # Timeout for busy database
            self._local.connection = sqlite3.connect(
                self._db_path,
                timeout=30.0,
                check_same_thread=False
            )
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
            self._local.connection.execute("PRAGMA mmap_size=268435456")  # 256MB

        return self._local.connection

    def _init_schema(self):
        """Initialize the database schema."""
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS points (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for pattern matching
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_points_key_pattern
                ON points(key)
            """)

            # Trigger to update updated_at timestamp
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS points_update_timestamp
                AFTER UPDATE ON points
                FOR EACH ROW
                BEGIN
                    UPDATE points SET updated_at = CURRENT_TIMESTAMP
                    WHERE key = NEW.key;
                END
            """)

            conn.commit()
            _log.debug("SQLite schema initialized")
        except Exception as e:
            _log.error(f"Failed to initialize SQLite schema: {e}")
            raise

    def set_point(self, key: str, value: bytes) -> None:
        """Set a point into the key/value store."""
        try:
            conn = self._get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)",
                (key, value)
            )
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, 'active', False):
                conn.commit()
            _log.debug(f"Set point: {key} -> {len(value)} bytes")
        except Exception as e:
            _log.error(f"Failed to set point {key}: {e}")
            raise

    def get_point(self, key: str) -> Optional[bytes]:
        """Retrieve a point from the key/value store."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT value FROM points WHERE key = ?", (key,))
            row = cursor.fetchone()
            result = row[0] if row else None
            _log.debug(f"Get point: {key} -> {'found' if result else 'not found'}")
            return result
        except Exception as e:
            _log.error(f"Failed to get point {key}: {e}")
            return None

    def delete_point(self, key: str) -> bool:
        """Delete a point from the store."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("DELETE FROM points WHERE key = ?", (key,))
            conn.commit()
            deleted = cursor.rowcount > 0
            _log.debug(f"Delete point: {key} -> {'deleted' if deleted else 'not found'}")
            return deleted
        except Exception as e:
            _log.error(f"Failed to delete point {key}: {e}")
            raise

    def get_hrefs(self) -> List[str]:
        """Get all stored href keys."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT key FROM points ORDER BY key")
            keys = [row[0] for row in cursor.fetchall()]
            _log.debug(f"Retrieved {len(keys)} hrefs")
            return keys
        except Exception as e:
            _log.error(f"Failed to get hrefs: {e}")
            return []

    def get_keys_matching(self, pattern: str) -> List[str]:
        """Get all keys that match a pattern."""
        try:
            conn = self._get_connection()

            # Convert simple wildcard pattern to SQL LIKE pattern
            if pattern.endswith('*'):
                sql_pattern = pattern[:-1] + '%'
                cursor = conn.execute(
                    "SELECT key FROM points WHERE key LIKE ? ORDER BY key",
                    (sql_pattern,)
                )
            elif '*' in pattern:
                # More complex pattern - convert * to %
                sql_pattern = pattern.replace('*', '%')
                cursor = conn.execute(
                    "SELECT key FROM points WHERE key LIKE ? ORDER BY key",
                    (sql_pattern,)
                )
            else:
                # Exact match
                cursor = conn.execute(
                    "SELECT key FROM points WHERE key = ?",
                    (pattern,)
                )

            keys = [row[0] for row in cursor.fetchall()]
            _log.debug(f"Pattern '{pattern}' matched {len(keys)} keys")
            return keys
        except Exception as e:
            _log.error(f"Failed to get keys matching '{pattern}': {e}")
            return []

    def delete_point(self, key: str) -> bool:
        """Delete a point from the key/value store."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("DELETE FROM points WHERE key = ?", (key,))
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, 'active', False):
                conn.commit()
            deleted = cursor.rowcount > 0
            _log.debug(f"Deleted point: {key} -> {deleted}")
            return deleted
        except Exception as e:
            _log.error(f"Failed to delete point {key}: {e}")
            return False

    def clear_all(self) -> None:
        """Clear all points from the store. Use with caution!"""
        try:
            conn = self._get_connection()
            conn.execute("DELETE FROM points")
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, 'active', False):
                conn.commit()
            _log.info("Cleared all points from SQLite store")
        except Exception as e:
            _log.error(f"Failed to clear all points: {e}")
            raise

    def count(self) -> int:
        """Get the number of stored points."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT COUNT(*) FROM points")
            count = cursor.fetchone()[0]
            _log.debug(f"Point count: {count}")
            return count
        except Exception as e:
            _log.error(f"Failed to count points: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists in the store."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT 1 FROM points WHERE key = ? LIMIT 1", (key,))
            exists = cursor.fetchone() is not None
            _log.debug(f"Key exists: {key} -> {exists}")
            return exists
        except Exception as e:
            _log.error(f"Failed to check if key exists {key}: {e}")
            return False

    def bulk_set(self, items: Dict[str, bytes]) -> None:
        """Set multiple points in a single transaction."""
        try:
            conn = self._get_connection()
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.executemany(
                    "INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)",
                    list(items.items())
                )
                conn.commit()
                _log.debug(f"Bulk set {len(items)} points")
            except Exception:
                conn.rollback()
                raise
        except Exception as e:
            _log.error(f"Failed to bulk set points: {e}")
            raise

    def bulk_get(self, keys: List[str]) -> Dict[str, bytes]:
        """Get multiple points in a single operation."""
        try:
            conn = self._get_connection()

            # Use parameter placeholders for the IN clause
            placeholders = ','.join(['?' for _ in keys])
            cursor = conn.execute(
                f"SELECT key, value FROM points WHERE key IN ({placeholders})",
                keys
            )

            result = {row[0]: row[1] for row in cursor.fetchall()}
            _log.debug(f"Bulk get {len(result)}/{len(keys)} points")
            return result
        except Exception as e:
            _log.error(f"Failed to bulk get points: {e}")
            return {}

    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic operations across multiple point operations."""
        conn = self._get_connection()
        
        # Check if we're already in a transaction
        already_in_transaction = getattr(self._in_transaction, 'active', False)
        
        if not already_in_transaction:
            # Set transaction state for this thread
            self._in_transaction.active = True
            conn.execute("BEGIN TRANSACTION")
        
        try:
            yield
            if not already_in_transaction:
                conn.commit()
        except Exception:
            if not already_in_transaction:
                conn.rollback()
            raise
        finally:
            if not already_in_transaction:
                # Reset transaction state
                self._in_transaction.active = False

    def close(self) -> None:
        """Close the database connection."""
        try:
            # Close thread-local connections
            if hasattr(self._local, 'connection'):
                self._local.connection.close()

            _log.info("SQLite point store closed")
        except Exception as e:
            _log.error(f"Error closing SQLite point store: {e}")

    def get_stats(self) -> Dict[str, any]:
        """Get database statistics for debugging."""
        try:
            conn = self._get_connection()

            # Get table info
            cursor = conn.execute("SELECT COUNT(*) FROM points")
            total_points = cursor.fetchone()[0]

            # Get database file size
            cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            # Get some sample keys
            cursor = conn.execute("SELECT key FROM points ORDER BY key LIMIT 10")
            sample_keys = [row[0] for row in cursor.fetchall()]

            return {
                'total_points': total_points,
                'db_size_bytes': db_size,
                'db_file': self._db_path,
                'sample_keys': sample_keys
            }
        except Exception as e:
            _log.error(f"Failed to get stats: {e}")
            return {}


if __name__ == '__main__':
    # Test the SQLite implementation
    print("Testing SQLite points store...")

    store = SQLitePointStore()

    # Test basic operations
    store.set_point("foo", b"bar")
    store.set_point("bim", b"baf")
    store.set_point("single:test", b"single value")
    store.set_point("single:test_other", b"other single value")
    store.set_point("single:der_status", b"status data")

    print(f"foo = {store.get_point('foo')}")
    print(f"bim = {store.get_point('bim')}")
    print(f"Count: {store.count()}")
    print(f"HREFs: {store.get_hrefs()}")

    # Test pattern matching
    print(f"Keys matching 'single:*': {store.get_keys_matching('single:*')}")
    print(f"Keys matching '*test*': {store.get_keys_matching('*test*')}")

    # Test atomic operations
    try:
        with store.atomic_operation():
            store.set_point("atomic1", b"value1")
            store.set_point("atomic2", b"value2")
            # Both committed together
        print("Atomic operation successful")
    except Exception as e:
        print(f"Atomic operation failed: {e}")

    # Test bulk operations
    store.bulk_set({
        "bulk1": b"value1",
        "bulk2": b"value2",
        "bulk3": b"value3"
    })

    bulk_result = store.bulk_get(["bulk1", "bulk2", "nonexistent"])
    print(f"Bulk get result: {bulk_result}")

    # Test stats
    stats = store.get_stats()
    print(f"Database stats: {stats}")

    store.close()
    print("SQLite points store test completed.")
