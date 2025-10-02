"""
SQLite implementation of the point store interface.
"""

import atexit
import json
import logging
import queue
import sqlite3
import sys
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from .base import PointStoreBase

_log = logging.getLogger(__name__)


class DatabaseLoadMonitor:
    """Monitors database load and adjusts retry behavior dynamically."""

    def __init__(self):
        self._lock = threading.RLock()
        self._active_connections = 0
        self._failed_attempts = 0
        self._successful_attempts = 0
        self._last_reset = time.time()
        self._reset_interval = 60.0  # Reset stats every minute

    def connection_started(self):
        with self._lock:
            self._active_connections += 1

    def connection_ended(self, success: bool):
        with self._lock:
            self._active_connections = max(0, self._active_connections - 1)
            if success:
                self._successful_attempts += 1
            else:
                self._failed_attempts += 1

            # Reset stats periodically
            now = time.time()
            if now - self._last_reset > self._reset_interval:
                self._failed_attempts = 0
                self._successful_attempts = 0
                self._last_reset = now

    def get_load_metrics(self) -> dict:
        with self._lock:
            total_attempts = self._successful_attempts + self._failed_attempts
            failure_rate = self._failed_attempts / max(1, total_attempts)
            return {
                "active_connections": self._active_connections,
                "failure_rate": failure_rate,
                "load_factor": min(self._active_connections / 10.0, 1.0),  # Normalize to 0-1
            }


# Global load monitor instance
_load_monitor = DatabaseLoadMonitor()


