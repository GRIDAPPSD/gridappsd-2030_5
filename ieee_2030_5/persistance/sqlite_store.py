"""
SQLite implementation of the point store interface.
"""
import atexit
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from contextlib import contextmanager
from functools import wraps

from .base import PointStoreBase

_log = logging.getLogger(__name__)


def retry_db_operation(max_retries: int = 3, base_delay: float = 0.05, max_delay: float = 1.0):
    """
    Decorator for database operations that handles SQLite lock retries with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for first retry (default: 0.05 = 50ms)
        max_delay: Maximum delay in seconds between retries (default: 1.0)
    """

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Only retry for database lock errors
                    if 'database is locked' in error_msg or 'busy' in error_msg:
                        if attempt < max_retries:
                            # Exponential backoff with jitter
                            delay = min(base_delay * (2**attempt), max_delay)
                            # Add small random jitter to prevent thundering herd
                            jitter = delay * 0.1 * (
                                0.5 + 0.5 * (hash(threading.current_thread().ident) % 100) / 100)
                            total_delay = delay + jitter

                            _log.debug(
                                f"Database locked, retrying in {total_delay:.3f}s (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(total_delay)
                            continue

                    # Re-raise non-lock errors immediately
                    raise
                except Exception as e:
                    # Re-raise non-sqlite errors immediately
                    last_exception = e
                    raise

            # If we've exhausted all retries, raise the last exception
            if last_exception:
                _log.error(
                    f"Database operation failed after {max_retries} retries: {last_exception}")
                raise last_exception
            else:
                raise RuntimeError(f"Database operation failed after {max_retries} retries")

        return wrapper

    return decorator


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
            # Increased timeout for busy database during complex operations
            self._local.connection = sqlite3.connect(
                self._db_path,
                timeout=60.0,    # Increased from 30 to 60 seconds
                check_same_thread=False)
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
            self._local.connection.execute("PRAGMA mmap_size=268435456")    # 256MB
            self._local.connection.execute("PRAGMA busy_timeout=60000")    # 60 second busy timeout
            self._local.connection.execute(
                "PRAGMA wal_autocheckpoint=1000")    # Checkpoint every 1000 pages

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

    @retry_db_operation(max_retries=10, base_delay=0.05, max_delay=1.0)
    def set_point(self, key: str, value: bytes) -> None:
        """Set a point into the key/value store."""
        try:
            conn = self._get_connection()
            conn.execute("INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)", (key, value))
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
            cursor = conn.execute("SELECT value FROM points WHERE key = ?", (key, ))
            row = cursor.fetchone()
            result = row[0] if row else None
            _log.debug(f"Get point: {key} -> {'found' if result else 'not found'}")
            return result
        except Exception as e:
            _log.error(f"Failed to get point {key}: {e}")
            return None

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
                cursor = conn.execute("SELECT key FROM points WHERE key LIKE ? ORDER BY key",
                                      (sql_pattern, ))
            elif '*' in pattern:
                # More complex pattern - convert * to %
                sql_pattern = pattern.replace('*', '%')
                cursor = conn.execute("SELECT key FROM points WHERE key LIKE ? ORDER BY key",
                                      (sql_pattern, ))
            else:
                # Exact match
                cursor = conn.execute("SELECT key FROM points WHERE key = ?", (pattern, ))

            keys = [row[0] for row in cursor.fetchall()]
            _log.debug(f"Pattern '{pattern}' matched {len(keys)} keys")
            return keys
        except Exception as e:
            _log.error(f"Failed to get keys matching '{pattern}': {e}")
            return []

    @retry_db_operation(max_retries=3, base_delay=0.05, max_delay=1.0)
    def delete_point(self, key: str) -> bool:
        """Delete a point from the key/value store."""
        try:
            conn = self._get_connection()
            cursor = conn.execute("DELETE FROM points WHERE key = ?", (key, ))
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, 'active', False):
                conn.commit()
            deleted = cursor.rowcount > 0
            _log.debug(f"Deleted point: {key} -> {deleted}")
            return deleted
        except Exception as e:
            _log.error(f"Failed to delete point {key}: {e}")
            return False

    @retry_db_operation(max_retries=3, base_delay=0.05, max_delay=1.0)
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
            cursor = conn.execute("SELECT 1 FROM points WHERE key = ? LIMIT 1", (key, ))
            exists = cursor.fetchone() is not None
            _log.debug(f"Key exists: {key} -> {exists}")
            return exists
        except Exception as e:
            _log.error(f"Failed to check if key exists {key}: {e}")
            return False

    @retry_db_operation(max_retries=20, base_delay=0.05, max_delay=1.0)
    def bulk_set(self, items: Dict[str, bytes]) -> None:
        """Set multiple points in a single transaction."""
        try:
            conn = self._get_connection()
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.executemany("INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)",
                                 list(items.items()))
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
            cursor = conn.execute(f"SELECT key, value FROM points WHERE key IN ({placeholders})",
                                  keys)

            result = {row[0]: row[1] for row in cursor.fetchall()}
            _log.debug(f"Bulk get {len(result)}/{len(keys)} points")
            return result
        except Exception as e:
            _log.error(f"Failed to bulk get points: {e}")
            return {}

    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic operations across multiple point operations."""
        import threading
        import time
        thread_id = threading.current_thread().ident
        start_time = time.time()

        conn = self._get_connection()

        # Check if we're already in a transaction
        already_in_transaction = getattr(self._in_transaction, 'active', False)

        if not already_in_transaction:
            # Set transaction state for this thread
            self._in_transaction.active = True
            _log.debug(
                f"LOCK DEBUG: Thread {thread_id} starting new transaction at {start_time:.3f}")

            # Retry transaction begin with exponential backoff for lock errors
            max_begin_retries = 3
            for attempt in range(max_begin_retries):
                try:
                    conn.execute("BEGIN TRANSACTION")
                    begin_time = time.time()
                    _log.debug(
                        f"LOCK DEBUG: Thread {thread_id} successfully began transaction (took {(begin_time-start_time)*1000:.1f}ms)"
                    )
                    break
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    if ('database is locked' in error_msg
                            or 'busy' in error_msg) and attempt < max_begin_retries - 1:
                        delay = 0.05 * (2**attempt)    # 50ms, 100ms, 200ms
                        _log.debug(
                            f"LOCK DEBUG: Thread {thread_id} transaction begin locked, retrying in {delay:.3f}s (attempt {attempt + 1}/{max_begin_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        self._in_transaction.active = False
                        fail_time = time.time()
                        _log.error(
                            f"LOCK DEBUG: Thread {thread_id} failed to begin transaction after {(fail_time-start_time)*1000:.1f}ms: {e}"
                        )
                        raise
                except Exception as e:
                    self._in_transaction.active = False
                    fail_time = time.time()
                    _log.error(
                        f"LOCK DEBUG: Thread {thread_id} failed to begin transaction after {(fail_time-start_time)*1000:.1f}ms: {e}"
                    )
                    raise
        else:
            _log.debug(f"LOCK DEBUG: Thread {thread_id} already in transaction, nested operation")

        try:
            yield
            if not already_in_transaction:
                # Retry commit with exponential backoff for lock errors
                max_commit_retries = 3
                for attempt in range(max_commit_retries):
                    try:
                        commit_start = time.time()
                        _log.debug(
                            f"LOCK DEBUG: Thread {thread_id} committing transaction (held for {(commit_start-start_time)*1000:.1f}ms)"
                        )
                        conn.commit()
                        commit_end = time.time()
                        _log.debug(
                            f"LOCK DEBUG: Thread {thread_id} successfully committed transaction (commit took {(commit_end-commit_start)*1000:.1f}ms, total {(commit_end-start_time)*1000:.1f}ms)"
                        )
                        break
                    except sqlite3.OperationalError as e:
                        error_msg = str(e).lower()
                        if ('database is locked' in error_msg
                                or 'busy' in error_msg) and attempt < max_commit_retries - 1:
                            delay = 0.05 * (2**attempt)    # 50ms, 100ms, 200ms
                            _log.debug(
                                f"LOCK DEBUG: Thread {thread_id} commit locked, retrying in {delay:.3f}s (attempt {attempt + 1}/{max_commit_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            error_time = time.time()
                            _log.error(
                                f"LOCK DEBUG: Thread {thread_id} failed to commit transaction after {(error_time-start_time)*1000:.1f}ms: {e}"
                            )
                            try:
                                conn.rollback()
                                rollback_time = time.time()
                                _log.debug(
                                    f"LOCK DEBUG: Thread {thread_id} rolled back transaction (rollback took {(rollback_time-error_time)*1000:.1f}ms)"
                                )
                            except Exception as rollback_e:
                                _log.error(
                                    f"LOCK DEBUG: Thread {thread_id} failed to rollback after commit error: {rollback_e}"
                                )
                            raise
                    except Exception as e:
                        error_time = time.time()
                        _log.error(
                            f"LOCK DEBUG: Thread {thread_id} failed to commit transaction after {(error_time-start_time)*1000:.1f}ms: {e}"
                        )
                        try:
                            conn.rollback()
                            rollback_time = time.time()
                            _log.debug(
                                f"LOCK DEBUG: Thread {thread_id} rolled back transaction (rollback took {(rollback_time-error_time)*1000:.1f}ms)"
                            )
                        except Exception as rollback_e:
                            _log.error(
                                f"LOCK DEBUG: Thread {thread_id} failed to rollback after commit error: {rollback_e}"
                            )
                        raise
        except Exception as ex:
            if not already_in_transaction:
                try:
                    rollback_start = time.time()
                    _log.debug(
                        f"LOCK DEBUG: Thread {thread_id} rolling back transaction due to exception after {(rollback_start-start_time)*1000:.1f}ms: {ex}"
                    )
                    conn.rollback()
                    rollback_end = time.time()
                    _log.debug(
                        f"LOCK DEBUG: Thread {thread_id} successfully rolled back transaction (rollback took {(rollback_end-rollback_start)*1000:.1f}ms)"
                    )
                except Exception as e:
                    _log.error(
                        f"LOCK DEBUG: Thread {thread_id} failed to rollback transaction: {e}")
            else:
                _log.debug(f"LOCK DEBUG: Thread {thread_id} nested operation failed: {ex}")
            raise
        finally:
            if not already_in_transaction:
                # Reset transaction state
                self._in_transaction.active = False
                final_time = time.time()
                _log.debug(
                    f"LOCK DEBUG: Thread {thread_id} finished transaction (total duration {(final_time-start_time)*1000:.1f}ms)"
                )

    def close(self) -> None:
        """Close the database connection."""
        try:
            # Close thread-local connections
            if hasattr(self._local, 'connection'):
                self._local.connection.close()

            _log.info("SQLite point store closed")
        except Exception as e:
            _log.error(f"Error closing SQLite point store: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics for debugging."""
        try:
            conn = self._get_connection()

            # Get table info
            cursor = conn.execute("SELECT COUNT(*) FROM points")
            total_points = cursor.fetchone()[0]

            # Get database file size
            cursor = conn.execute(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )
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

    print(f"foo = {store.get_point('foo')!r}")
    print(f"bim = {store.get_point('bim')!r}")
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
    store.bulk_set({"bulk1": b"value1", "bulk2": b"value2", "bulk3": b"value3"})

    bulk_result = store.bulk_get(["bulk1", "bulk2", "nonexistent"])
    print(f"Bulk get result: {bulk_result}")

    # Test stats
    stats = store.get_stats()
    print(f"Database stats: {stats}")

    store.close()
    print("SQLite points store test completed.")