def adaptive_retry_db_operation(base_max_retries: int = 5, base_delay: float = 0.02, max_delay: float = 2.0):
    """
    Adaptive decorator that adjusts retry behavior based on current database load.

    Args:
        base_max_retries: Base number of retries when load is low (default: 5)
        base_delay: Base delay in seconds for first retry (default: 0.02 = 20ms)
        max_delay: Maximum delay in seconds between retries (default: 2.0)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _load_monitor.connection_started()
            last_exception: Exception | None = None

            try:
                # Get current load metrics to adapt retry behavior
                metrics = _load_monitor.get_load_metrics()
                load_factor = metrics["load_factor"]
                failure_rate = metrics["failure_rate"]

                # Adaptive retry count: more retries under high load, fewer under low load
                # Scale from base_max_retries to base_max_retries * 3 based on load
                adaptive_max_retries = int(base_max_retries * (1 + 2 * load_factor))

                # Adaptive base delay: faster retries under low load, slower under high load
                # Scale from base_delay to base_delay * 2 based on failure rate
                adaptive_base_delay = base_delay * (1 + failure_rate)

                _log.debug(
                    f"Adaptive retry: load_factor={load_factor:.2f}, failure_rate={failure_rate:.2f}, "
                    f"max_retries={adaptive_max_retries}, base_delay={adaptive_base_delay:.3f}s"
                )

                for attempt in range(adaptive_max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        _load_monitor.connection_ended(success=True)
                        return result
                    except sqlite3.OperationalError as e:
                        last_exception = e
                        error_msg = str(e).lower()

                        # Only retry for database lock errors
                        if "database is locked" in error_msg or "busy" in error_msg:
                            if attempt < adaptive_max_retries:
                                # Adaptive exponential backoff with load-aware jitter
                                delay = min(adaptive_base_delay * (1.5**attempt), max_delay)

                                # Add larger jitter under high load to spread out retries
                                jitter_factor = 0.2 + (0.3 * load_factor)  # 20%-50% jitter based on load
                                jitter = (
                                    delay
                                    * jitter_factor
                                    * (0.5 + 0.5 * (hash(threading.current_thread().ident) % 100) / 100)
                                )
                                total_delay = delay + jitter

                                _log.debug(
                                    f"Database locked (load={load_factor:.2f}), retrying in {total_delay:.3f}s "
                                    f"(attempt {attempt + 1}/{adaptive_max_retries})"
                                )
                                time.sleep(total_delay)
                                continue

                        # Re-raise non-lock errors immediately
                        _load_monitor.connection_ended(success=False)
                        raise
                    except Exception as e:
                        # Re-raise non-sqlite errors immediately
                        last_exception = e
                        _load_monitor.connection_ended(success=False)
                        raise

                # If we've exhausted all retries, raise the last exception
                _load_monitor.connection_ended(success=False)
                if last_exception:
                    _log.error(
                        f"Database operation failed after {adaptive_max_retries} adaptive retries "
                        f"(load_factor={load_factor:.2f}): {last_exception}"
                    )
                    raise last_exception
                else:
                    raise RuntimeError(f"Database operation failed after {adaptive_max_retries} adaptive retries")

            except Exception:
                _load_monitor.connection_ended(success=False)
                raise

        return wrapper

    return decorator


# Keep the original decorator for backward compatibility
def retry_db_operation(max_retries: int = 3, base_delay: float = 0.05, max_delay: float = 1.0):
    """
    Original decorator for database operations with fixed retry behavior.
    Consider using adaptive_retry_db_operation for better scalability.
    """
    return adaptive_retry_db_operation(base_max_retries=max_retries, base_delay=base_delay, max_delay=max_delay)


class SQLitePointStore(PointStoreBase):
    """Thread-safe point store using SQLite for persistence with connection pooling."""

    def __init__(
        self,
        db_path: Path | None = None,
        max_connections: int = 20,
        cache_size: int = 10000,
        cache_ttl: float = 300.0,
        max_cache_memory_mb: float = 100.0,
    ):
        if db_path is None:
            db_path = Path("~/.ieee_2030_5_data/points.db").expanduser().resolve()
        elif isinstance(db_path, str):
            db_path = Path(db_path).expanduser().resolve()

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db_path = str(db_path)
        self._max_connections = max_connections
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl  # Time-to-live for cache entries in seconds
        self._max_cache_memory = max_cache_memory_mb * 1024 * 1024  # Convert MB to bytes

        # Connection pool for better concurrency
        self._connection_pool = []
        self._available_connections = threading.Semaphore(max_connections)
        self._pool_lock = threading.RLock()

        # Fallback to thread-local connections for overflow
        self._local = threading.local()

        # For thread-safe access to shared resources
        self._lock = threading.RLock()

        # Track atomic operation state per thread
        self._in_transaction = threading.local()

        # Track which connections have active transactions
        self._active_transactions = set()
        self._transaction_lock = threading.RLock()

        # List-level locks to prevent concurrent updates to the same list resource
        self._list_locks = {}
        self._list_locks_lock = threading.RLock()

        # In-memory cache for fast reads with memory tracking
        self._cache = OrderedDict()  # LRU cache using OrderedDict
        self._cache_lock = threading.RLock()
        self._cache_timestamps = {}  # Track when entries were cached
        self._cache_sizes = {}  # Track size of each cached entry in bytes
        self._cache_total_size = 0  # Total memory used by cache in bytes

        # Write queue with dedicated background thread
        self._write_queue = queue.Queue(maxsize=5000)  # Thread-safe queue
        self._write_batch = []  # Accumulator for batching writes
        self._write_batch_lock = threading.RLock()
        self._pending_writes = {}  # Track pending writes (key -> (event, enqueue_time))
        self._pending_writes_lock = threading.RLock()

        # Queue latency tracking
        self._queue_latencies = deque(maxlen=1000)  # Keep last 1000 latencies
        self._queue_latency_lock = threading.RLock()

        # Background writer thread
        self._writer_running = False
        self._writer_thread = None
        self._last_flush_time = time.time()
        self._flush_interval = 0.1  # Flush every 100ms or when batch is full
        self._batch_size = 100  # Maximum batch size

        # Connection statistics for monitoring
        self._pool_stats = {
            "total_connections": 0,
            "pooled_connections": 0,
            "overflow_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0,
        }

        # Cache statistics with enhanced metrics
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "evictions_memory": 0,  # Evictions due to memory limit
            "evictions_size": 0,  # Evictions due to size limit
            "writes_queued": 0,
            "writes_flushed": 0,
            "write_batches": 0,
            "queue_timeouts": 0,
            "queue_latency_sum": 0.0,
            "queue_latency_count": 0,
            "max_queue_latency": 0.0,
            "last_stats_reset": time.time(),
        }

        # Periodic stats logging for monitoring
        self._stats_log_interval = 60.0  # Log stats every minute
        self._last_stats_log = time.time()
        self._stats_history = deque(maxlen=60)  # Keep last 60 minutes of stats

        # Initialize database schema
        self._init_schema()

        # Start background writer thread
        self._start_writer_thread()

        # Preload cache with existing data on startup (optional)
        self._preload_cache()

        # Register cleanup
        atexit.register(self.close)

    def _create_optimized_connection(self) -> sqlite3.Connection:
        """Create a new optimized SQLite connection for high concurrency."""
        conn = sqlite3.connect(
            self._db_path,
            timeout=30.0,  # Reduced timeout - let retry logic handle it
            check_same_thread=False,
        )

        # High-concurrency optimizations
        conn.execute("PRAGMA journal_mode=WAL")  # WAL mode for better concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety vs performance
        conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
        conn.execute("PRAGMA mmap_size=536870912")  # 512MB memory mapping
        conn.execute("PRAGMA cache_size=10000")  # Larger page cache (40MB)
        conn.execute("PRAGMA busy_timeout=8000")  # 8 second busy timeout (balanced for burst handling)
        conn.execute("PRAGMA wal_autocheckpoint=2000")  # Less frequent checkpoints
        conn.execute("PRAGMA optimize")  # Enable query optimizer

        # High-concurrency WAL settings
        conn.execute("PRAGMA journal_size_limit=67108864")  # 64MB WAL file limit
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # Clean start

        # Performance tuning for high client count
        conn.execute("PRAGMA threads=4")  # Enable multi-threading
        # NOTE: Dirty reads (PRAGMA read_uncommitted=true) are NOT enabled by default to ensure data consistency.
        # If dirty reads are required for specific, non-critical operations, use a separate connection and document the use case.
        return conn

    def _get_pooled_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one."""
        # Try to get from pool first (non-blocking)
        if self._available_connections.acquire(blocking=False):
            with self._pool_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop()
                    self._pool_stats["pool_hits"] += 1
                    # Pool hit - no need to log every time
                    pass
                    return conn
                else:
                    # Pool was empty, create new connection
                    self._pool_stats["pool_misses"] += 1
                    self._pool_stats["pooled_connections"] += 1
                    conn = self._create_optimized_connection()
                    # Log only when pool size changes significantly
                    if self._pool_stats["pooled_connections"] % 10 == 0:
                        _log.info(f"Pool size: {self._pool_stats['pooled_connections']} connections")
                    return conn
        else:
            # Pool exhausted, use thread-local overflow connection
            self._pool_stats["pool_misses"] += 1
            if not hasattr(self._local, "connection"):
                self._pool_stats["overflow_connections"] += 1
                self._local.connection = self._create_optimized_connection()
                # Log overflow connections at info level as they indicate pool exhaustion
                if self._pool_stats["overflow_connections"] % 5 == 0:
                    _log.info(f"Overflow connections: {self._pool_stats['overflow_connections']}")
            return self._local.connection

    def _return_pooled_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        if hasattr(self._local, "connection") and conn is self._local.connection:
            # This is an overflow connection, keep it thread-local
            return

        # Return to pool
        with self._pool_lock:
            if len(self._connection_pool) < self._max_connections:
                self._connection_pool.append(conn)
                _log.debug(f"Returned connection to pool: {len(self._connection_pool)} connections available")
            else:
                # Pool is full, close the connection
                conn.close()
                self._pool_stats["pooled_connections"] -= 1
                _log.debug("Pool full, closed connection")

        self._available_connections.release()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection using pooling for better concurrency."""
        return self._get_pooled_connection()

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

    def _start_writer_thread(self):
        """Start the background writer thread for asynchronous database writes."""
        if not self._writer_running:
            self._writer_running = True
            self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
            self._writer_thread.start()
            _log.info("Started background writer thread with cache")

    def _writer_loop(self):
        """Main loop for the background writer thread."""
        while self._writer_running:
            try:
                # Check if we should flush the batch
                should_flush = False
                current_time = time.time()

                with self._write_batch_lock:
                    batch_size = len(self._write_batch)
                    time_since_last_flush = current_time - self._last_flush_time

                    # Flush if batch is full or timeout reached
                    if batch_size >= self._batch_size or (
                        batch_size > 0 and time_since_last_flush >= self._flush_interval
                    ):
                        should_flush = True

                if should_flush:
                    self._flush_write_batch()
                else:
                    # Try to get item from queue (with timeout)
                    try:
                        item = self._write_queue.get(timeout=0.01)
                        if item:
                            with self._write_batch_lock:
                                self._write_batch.append(item)
                                self._cache_stats["writes_queued"] += 1
                    except queue.Empty:
                        pass

            except Exception as e:
                _log.error(f"Writer thread error: {e}")
                time.sleep(0.1)

    def _flush_write_batch(self):
        """Flush accumulated writes to database in a single transaction."""
        with self._write_batch_lock:
            if not self._write_batch:
                return

            batch = self._write_batch[:]
            self._write_batch.clear()
            self._last_flush_time = time.time()

        conn = None
        try:
            conn = self._get_connection()
            conn.execute("BEGIN TRANSACTION")

            # Group writes by key (keep only latest value for each key)
            writes_by_key = {}
            events_by_key = {}

            for item in batch:
                key, value, event = item
                writes_by_key[key] = value
                if key not in events_by_key:
                    events_by_key[key] = []
                if event:
                    events_by_key[key].append(event)

            # Execute all writes
            for key, value in writes_by_key.items():
                conn.execute("INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)", (key, value))

            conn.commit()

            # Update statistics
            self._cache_stats["writes_flushed"] += len(writes_by_key)
            self._cache_stats["write_batches"] += 1

            # Notify waiting threads
            with self._pending_writes_lock:
                for key, events in events_by_key.items():
                    # Track latency if we have timing info
                    if key in self._pending_writes:
                        _, enqueue_time = self._pending_writes[key]
                        latency = time.time() - enqueue_time
                        self._track_queue_latency(latency)
                    for event in events:
                        event.set()
                    self._pending_writes.pop(key, None)

            _log.debug(f"Flushed batch: {len(writes_by_key)} unique writes from {len(batch)} items")

        except Exception as e:
            _log.error(f"Batch flush failed: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass  # Ignore rollback errors
            # Notify waiting threads even on failure
            with self._pending_writes_lock:
                for item in batch:
                    key, _, event = item
                    if event:
                        event.set()
                    # Track latency if we have timing info
                    if key in self._pending_writes:
                        _, enqueue_time = self._pending_writes[key]
                        latency = time.time() - enqueue_time
                        self._track_queue_latency(latency)
                    self._pending_writes.pop(key, None)
        finally:
            if conn:
                self._return_pooled_connection(conn)

    def _preload_cache(self, limit: int = 1000):
        """Preload frequently accessed items into cache on startup."""
        try:
            conn = self._get_connection()
            # Load most recently updated items
            cursor = conn.execute("SELECT key, value FROM points ORDER BY updated_at DESC LIMIT ?", (limit,))

            count = 0
            with self._cache_lock:
                for row in cursor:
                    key, value = row
                    self._cache[key] = value
                    self._cache_timestamps[key] = time.time()
                    count += 1

                    # Maintain cache size limit
                    if len(self._cache) > self._cache_size:
                        self._evict_lru()

            _log.info(f"Preloaded {count} items into cache")

        except Exception as e:
            _log.warning(f"Cache preload failed: {e}")

    def _evict_lru(self, reason="size"):
        """Evict least recently used item from cache."""
        if self._cache:
            # OrderedDict maintains insertion order, oldest item is first
            evicted_key = next(iter(self._cache))
            evicted_size = self._cache_sizes.get(evicted_key, 0)

            del self._cache[evicted_key]
            if evicted_key in self._cache_timestamps:
                del self._cache_timestamps[evicted_key]
            if evicted_key in self._cache_sizes:
                del self._cache_sizes[evicted_key]
            self._cache_total_size -= evicted_size

            self._cache_stats["evictions"] += 1
            if reason == "memory":
                self._cache_stats["evictions_memory"] += 1
            else:
                self._cache_stats["evictions_size"] += 1

            _log.debug(f"Evicted {evicted_key} ({evicted_size} bytes) due to {reason} limit")

    def _update_cache(self, key: str, value: bytes):
        """Update cache with new value, maintaining size and memory limits."""
        with self._cache_lock:
            value_size = sys.getsizeof(value) + sys.getsizeof(key)  # Include key size

            # Remove old entry if exists (to update position in OrderedDict)
            if key in self._cache:
                old_size = self._cache_sizes.get(key, 0)
                self._cache_total_size -= old_size
                del self._cache[key]
                if key in self._cache_sizes:
                    del self._cache_sizes[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]

            # Check memory limit first - evict until we have space
            while self._cache and (self._cache_total_size + value_size > self._max_cache_memory):
                self._evict_lru(reason="memory")

            # Check if value would still exceed memory limit after evictions
            if value_size > self._max_cache_memory:
                _log.warning(
                    f"Value for {key} ({value_size} bytes) exceeds max cache memory ({self._max_cache_memory} bytes)"
                )
                return  # Don't cache overly large values

            # Add to end (most recently used)
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()
            self._cache_sizes[key] = value_size
            self._cache_total_size += value_size

            # Evict if over size limit
            while len(self._cache) > self._cache_size:
                self._evict_lru(reason="size")

    def _get_from_cache(self, key: str) -> bytes | None:
        """Get value from cache if available and not expired."""
        with self._cache_lock:
            if key in self._cache:
                # Check if expired
                if time.time() - self._cache_timestamps[key] < self._cache_ttl:
                    # Move to end (mark as recently used)
                    value = self._cache[key]
                    del self._cache[key]
                    self._cache[key] = value
                    self._cache_stats["hits"] += 1
                    return value
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    del self._cache_timestamps[key]

            self._cache_stats["misses"] += 1
            return None

    def _invalidate_cache(self, key: str):
        """Remove an item from cache."""
        with self._cache_lock:
            if key in self._cache:
                size = self._cache_sizes.get(key, 0)
                self._cache_total_size -= size
                del self._cache[key]
                del self._cache_timestamps[key]
                del self._cache_sizes[key]

    @adaptive_retry_db_operation(base_max_retries=8, base_delay=0.05, max_delay=5.0)
    def set_point(self, key: str, value: bytes, synchronous: bool = False) -> None:
        """Set a point with write-through caching and optional background writes.

        Args:
            key: The key to store
            value: The value to store as bytes
            synchronous: If True, writes immediately to database (for critical operations)
        """
        # Always update cache immediately for consistency
        self._update_cache(key, value)

        # Check if we're in an atomic transaction
        in_transaction = getattr(self._in_transaction, "active", False)

        # Synchronous writes or atomic operations bypass queue
        if synchronous or in_transaction:
            with self._get_list_lock(key):
                conn = None
                try:
                    conn = self._get_connection()
                    conn.execute("INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)", (key, value))
                    if not in_transaction:
                        conn.commit()
                    _log.debug(f"Direct write: {key} -> {len(value)} bytes")
                except Exception as e:
                    # On error, invalidate cache entry
                    self._invalidate_cache(key)
                    _log.error(f"Failed to set point {key}: {e}")
                    raise
                finally:
                    if conn and not in_transaction:
                        self._return_pooled_connection(conn)
            return

        # Asynchronous write through queue
        with self._pending_writes_lock:
            # Check if already pending
            if key in self._pending_writes:
                # Update the pending write with new value
                old_event, _ = self._pending_writes[key]
                old_event.set()  # Release old waiter

            # Create completion event with timestamp for latency tracking
            event = threading.Event()
            self._pending_writes[key] = (event, time.time())

        # Queue the write
        try:
            self._write_queue.put((key, value, event), timeout=5.0)
            _log.debug(f"Queued write: {key} -> {len(value)} bytes")
        except queue.Full:
            # Queue full, fall back to synchronous write
            _log.warning("Write queue full, falling back to synchronous write")
            self._invalidate_cache(key)  # Remove from cache since we couldn't queue
            return self.set_point(key, value, synchronous=True)

    def get_point(self, key: str) -> bytes | None:
        """Retrieve a point, checking cache first then database."""
        # Check if there's a pending write for this key
        with self._pending_writes_lock:
            if key in self._pending_writes:
                # Get from cache since write is pending
                cached = self._get_from_cache(key)
                if cached is not None:
                    return cached

        # Try cache first
        cached = self._get_from_cache(key)
        if cached is not None:
            _log.debug(f"Cache hit: {key}")
            return cached

        # Cache miss, get from database
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT value FROM points WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row:
                value = row[0]
                # Update cache with fetched value
                self._update_cache(key, value)
                _log.debug(f"DB fetch: {key} -> found")
                return value
            else:
                _log.debug(f"DB fetch: {key} -> not found")
                return None

        except Exception as e:
            _log.error(f"Failed to get point {key}: {e}")
            return None

    def get_hrefs(self) -> list[str]:
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

    def get_keys_matching(self, pattern: str) -> list[str]:
        """Get all keys that match a pattern."""
        try:
            conn = self._get_connection()

            # Convert simple wildcard pattern to SQL LIKE pattern
            if pattern.endswith("*"):
                sql_pattern = pattern[:-1] + "%"
                cursor = conn.execute("SELECT key FROM points WHERE key LIKE ? ORDER BY key", (sql_pattern,))
            elif "*" in pattern:
                # More complex pattern - convert * to %
                sql_pattern = pattern.replace("*", "%")
                cursor = conn.execute("SELECT key FROM points WHERE key LIKE ? ORDER BY key", (sql_pattern,))
            else:
                # Exact match
                cursor = conn.execute("SELECT key FROM points WHERE key = ?", (pattern,))

            keys = [row[0] for row in cursor.fetchall()]
            _log.debug(f"Pattern '{pattern}' matched {len(keys)} keys")
            return keys
        except Exception as e:
            _log.error(f"Failed to get keys matching '{pattern}': {e}")
            return []

    @adaptive_retry_db_operation(base_max_retries=8, base_delay=0.05, max_delay=5.0)
    def delete_point(self, key: str) -> bool:
        """Delete a point from both cache and database."""
        # Remove from cache immediately
        self._invalidate_cache(key)

        # Delete from database
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.execute("DELETE FROM points WHERE key = ?", (key,))
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, "active", False):
                conn.commit()
            deleted = cursor.rowcount > 0
            _log.debug(f"Deleted point: {key} -> {deleted}")
            return deleted
        except Exception as e:
            _log.error(f"Failed to delete point {key}: {e}")
            return False
        finally:
            if conn and not getattr(self._in_transaction, "active", False):
                self._return_pooled_connection(conn)

    @adaptive_retry_db_operation(base_max_retries=8, base_delay=0.05, max_delay=5.0)
    def clear_all(self) -> None:
        """Clear all points from cache and database. Use with caution!"""
        # Clear cache
        with self._cache_lock:
            self._cache.clear()
            self._cache_timestamps.clear()

        # Clear database
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("DELETE FROM points")
            # Only commit if we're not in an atomic operation
            if not getattr(self._in_transaction, "active", False):
                conn.commit()
            _log.info("Cleared all points from cache and database")
        except Exception as e:
            _log.error(f"Failed to clear all points: {e}")
            raise
        finally:
            if conn and not getattr(self._in_transaction, "active", False):
                self._return_pooled_connection(conn)

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

    @adaptive_retry_db_operation(base_max_retries=5, base_delay=0.02, max_delay=2.0)
    def bulk_set(self, items: dict[str, bytes]) -> None:
        """Set multiple points in a single transaction."""
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.executemany("INSERT OR REPLACE INTO points (key, value) VALUES (?, ?)", list(items.items()))
                conn.commit()
                _log.debug(f"Bulk set {len(items)} points")
            except Exception:
                conn.rollback()
                raise
        except Exception as e:
            _log.error(f"Failed to bulk set points: {e}")
            raise
        finally:
            if conn:
                self._return_pooled_connection(conn)

    def bulk_get(self, keys: list[str]) -> dict[str, bytes]:
        """Get multiple points in a single operation."""
        try:
            conn = self._get_connection()

            # Use parameter placeholders for the IN clause
            placeholders = ",".join(["?" for _ in keys])
            cursor = conn.execute(f"SELECT key, value FROM points WHERE key IN ({placeholders})", keys)

            result = {row[0]: row[1] for row in cursor.fetchall()}
            _log.debug(f"Bulk get {len(result)}/{len(keys)} points")
            return result
        except Exception as e:
            _log.error(f"Failed to bulk get points: {e}")
            return {}

    @contextmanager
    def _get_list_lock(self, key: str):
        """Get a per-list lock to serialize updates to the same list resource."""
        if not key.startswith(("list:", "list_meta:")):
            # Not a list operation, yield immediately
            yield
            return

        # Extract the list name (e.g., 'list:/mup' -> '/mup')
        list_name = key.split(":", 1)[1] if ":" in key else key

        # Get or create a lock for this specific list
        with self._list_locks_lock:
            if list_name not in self._list_locks:
                self._list_locks[list_name] = threading.RLock()
            list_lock = self._list_locks[list_name]

        # Acquire the list-specific lock
        with list_lock:
            yield

    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic operations across multiple point operations."""
        import threading
        import time

        thread_id = threading.current_thread().ident
        start_time = time.time()

        conn = self._get_connection()
        conn_id = id(conn)

        # Check if this specific connection already has an active transaction
        with self._transaction_lock:
            already_in_transaction = conn_id in self._active_transactions

        if already_in_transaction:
            # This connection is already in a transaction, just yield it without starting a new transaction
            _log.debug(f"LOCK DEBUG: Thread {thread_id} reusing existing transaction on connection {conn_id}")
            try:
                yield conn
            finally:
                pass  # Don't commit/rollback nested transactions
            return

        # Not in transaction, start a new one
        # Mark this connection as having an active transaction
        with self._transaction_lock:
            self._active_transactions.add(conn_id)
        _log.debug(f"LOCK DEBUG: Thread {thread_id} starting new transaction at {start_time:.3f}")

        # Retry transaction begin with exponential backoff for lock errors
        max_begin_retries = 3
        for attempt in range(max_begin_retries):
            try:
                conn.execute("BEGIN TRANSACTION")
                begin_time = time.time()
                _log.debug(
                    f"LOCK DEBUG: Thread {thread_id} successfully began transaction (took {(begin_time - start_time) * 1000:.1f}ms)"
                )
                break
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if ("database is locked" in error_msg or "busy" in error_msg) and attempt < max_begin_retries - 1:
                    delay = 0.05 * (2**attempt)  # 50ms, 100ms, 200ms
                    _log.debug(
                        f"LOCK DEBUG: Thread {thread_id} transaction begin locked, retrying in {delay:.3f}s (attempt {attempt + 1}/{max_begin_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    with self._transaction_lock:
                        self._active_transactions.discard(conn_id)
                    fail_time = time.time()
                    _log.error(
                        f"LOCK DEBUG: Thread {thread_id} failed to begin transaction after {(fail_time - start_time) * 1000:.1f}ms: {e}"
                    )
                    raise

        try:
            yield conn
            if not already_in_transaction:
                # Retry commit with exponential backoff for lock errors
                max_commit_retries = 3
                for attempt in range(max_commit_retries):
                    try:
                        commit_start = time.time()
                        _log.debug(
                            f"LOCK DEBUG: Thread {thread_id} committing transaction (held for {(commit_start - start_time) * 1000:.1f}ms)"
                        )
                        conn.commit()
                        commit_end = time.time()
                        _log.debug(
                            f"LOCK DEBUG: Thread {thread_id} successfully committed transaction (commit took {(commit_end - commit_start) * 1000:.1f}ms, total {(commit_end - start_time) * 1000:.1f}ms)"
                        )
                        break
                    except sqlite3.OperationalError as e:
                        error_msg = str(e).lower()
                        if (
                            "database is locked" in error_msg or "busy" in error_msg
                        ) and attempt < max_commit_retries - 1:
                            delay = 0.05 * (2**attempt)  # 50ms, 100ms, 200ms
                            _log.debug(
                                f"LOCK DEBUG: Thread {thread_id} commit locked, retrying in {delay:.3f}s (attempt {attempt + 1}/{max_commit_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            error_time = time.time()
                            _log.error(
                                f"LOCK DEBUG: Thread {thread_id} failed to commit transaction after {(error_time - start_time) * 1000:.1f}ms: {e}"
                            )
                            try:
                                conn.rollback()
                                rollback_time = time.time()
                                _log.debug(
                                    f"LOCK DEBUG: Thread {thread_id} rolled back transaction (rollback took {(rollback_time - error_time) * 1000:.1f}ms)"
                                )
                            except Exception as rollback_e:
                                _log.error(
                                    f"LOCK DEBUG: Thread {thread_id} failed to rollback after commit error: {rollback_e}"
                                )
                            raise
                    except Exception as e:
                        error_time = time.time()
                        _log.error(
                            f"LOCK DEBUG: Thread {thread_id} failed to commit transaction after {(error_time - start_time) * 1000:.1f}ms: {e}"
                        )
                        try:
                            conn.rollback()
                            rollback_time = time.time()
                            _log.debug(
                                f"LOCK DEBUG: Thread {thread_id} rolled back transaction (rollback took {(rollback_time - error_time) * 1000:.1f}ms)"
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
                        f"LOCK DEBUG: Thread {thread_id} rolling back transaction due to exception after {(rollback_start - start_time) * 1000:.1f}ms: {ex}"
                    )
                    conn.rollback()
                    rollback_end = time.time()
                    _log.debug(
                        f"LOCK DEBUG: Thread {thread_id} successfully rolled back transaction (rollback took {(rollback_end - rollback_start) * 1000:.1f}ms)"
                    )
                except Exception as e:
                    _log.error(f"LOCK DEBUG: Thread {thread_id} failed to rollback transaction: {e}")
            else:
                _log.debug(f"LOCK DEBUG: Thread {thread_id} nested operation failed: {ex}")
            raise
        finally:
            if not already_in_transaction:
                # Reset transaction state for this connection
                with self._transaction_lock:
                    self._active_transactions.discard(conn_id)
                final_time = time.time()
                _log.debug(
                    f"LOCK DEBUG: Thread {thread_id} finished transaction on connection {conn_id} (total duration {(final_time - start_time) * 1000:.1f}ms)"
                )

    def close(self) -> None:
        """Close database connections and shutdown background threads."""
        try:
            # Shutdown writer thread
            if self._writer_running:
                _log.info("Shutting down background writer thread")
                self._writer_running = False

                # Flush any remaining writes
                self._flush_write_batch()

                # Wait for writer thread to finish
                if self._writer_thread and self._writer_thread.is_alive():
                    self._writer_thread.join(timeout=5.0)
                    if self._writer_thread.is_alive():
                        _log.warning("Writer thread did not shut down cleanly")

                # Process any remaining items in queue
                remaining = []
                while not self._write_queue.empty():
                    try:
                        remaining.append(self._write_queue.get_nowait())
                    except queue.Empty:
                        break

                if remaining:
                    _log.info(f"Processing {len(remaining)} remaining writes before shutdown")
                    with self._write_batch_lock:
                        self._write_batch.extend(remaining)
                    self._flush_write_batch()

            # Close pooled connections
            if hasattr(self, "_pool") and hasattr(self, "_pool_lock"):
                with self._pool_lock:
                    for conn in self._pool:
                        try:
                            conn.close()
                        except Exception as e:
                            _log.warning(f"Error closing pooled connection: {e}")
                    self._pool.clear()

            # Close thread-local connections
            if hasattr(self._local, "connection"):
                self._local.connection.close()

            _log.info("SQLite point store closed")
        except Exception as e:
            _log.error(f"Error closing SQLite point store: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive database and connection pool statistics."""
        conn = None
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

            # Get WAL file info
            wal_stats = {}
            try:
                cursor = conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                wal_info = cursor.fetchone()
                if wal_info:
                    wal_stats = {
                        "wal_frames": wal_info[1] if len(wal_info) > 1 else 0,
                        "wal_checkpointed": wal_info[2] if len(wal_info) > 2 else 0,
                    }
            except Exception as e:
                _log.debug(f"Could not get WAL stats: {e}")

            # Get load metrics
            load_metrics = _load_monitor.get_load_metrics()

            # Connection pool stats
            with self._pool_lock:
                pool_stats = self._pool_stats.copy()
                pool_stats["available_connections"] = len(self._connection_pool)
                pool_stats["max_connections"] = self._max_connections

            # Cache stats with memory information
            with self._cache_lock:
                cache_info = {
                    "size": len(self._cache),
                    "max_size": self._cache_size,
                    "memory_bytes": self._cache_total_size,
                    "max_memory_bytes": self._max_cache_memory,
                    "memory_usage_pct": (self._cache_total_size / self._max_cache_memory * 100)
                    if self._max_cache_memory > 0
                    else 0,
                    "ttl_seconds": self._cache_ttl,
                    "stats": self._cache_stats.copy(),
                }
                cache_info["stats"]["hit_rate"] = cache_info["stats"]["hits"] / max(
                    1, cache_info["stats"]["hits"] + cache_info["stats"]["misses"]
                )

                # Log stats periodically
                self._log_stats_if_needed(cache_info)

            # Queue stats with latency metrics
            with self._queue_latency_lock:
                if self._queue_latencies:
                    avg_latency = sum(self._queue_latencies) / len(self._queue_latencies)
                    max_latency = max(self._queue_latencies)
                    p95_latency = (
                        sorted(self._queue_latencies)[int(len(self._queue_latencies) * 0.95)]
                        if len(self._queue_latencies) > 20
                        else max_latency
                    )
                else:
                    avg_latency = max_latency = p95_latency = 0.0

            queue_info = {
                "queue_size": self._write_queue.qsize(),
                "batch_size": len(self._write_batch),
                "pending_writes": len(self._pending_writes),
                "writer_running": self._writer_running,
                "avg_latency_ms": avg_latency * 1000,
                "max_latency_ms": max_latency * 1000,
                "p95_latency_ms": p95_latency * 1000,
            }

            return {
                "database": {
                    "total_points": total_points,
                    "db_size_bytes": db_size,
                    "db_file": self._db_path,
                    "sample_keys": sample_keys,
                    "wal_stats": wal_stats,
                },
                "cache": cache_info,
                "write_queue": queue_info,
                "connection_pool": pool_stats,
                "load_metrics": load_metrics,
                "performance": {
                    "pool_hit_rate": pool_stats["pool_hits"]
                    / max(1, pool_stats["pool_hits"] + pool_stats["pool_misses"]),
                    "cache_hit_rate": cache_info["stats"]["hit_rate"],
                    "active_load_factor": load_metrics["load_factor"],
                    "failure_rate": load_metrics["failure_rate"],
                },
            }
        except Exception as e:
            _log.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                self._return_pooled_connection(conn)

    def optimize_database(self):
        """Perform database optimization for better performance."""
        conn = None
        try:
            conn = self._get_connection()
            _log.info("Starting database optimization...")

            # Analyze and optimize tables
            conn.execute("ANALYZE")
            conn.execute("PRAGMA optimize")

            # Checkpoint WAL file to reduce size
            conn.execute("PRAGMA wal_checkpoint(RESTART)")

            # Vacuum if database is fragmented (check free pages)
            cursor = conn.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]

            cursor = conn.execute("PRAGMA page_count")
            total_pages = cursor.fetchone()[0]

            if total_pages > 1000 and free_pages > total_pages * 0.1:  # More than 10% fragmentation
                _log.info(f"Database fragmented ({free_pages}/{total_pages} free pages), running VACUUM...")
                conn.execute("VACUUM")
                _log.info("VACUUM completed")

            _log.info("Database optimization completed")

        except Exception as e:
            _log.error(f"Database optimization failed: {e}")
            raise
        finally:
            if conn:
                self._return_pooled_connection(conn)

    def _track_queue_latency(self, latency: float):
        """Track queue latency for monitoring."""
        with self._queue_latency_lock:
            self._queue_latencies.append(latency)
            self._cache_stats["queue_latency_sum"] += latency
            self._cache_stats["queue_latency_count"] += 1
            if latency > self._cache_stats["max_queue_latency"]:
                self._cache_stats["max_queue_latency"] = latency

    def _log_stats_if_needed(self, cache_info: dict):
        """Log statistics periodically for monitoring."""
        current_time = time.time()
        if current_time - self._last_stats_log >= self._stats_log_interval:
            self._last_stats_log = current_time

            # Get queue info for logging
            with self._queue_latency_lock:
                if self._queue_latencies:
                    avg_latency = sum(self._queue_latencies) / len(self._queue_latencies)
                    max_latency = max(self._queue_latencies)
                else:
                    avg_latency = max_latency = 0.0

            # Prepare stats snapshot
            stats_snapshot = {
                "timestamp": datetime.now().isoformat(),
                "cache": {
                    "entries": cache_info["size"],
                    "memory_mb": cache_info["memory_bytes"] / (1024 * 1024),
                    "memory_pct": cache_info["memory_usage_pct"],
                    "hit_rate": cache_info["stats"]["hit_rate"],
                    "hits": cache_info["stats"]["hits"],
                    "misses": cache_info["stats"]["misses"],
                    "evictions": cache_info["stats"]["evictions"],
                    "evictions_memory": cache_info["stats"]["evictions_memory"],
                    "evictions_size": cache_info["stats"]["evictions_size"],
                },
                "queue": {
                    "size": self._write_queue.qsize(),
                    "pending": len(self._pending_writes),
                    "avg_latency_ms": avg_latency * 1000,
                    "max_latency_ms": max_latency * 1000,
                    "writes_queued": self._cache_stats["writes_queued"],
                    "writes_flushed": self._cache_stats["writes_flushed"],
                    "batches": self._cache_stats["write_batches"],
                },
                "connections": {
                    "pool_size": len(self._connection_pool),
                    "max_connections": self._max_connections,
                    "active": _load_monitor._active_connections,
                },
            }

            # Store in history
            self._stats_history.append(stats_snapshot)

            # Log as structured data for monitoring
            _log.info(f"PERF_MONITOR: {json.dumps(stats_snapshot, separators=(',', ':'))}")

    def get_monitoring_data(self) -> dict[str, Any]:
        """Get comprehensive monitoring data for visualization dashboards."""
        # Get current stats
        current_stats = self.get_stats()

        # Historical data
        with self._cache_lock:
            history = list(self._stats_history)

        return {
            "current": current_stats,
            "history": history,
            "metadata": {
                "collection_interval_seconds": self._stats_log_interval,
                "history_size": len(history),
                "uptime_seconds": time.time() - self._cache_stats["last_stats_reset"],
                "cache_memory_limit_mb": self._max_cache_memory / (1024 * 1024),
                "cache_size_limit": self._cache_size,
            },
        }

    def reset_stats(self):
        """Reset statistics counters (useful for testing or periodic resets)."""
        with self._cache_lock:
            # Reset counters but keep structural data
            self._cache_stats.update(
                {
                    "hits": 0,
                    "misses": 0,
                    "evictions": 0,
                    "evictions_memory": 0,
                    "evictions_size": 0,
                    "writes_queued": 0,
                    "writes_flushed": 0,
                    "write_batches": 0,
                    "queue_timeouts": 0,
                    "queue_latency_sum": 0.0,
                    "queue_latency_count": 0,
                    "max_queue_latency": 0.0,
                    "last_stats_reset": time.time(),
                }
            )

        with self._queue_latency_lock:
            self._queue_latencies.clear()

        _log.info("Performance statistics reset")

    def get_all_keys_with_prefix(self, prefix: str) -> list[str]:
        """Get all database keys that start with the given prefix.

        Args:
            prefix: The prefix to search for

        Returns:
            list: All keys starting with the prefix
        """
        with self._lock:
            try:
                conn = self._get_pooled_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT key FROM points WHERE key LIKE ?", (f"{prefix}%",))
                    rows = cursor.fetchall()
                    return [row[0] for row in rows]
                finally:
                    self._return_pooled_connection(conn)
            except Exception as e:
                _log.error(f"Failed to get keys with prefix '{prefix}': {e}")
                return []


if __name__ == "__main__":
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
