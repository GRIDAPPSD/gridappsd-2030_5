# ieee_2030_5/adapters/base.py
"""
Thread-safe base adapter classes for IEEE 2030.5 server.

This module provides the foundation for thread-safe data access patterns in the IEEE 2030.5
server implementation. It includes:

- Base adapter classes with configurable concurrency control
- Reader-writer locks for high-performance read-heavy workloads
- Resource-specific locking for fine-grained concurrency
- Performance tracking and monitoring capabilities
- Specialized adapters for List and EndDevice resources

Classes:
    AdapterResult: Result wrapper for adapter operations with metadata
    ConcurrencyMode: Constants for different concurrency control strategies
    ResourceLockManager: Fine-grained resource-specific locking
    ReadWriteLock: Reader-writer lock implementation for concurrent access
    ThreadSafeAdapter: Abstract base class for all thread-safe adapters
    ThreadSafeListAdapter: Adapter for IEEE 2030.5 List resources
    ThreadSafeEndDeviceAdapter: Specialized adapter for EndDevice resources

The adapter pattern allows for consistent, thread-safe access to IEEE 2030.5 resources
while supporting different concurrency strategies based on usage patterns. Read-heavy
workloads benefit from reader-writer locks, while write-heavy workloads can use
traditional mutex locks.

Example:
    >>> # Initialize adapters (done automatically on import)
    >>> initialize_adapters()
    >>>
    >>> # Access global adapter instances
    >>> if ListAdapter is not None:
    ...     result = ListAdapter.fetch_all(0, 10)
    ...     if result.success:
    ...         print(f"Found {len(result.data)} items")

Threading Model:
    All adapters are thread-safe and designed for concurrent access. The concurrency
    mode can be configured per adapter:

    - READ_WRITE_LOCK: Optimized for read-heavy workloads (default)
    - MUTEX: Simple mutual exclusion for write-heavy workloads
    - OPTIMISTIC: Optimistic locking with retry (future enhancement)

Performance:
    Adapters track operation counts and timing for monitoring and debugging.
    Use get_adapter_stats() to retrieve performance metrics.
"""

import logging
import threading
import time
from abc import ABC
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Union

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.persistance.points import atomic_operation, get_db

_log = logging.getLogger(__name__)
T = TypeVar("T")
LockType = Union["ReadWriteLock", threading.RLock]


@dataclass
class AdapterResult:
    """Result of an adapter operation with metadata.

    This class provides a standardized way to return results from adapter operations,
    including success/failure status, data payload, error information, and operation
    metadata. It enables consistent error handling and result processing across all
    adapter implementations.

    Attributes:
        success (bool): Whether the operation completed successfully
        data (Any, optional): The result data from the operation. For fetch operations,
            this contains the retrieved object(s). For create/update operations, this
            may contain the created/updated object or confirmation data.
        error (str | None, optional): Error message if the operation failed. None if
            the operation succeeded.
        was_update (bool, optional): For create/update operations, indicates whether
            an existing resource was updated (True) or a new resource was created (False).
            Defaults to False.
        location (str | None, optional): For create operations, the location (href) of
            the newly created resource. Used in HTTP responses for proper resource
            location headers.

    Examples:
        >>> # Successful fetch operation
        >>> result = AdapterResult(success=True, data=device_obj)
        >>>
        >>> # Failed operation with error
        >>> result = AdapterResult(success=False, error="Device not found")
        >>>
        >>> # Successful create operation
        >>> result = AdapterResult(
        ...     success=True,
        ...     data=new_device,
        ...     was_update=False,
        ...     location="/edev/123"
        ... )
    """

    success: bool
    data: Any = None
    error: str | None = None
    was_update: bool = False
    location: str | None = None
    status_code: int | None = None


class ConcurrencyMode:
    """Concurrency control modes for adapters.

    This class defines constants for different concurrency control strategies that
    can be used by ThreadSafeAdapter implementations. The choice of concurrency mode
    affects performance characteristics and should be selected based on the expected
    read/write patterns of the adapter.

    Constants:
        READ_WRITE_LOCK: Uses reader-writer locks that allow multiple concurrent readers
            but exclusive write access. This is optimal for read-heavy workloads where
            many threads need to read data simultaneously but writes are infrequent.
            This is the default mode for most adapters.

        MUTEX: Uses a simple mutual exclusion lock (threading.RLock) that allows only
            one thread at a time to access the resource. This is simpler but less
            performant for read-heavy workloads. Use when write operations are frequent
            or when simpler locking semantics are preferred.

        OPTIMISTIC: Planned for future implementation. Will use optimistic locking
            with conflict detection and retry logic. Suitable for low-contention
            scenarios where conflicts are rare.

    Example:
        >>> adapter = ThreadSafeListAdapter(
        ...     model_class=MyModel,
        ...     concurrency_mode=ConcurrencyMode.READ_WRITE_LOCK
        ... )
    """

    READ_WRITE_LOCK = "rw_lock"  # Reader-writer locks (best for read-heavy)
    MUTEX = "mutex"  # Simple mutual exclusion
    OPTIMISTIC = "optimistic"  # Optimistic locking with retry


class ResourceLockManager:
    """Manages fine-grained locks for individual resources.

    This class provides a mechanism for creating and managing locks on a per-resource
    basis, allowing for fine-grained concurrency control. Instead of locking an entire
    adapter, individual resources can be locked independently, improving concurrency
    when different threads are working with different resources.

    The manager maintains a dictionary of locks keyed by resource ID and ensures
    thread-safe creation of new locks when needed. Locks are reentrant (RLock) to
    allow the same thread to acquire the same resource lock multiple times.

    Attributes:
        _locks: Dictionary mapping resource IDs to their corresponding locks
        _locks_lock: Master lock for thread-safe modification of the locks dictionary

    Example:
        >>> manager = ResourceLockManager()
        >>> with manager.lock_resource("device_123"):
        ...     # Perform operations on device_123
        ...     pass
    """

    def __init__(self):
        """Initialize the resource lock manager.

        Creates empty lock dictionary and master lock for thread-safe access.
        """
        self._locks: dict[str, threading.RLock] = {}
        self._locks_lock = threading.Lock()

    def get_resource_lock(self, resource_id: str) -> threading.RLock:
        """Get or create a lock for a specific resource.

        This method retrieves an existing lock for the given resource ID, or creates
        a new one if none exists. The operation is thread-safe.

        Args:
            resource_id: Unique identifier for the resource to lock

        Returns:
            threading.RLock: A reentrant lock for the specified resource

        Thread Safety:
            This method is thread-safe and can be called concurrently from multiple threads.
        """
        with self._locks_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = threading.RLock()
            return self._locks[resource_id]

    @contextmanager
    def lock_resource(self, resource_id: str):
        """Context manager for locking a specific resource.

        This provides a convenient way to acquire and automatically release a
        resource-specific lock using Python's 'with' statement. The lock will
        be automatically released when the context exits, even if an exception
        occurs.

        Args:
            resource_id: Unique identifier for the resource to lock

        Yields:
            None: Context manager yields control to the caller while holding the lock

        Raises:
            TimeoutError: If the lock cannot be acquired within 30 seconds

        Example:
            >>> manager = ResourceLockManager()
            >>> with manager.lock_resource("device_123"):
            ...     # Critical section - only one thread can access device_123
            ...     modify_device("device_123")
        """
        lock = self.get_resource_lock(resource_id)
        acquired = lock.acquire(timeout=30)  # 30 second timeout
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for resource {resource_id}")
        try:
            yield
        finally:
            lock.release()


class ReadWriteLock:
    """Reader-writer lock implementation for read-heavy workloads.

    This class implements a reader-writer lock that allows multiple concurrent readers
    OR a single exclusive writer, but not both simultaneously. This is ideal for
    scenarios where reads are much more frequent than writes, as it allows multiple
    threads to read data concurrently while ensuring data consistency during writes.

    The implementation uses condition variables to coordinate between readers and writers:
    - Multiple readers can acquire the lock simultaneously
    - Writers wait for all readers to finish before acquiring exclusive access
    - Readers wait for any active writer to finish before acquiring shared access

    Attributes:
        _readers: Current number of active readers holding the lock
        _writers: Current number of active writers (should be 0 or 1)
        _read_ready: Condition variable for coordinating reader access
        _write_ready: Condition variable for coordinating writer access

    Thread Safety:
        This class is fully thread-safe and designed for high-concurrency scenarios.

    Performance:
        - Read operations scale linearly with the number of CPU cores
        - Write operations have exclusive access ensuring consistency
        - No reader starvation under normal conditions

    Example:
        >>> rw_lock = ReadWriteLock()
        >>>
        >>> # Multiple readers can access simultaneously
        >>> with rw_lock.reader():
        ...     data = read_shared_data()
        >>>
        >>> # Writers get exclusive access
        >>> with rw_lock.writer():
        ...     modify_shared_data()
    """

    def __init__(self):
        """Initialize the reader-writer lock.

        Creates the internal state tracking and condition variables needed
        for coordinating reader and writer access.
        """
        self._readers = 0
        self._writers = 0
        self._read_ready = threading.Condition(threading.RLock())
        self._write_ready = threading.Condition(threading.RLock())

    @contextmanager
    def reader(self):
        """Acquire reader lock for shared read access.

        This context manager allows multiple threads to acquire read access
        simultaneously. The calling thread will block if there are any active
        writers, but can proceed immediately if only other readers are active.

        Yields:
            None: Context manager yields control while holding the reader lock

        Blocking Behavior:
            - Blocks if any writer is active
            - Proceeds immediately if no writers are active
            - Multiple readers can be active simultaneously

        Example:
            >>> rw_lock = ReadWriteLock()
            >>> with rw_lock.reader():
            ...     # Safe to read shared data
            ...     # Multiple threads can be in this section simultaneously
            ...     data = shared_resource.read()
        """
        with self._read_ready:
            while self._writers > 0:
                self._read_ready.wait()
            self._readers += 1
        try:
            yield
        finally:
            with self._read_ready:
                self._readers -= 1
                if self._readers == 0:
                    self._read_ready.notify_all()

    @contextmanager
    def writer(self):
        """Acquire writer lock for exclusive write access.

        This context manager provides exclusive access for write operations.
        The calling thread will block until all readers and any other writers
        have released their locks. Once acquired, no other readers or writers
        can access the resource.

        Yields:
            None: Context manager yields control while holding the exclusive writer lock

        Blocking Behavior:
            - Blocks if any readers are active
            - Blocks if any other writer is active
            - Provides exclusive access once acquired

        Example:
            >>> rw_lock = ReadWriteLock()
            >>> with rw_lock.writer():
            ...     # Exclusive access to shared data
            ...     # No other readers or writers can be active
            ...     shared_resource.modify()
        """
        with self._write_ready:
            while self._writers > 0 or self._readers > 0:
                self._write_ready.wait()
            self._writers += 1
        try:
            yield
        finally:
            with self._write_ready:
                self._writers -= 1
                self._write_ready.notify_all()
            with self._read_ready:
                self._read_ready.notify_all()


class ThreadSafeAdapter(Generic[T], ABC):
    """Base class for all thread-safe adapters.

    This abstract base class provides the foundation for all thread-safe data access
    adapters in the IEEE 2030.5 server. It implements configurable concurrency control,
    performance tracking, and common data access patterns that are inherited by all
    concrete adapter implementations.

    The adapter pattern provides a consistent interface for CRUD operations while
    abstracting the underlying storage mechanism and ensuring thread safety through
    various concurrency control strategies.

    Type Parameters:
        T: The model type that this adapter manages (e.g., EndDevice, List, etc.)

    Attributes:
        model_class: The Python class of the model this adapter manages
        concurrency_mode: The concurrency control strategy (READ_WRITE_LOCK, MUTEX, etc.)
        _lock: The primary lock for this adapter (ReadWriteLock or RLock based on mode)
        _resource_locks: Manager for fine-grained resource-specific locks
        _db: Database connection for persistence operations
        _operation_count: Performance tracking for operation counts by type
        _last_operation_time: Performance tracking for operation timing

    Concurrency Control:
        The adapter supports multiple concurrency strategies:
        - READ_WRITE_LOCK: Optimized for read-heavy workloads (default)
        - MUTEX: Simple mutual exclusion for write-heavy workloads
        - OPTIMISTIC: Planned for future conflict detection and retry

    Performance Tracking:
        All operations are tracked for monitoring and debugging:
        - Operation counts by type (fetch, create, update, delete)
        - Last operation timestamps for each operation type
        - Available via get_stats() method

    Subclass Requirements:
        Concrete subclasses must implement abstract methods for their specific
        data access patterns. Common patterns include list-based storage and
        specialized indexed storage for complex objects.

    Thread Safety:
        All public methods are thread-safe and can be called concurrently from
        multiple threads. Internal methods starting with underscore may require
        external synchronization.

    Example:
        >>> class MyAdapter(ThreadSafeAdapter[MyModel]):
        ...     def fetch_all(self, start, limit):
        ...         # Implementation specific to MyModel
        ...         pass
        >>>
        >>> adapter = MyAdapter(MyModel, ConcurrencyMode.READ_WRITE_LOCK)
        >>> result = adapter.fetch_by_href("/my/resource/123")
    """

    _lock: LockType

    def __init__(self, model_class: type[T], concurrency_mode: str = ConcurrencyMode.READ_WRITE_LOCK):
        """Initialize the thread-safe adapter.

        Args:
            model_class: The Python class of the model this adapter manages
            concurrency_mode: The concurrency control strategy to use
                (defaults to READ_WRITE_LOCK for optimal read performance)
        """
        self.model_class = model_class
        self.concurrency_mode = concurrency_mode

        # Initialize appropriate locking mechanism
        if concurrency_mode == ConcurrencyMode.READ_WRITE_LOCK:
            self._lock = ReadWriteLock()
        else:
            self._lock = threading.RLock()

        self._resource_locks = ResourceLockManager()
        self._db = get_db()

        # Performance metrics
        self._operation_count: dict[str, int] = defaultdict(int)
        self._last_operation_time: dict[str, float] = {}

    def fetch_index(self, href: str) -> int | None:
        """Extract and return the resource index from its href.

        This method provides backward compatibility for older code that expects
        to work with numeric indices. It attempts to extract the index from the
        href path, and if that fails, it will fetch the object and extract the
        index from the object's href.

        Args:
            href: The resource href string (e.g., "/edev/123" or "/list/456")

        Returns:
            The resource index if found, otherwise None

        Performance:
            This method is tracked for performance monitoring. For new code,
            consider using fetch_by_href() directly instead of relying on
            numeric indices.

        Example:
            >>> adapter = SomeAdapter(SomeModel)
            >>> index = adapter.fetch_index("/edev/123")  # Returns 123
            >>> index = adapter.fetch_index("/invalid")   # Returns None
        """
        self._track_operation("fetch_index")
        try:
            # Try to extract index from href directly
            parts = href.split("/")
            if parts and parts[-1].isdigit():
                return int(parts[-1])

            # If that fails, try to look up the object and then extract its index
            obj = self.fetch_by_href(href)
            if obj and hasattr(obj, "href"):
                parts = obj.href.split("/")
                if parts and parts[-1].isdigit():
                    return int(parts[-1])

            return None
        except Exception as e:
            _log.error(f"Failed to fetch index for href {href}: {e}")
            return None

    def fetch_by_href(self, href: str) -> T | None:
        """Fetch an object by its href.

        This is a fundamental method for retrieving resources by their unique href
        identifier. It's used extensively throughout the IEEE 2030.5 server for
        resource lookups and cross-references. The method uses optimized index
        lookups when available and falls back to property-based searches.

        Args:
            href: The href to search for (e.g., "/edev/123", "/list/456")

        Returns:
            The object if found, otherwise None

        Thread Safety:
            This method acquires a read lock and is safe for concurrent access
            by multiple threads.

        Performance:
            - Uses index-based lookup for O(1) performance when available
            - Falls back to linear search for O(n) when index not available
            - All calls are tracked for performance monitoring

        Example:
            >>> adapter = EndDeviceAdapter()
            >>> device = adapter.fetch_by_href("/edev/123")
            >>> if device:
            ...     print(f"Found device: {device.lFDI}")
        """
        with self._read_lock():
            self._track_operation("fetch_by_href")

            try:
                # Check if we have a specialized index for hrefs
                href_index_key = f"index:{self.model_class.__name__.lower()}:href"
                import pickle

                # Try to get the index
                index_data = self._db.get_point(href_index_key)
                if index_data:
                    href_index = pickle.loads(index_data)
                    obj_index = href_index.get(href)

                    if obj_index is not None:
                        # Get object using the index
                        obj_key = f"{self.model_class.__name__.lower()}:{obj_index}"
                        obj_data = self._db.get_point(obj_key)

                        if obj_data:
                            return pickle.loads(obj_data)

                # Fall back to generic property search
                return self.fetch_by_property("href", href)

            except Exception as e:
                _log.error(f"Failed to fetch object by href {href}: {e}")
                return None

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> T | None:
        """Fetch an object by a specific property value.

        This is a generic property-based lookup method that can be used when
        href-based lookups are not applicable. The base implementation is a
        placeholder that should be overridden by subclasses with optimized
        lookup mechanisms such as indexes or property-specific search logic.

        Args:
            prop_name: The name of the property to search by (e.g., "lFDI", "href")
            prop_value: The value to search for. Type should match the property type.

        Returns:
            The first object found with the matching property value, or None if
            no match is found.

        Thread Safety:
            This method is thread-safe when overridden properly in subclasses.
            The base implementation does not perform any actual search.

        Performance:
            Base implementation has O(1) performance (returns None immediately).
            Subclass implementations should provide appropriate performance
            characteristics based on their indexing strategies.

        Example:
            >>> adapter = EndDeviceAdapter()
            >>> device = adapter.fetch_by_property("lFDI", b"some_lfdi_bytes")
            >>> if device:
            ...     print(f"Found device at {device.href}")

        Note:
            This base implementation logs a warning and returns None. Subclasses
            should override this method to provide actual functionality.
        """
        _log.warning(f"Using unimplemented base fetch_by_property for {self.model_class.__name__}")
        return None

    @contextmanager
    def _read_lock(self):
        """Acquire read lock based on concurrency mode."""
        if self.concurrency_mode == ConcurrencyMode.READ_WRITE_LOCK:
            with self._lock.reader():
                yield
        else:
            with self._lock:
                yield

    @contextmanager
    def _write_lock(self):
        """Acquire write lock based on concurrency mode."""
        if self.concurrency_mode == ConcurrencyMode.READ_WRITE_LOCK:
            with self._lock.writer():
                yield
        else:
            with self._lock:
                yield

    @contextmanager
    def _resource_lock(self, resource_id: str):
        """Lock a specific resource for fine-grained control."""
        with self._resource_locks.lock_resource(resource_id):
            yield

    def _track_operation(self, operation: str):
        """Track operation for performance monitoring."""
        self._operation_count[operation] += 1
        self._last_operation_time[operation] = time.time()

    def get_stats(self) -> dict[str, Any]:
        """Get adapter performance statistics.

        This method returns comprehensive performance and monitoring data
        for the adapter instance. The statistics are useful for debugging,
        performance monitoring, and system health checks.

        Returns:
            Dict[str, Any]: Dictionary containing performance statistics:
                - 'operation_counts': Dict mapping operation names to their
                  execution count (e.g., {"fetch_by_href": 42, "put": 15})
                - 'last_operation_times': Dict mapping operation names to their
                  last execution timestamp (Unix timestamp)
                - 'concurrency_mode': The current concurrency control mode
                  (READ_WRITE_LOCK, MUTEX, etc.)

        Thread Safety:
            This method is thread-safe and can be called concurrently.

        Performance:
            O(1) operation that returns snapshots of internal counters.

        Example:
            >>> adapter = ThreadSafeListAdapter(MyModel)
            >>> # ... perform some operations ...
            >>> stats = adapter.get_stats()
            >>> print(f"Fetch operations: {stats['operation_counts'].get('fetch_by_href', 0)}")
            >>> print(f"Concurrency mode: {stats['concurrency_mode']}")
            >>>
            >>> # Check if operations happened recently
            >>> import time
            >>> last_fetch = stats['last_operation_times'].get('fetch_by_href', 0)
            >>> if time.time() - last_fetch < 60:
            ...     print("Recent fetch activity detected")
        """
        return {
            "operation_counts": dict(self._operation_count),
            "last_operation_times": dict(self._last_operation_time),
            "concurrency_mode": self.concurrency_mode,
        }


class ThreadSafeListAdapter(ThreadSafeAdapter[T]):
    """Thread-safe adapter for managing lists of IEEE 2030.5 objects.

    This adapter provides thread-safe access to list-based collections of IEEE 2030.5
    resources. It supports dynamic list creation, atomic operations on list items,
    and efficient list management with automatic sizing and metadata tracking.

    The adapter is optimized for scenarios where multiple threads need to access
    and modify lists of objects concurrently. It provides both list-level operations
    (get entire list, set entire list) and item-level operations (get/put individual
    items by index).

    Key Features:
        - Dynamic list initialization with configurable parameters
        - Thread-safe append, get, put, and delete operations
        - Automatic list sizing and metadata management
        - Support for both list and single-object storage patterns
        - Property-based object lookups with optional filtering
        - Comprehensive error handling and result reporting

    Storage Model:
        Lists are stored with metadata including size, object type, and creation
        parameters. Individual items are stored separately for efficient access.
        The storage keys follow patterns like:
        - List metadata: "{list_uri}:meta"
        - List items: "{list_uri}:{index}"
        - Single objects: "{uri}"

    Thread Safety:
        All public methods are thread-safe using reader-writer locks for optimal
        performance on read-heavy workloads. Write operations use exclusive locks.

    Example:
        >>> adapter = ThreadSafeListAdapter(EndDevice)
        >>>
        >>> # Initialize a new list
        >>> adapter.initialize_uri("/edev", EndDevice, all=10, results=5)
        >>>
        >>> # Add items to the list
        >>> device = EndDevice(href="/edev/0")
        >>> result = adapter.append("/edev", device)
        >>>
        >>> # Retrieve items
        >>> devices = adapter.get_list("/edev")
        >>> device = adapter.get("/edev", 0)
    """

    def __init__(self, model_class: type[T]):
        super().__init__(model_class, ConcurrencyMode.READ_WRITE_LOCK)
        self._db = get_db()

    def _get_list_key(self, list_uri: str) -> str:
        """Get storage key for a list."""
        return f"list:{list_uri}"

    def _get_metadata_key(self, list_uri: str) -> str:
        """Get storage key for list metadata."""
        return f"list_meta:{list_uri}"

    def initialize_uri(self, list_uri: str, obj_type: type[T] | None = None, **kwargs) -> bool:
        """Initialize a new list URI with metadata and configuration.

        This method creates a new list at the specified URI with initial metadata
        and configuration parameters. It's used to set up list storage before
        adding items to the list.

        Args:
            list_uri: The URI path for the list (e.g., "/edev", "/dr/programs")
            obj_type: The type of objects that will be stored in this list.
                If None, uses the adapter's model_class.
            **kwargs: Additional configuration parameters:
                - all: Maximum number of items the list can contain
                - results: Number of results to return by default in queries
                - subscribable: Whether the list supports subscriptions
                - list_uri: Alternative way to specify the URI (backward compatibility)
                - obj: Alternative way to specify the object type (backward compatibility)

        Returns:
            bool: True if the list was successfully initialized, False if it
                already exists or initialization failed.

        Thread Safety:
            This method is thread-safe and uses write locks to ensure exclusive
            access during list creation.

        Storage:
            Creates metadata entry with configuration and initializes empty list.
            The metadata includes object type, creation parameters, and timestamps.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>>
            >>> # Initialize a list for end devices with capacity of 100
            >>> success = adapter.initialize_uri("/edev", EndDevice, all=100, results=20)
            >>> if success:
            ...     print("List initialized successfully")
            >>>
            >>> # Initialize with backward compatibility parameters
            >>> adapter.initialize_uri("/programs", obj=Program, all=50)

        Note:
            If a list already exists at the URI, this method returns False without
            modifying the existing list.


        Returns:
            bool: True if initialized, False if already existed
        """
        # Support for both positional and named arguments
        if obj_type is None:
            # Check for 'obj' parameter for backward compatibility
            obj_type = kwargs.get("obj")

        # If list_uri is provided as a named parameter, use it
        if "list_uri" in kwargs and not list_uri:
            list_uri = kwargs.get("list_uri", "")

        if not list_uri or not obj_type:
            raise ValueError("Both list_uri and obj_type/obj must be provided")

        list_key = self._get_list_key(list_uri)

        with self._write_lock():
            self._track_operation("initialize_uri")

            if self._db.exists(list_key):
                return False  # Already exists

            try:
                with atomic_operation():
                    # Initialize empty list
                    import pickle

                    empty_list: list[T] = []
                    self._db.set_point(list_key, pickle.dumps(empty_list))

                    # Store metadata
                    metadata = {"type": obj_type.__name__, "created": time.time(), "count": 0}
                    self._db.set_point(self._get_metadata_key(list_uri), pickle.dumps(metadata))

                _log.debug(f"Initialized list URI: {list_uri}")
                return True
            except Exception as e:
                _log.error(f"Failed to initialize URI {list_uri}: {e}")
                raise

    def append(self, list_uri: str, obj: T, synchronous: bool = False) -> AdapterResult:
        """Append an object to the end of a list.

        This method adds a new object to the end of the specified list in a
        thread-safe manner. If the list does not exist, it will be automatically
        initialized with default parameters.

        Args:
            list_uri: The URI of the list to append to (e.g., "/edev", "/programs")
            obj: The object to append to the list. Must be of type T.
            synchronous: If True, forces immediate write bypassing queue (critical for MUP creation)

        Returns:
            AdapterResult: Result of the append operation containing:
                - success: True if the object was successfully appended
                - data: The appended object with updated href if applicable
                - location: The href/location of the newly added object
                - error: Error message if the operation failed

        Thread Safety:
            This method is thread-safe and uses resource-specific locking to
            prevent concurrent modifications to the same list.

        Performance:
            O(n) where n is the current list size, due to list serialization.
            For better performance with large lists, consider using indexed
            storage patterns.

        Auto-initialization:
            If the target list does not exist, it will be automatically created
            with the object type inferred from the appended object.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> device = EndDevice(href="/edev/0")
            >>> result = adapter.append("/edev", device)
            >>> if result.success:
            ...     print(f"Added device at {result.location}")
            >>> else:
            ...     print(f"Failed: {result.error}")

        Raises:
            Exception: If database operations fail or object serialization fails
        """
        list_key = self._get_list_key(list_uri)

        with self._resource_lock(list_uri):
            self._track_operation("append")

            try:
                with atomic_operation():
                    import pickle

                    # Get current list
                    list_data = self._db.get_point(list_key)
                    if list_data is None:
                        # Auto-initialize if needed
                        self.initialize_uri(list_uri, type(obj))
                        current_list = []
                    else:
                        current_list = pickle.loads(list_data)

                    # Add href to object if not present
                    if not hasattr(obj, "href") or not obj.href:
                        obj.href = f"{list_uri}_{len(current_list)}"  # type: ignore[attr-defined]

                    # Append object
                    current_list.append(obj)

                    # Store updated list and metadata in sequence to reduce lock contention
                    # During burst periods, add tiny delay to allow batching of rapid requests
                    import time

                    now = time.time()

                    # For burst mitigation: if this is a list operation and we're in a burst,
                    # add jitter to spread out database writes
                    if hasattr(self, "_last_write_time"):
                        time_since_last = now - getattr(self, "_last_write_time", 0)
                        if time_since_last < 0.1:  # If last write was < 100ms ago (burst detected)
                            # Add larger randomized delay (5-50ms) to spread out writes during bursts
                            import random

                            jitter = random.uniform(0.005, 0.05)
                            time.sleep(jitter)
                            _log.debug(
                                f"Burst detected (last write {time_since_last * 1000:.1f}ms ago), added {jitter * 1000:.1f}ms jitter"
                            )

                    # Store updated list (synchronous for critical operations like MUP creation)
                    self._db.set_point(list_key, pickle.dumps(current_list), synchronous=synchronous)

                    # Register mRID if the object has one
                    if hasattr(obj, "mRID") and obj.mRID is not None and hasattr(obj, "href"):
                        try:
                            global _GlobalMRIDs
                            if _GlobalMRIDs is not None:
                                obj_type = type(obj).__name__
                                _GlobalMRIDs.register_mrid(obj.mRID, obj.href, obj_type)
                                _log.debug(f"Registered mRID {obj.mRID} -> {obj_type}:{obj.href}")
                        except Exception as e:
                            _log.debug(f"mRID registration failed in append: {e}")

                    # Update metadata (synchronous for critical operations)
                    metadata = self._get_list_metadata(list_uri)
                    metadata["count"] = len(current_list)
                    metadata["last_modified"] = time.time()
                    self._db.set_point(
                        self._get_metadata_key(list_uri), pickle.dumps(metadata), synchronous=synchronous
                    )

                    # Track last write time for burst detection
                    self._last_write_time = time.time()

                _log.debug(f"Appended object to {list_uri}, new count: {len(current_list)}")
                return AdapterResult(success=True, data=obj, location=obj.href)  # type: ignore[attr-defined]

            except Exception as e:
                _log.error(f"Failed to append to {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get_list(self, list_uri: str) -> list[T]:
        """Get the complete list of objects from the specified URI.

        This method retrieves all objects stored in a list at the given URI.
        It's useful for operations that need to process all items in a collection
        or when implementing pagination at a higher level.

        Args:
            list_uri: The URI of the list to retrieve (e.g., "/edev", "/programs")

        Returns:
            List[T]: A list containing all objects of type T stored at the URI.
                Returns an empty list if the URI doesn't exist or contains no items.

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(n) where n is the number of items in the list. For large lists,
            consider using pagination with get_resource_list() instead.

        Memory Usage:
            Loads the entire list into memory. For very large lists, this may
            cause memory pressure. Monitor usage for lists with thousands of items.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> devices = adapter.get_list("/edev")
            >>> print(f"Found {len(devices)} devices")
            >>> for device in devices:
            ...     print(f"Device: {device.href}")
        """
        list_key = self._get_list_key(list_uri)

        with self._read_lock():
            self._track_operation("get_list")

            try:
                list_data = self._db.get_point(list_key)
                if list_data is None:
                    return []

                import pickle

                return pickle.loads(list_data)
            except Exception as e:
                _log.error(f"Failed to get list {list_uri}: {e}")
                return []

    def get_list_size(self, list_uri: str) -> int:
        """Get the size of a list efficiently without loading all items.

        This method retrieves the number of items in a list by checking the
        metadata rather than loading and counting all items. This is much more
        efficient for large lists.

        Args:
            list_uri: The URI of the list to check (e.g., "/edev", "/programs")

        Returns:
            int: The number of items in the list. Returns 0 if the list
                doesn't exist or is empty.

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(1) operation that only reads metadata, making it very efficient
            even for large lists.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> size = adapter.get_list_size("/edev")
            >>> print(f"EndDevice list contains {size} devices")
            >>>
            >>> # Much more efficient than len(adapter.get_list("/edev"))
            >>> # for large lists
        """
        with self._read_lock():
            self._track_operation("get_list_size")

            metadata = self._get_list_metadata(list_uri)
            return metadata.get("count", 0)

    # For backward compatibility
    def list_size(self, list_uri: str) -> int:
        """Alias for get_list_size for backward compatibility."""
        return self.get_list_size(list_uri)

    def set_list(self, list_uri: str, items: list[T]) -> AdapterResult:
        """Replace the entire list with new items atomically.

        This method replaces all items in a list with a new set of items in a
        single atomic operation. This is useful for bulk updates or when you
        need to ensure the list contains exactly the specified items.

        Args:
            list_uri: The URI of the list to replace (e.g., "/edev", "/programs")
            items: The new list of items to store. All items must be of type T.

        Returns:
            AdapterResult: Result of the operation containing:
                - success: True if the list was successfully replaced
                - data: The new list items if successful
                - error: Error message if the operation failed

        Thread Safety:
            This method is thread-safe and uses resource-specific locking to
            ensure atomic replacement of the entire list.

        Performance:
            O(n) where n is the number of items in the new list. The operation
            is atomic, so other threads will see either the old list or the
            new list, never a partial state.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> new_devices = [device1, device2, device3]
            >>> result = adapter.set_list("/edev", new_devices)
            >>> if result.success:
            ...     print(f"Replaced list with {len(new_devices)} devices")
            >>> else:
            ...     print(f"Failed to replace list: {result.error}")

        Note:
            This operation completely replaces the list contents. Any existing
            items not in the new list will be lost.
        """
        list_key = self._get_list_key(list_uri)

        with self._resource_lock(list_uri):
            self._track_operation("set_list")

            try:
                with atomic_operation():
                    import pickle

                    # Store the updated list
                    self._db.set_point(list_key, pickle.dumps(items))

                    # Update metadata
                    metadata = self._get_list_metadata(list_uri)
                    metadata["count"] = len(items)
                    metadata["last_modified"] = time.time()
                    self._db.set_point(self._get_metadata_key(list_uri), pickle.dumps(metadata))

                _log.debug(f"Set list {list_uri} with {len(items)} items")
                return AdapterResult(success=True, data=items)

            except Exception as e:
                _log.error(f"Failed to set list {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get(self, list_uri: str, index: int) -> T | None:
        """Get an object from a list by its index.

        This method retrieves a specific object from a list using its zero-based
        index position. It provides thread-safe access to list items without
        requiring retrieval of the entire list.

        Args:
            list_uri: The URI of the list to retrieve from (e.g., "/edev", "/programs")
            index: Zero-based index of the item to retrieve

        Returns:
            T | None: The object at the specified index, or None if:
                - The index is out of bounds
                - The list does not exist
                - An error occurred during retrieval

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(n) where n is the list size, as it needs to deserialize the entire
            list to access a single element. For frequent random access, consider
            using direct object storage with href-based keys.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> device = adapter.get("/edev", 0)  # Get first device
            >>> if device:
            ...     print(f"Device href: {device.href}")
            >>> else:
            ...     print("Device not found or index out of bounds")
        """
        with self._read_lock():
            self._track_operation("get")

            try:
                current_list = self.get_list(list_uri)
                if 0 <= index < len(current_list):
                    return current_list[index]
                return None
            except Exception as e:
                _log.error(f"Failed to get item {index} from {list_uri}: {e}")
                return None

    def put(self, list_uri: str, index: int, obj: T) -> AdapterResult:
        """Update an object at a specific index in a list.

        This method replaces the object at the specified index with a new object.
        The operation is atomic and thread-safe. If the index is out of bounds,
        the operation will fail.

        Args:
            list_uri: The URI of the list to modify (e.g., "/edev", "/programs")
            index: Zero-based index of the item to replace
            obj: The new object to store at the specified index

        Returns:
            AdapterResult: Result of the operation containing:
                - success: True if the object was successfully updated
                - data: The updated object if successful
                - was_update: Always True for successful put operations
                - error: Error message if the operation failed (e.g., index out of bounds)

        Thread Safety:
            This method is thread-safe and uses resource-specific locking to
            prevent concurrent modifications to the same list.

        Performance:
            O(n) where n is the list size, due to list serialization and
            deserialization. For better performance with frequent updates,
            consider using direct object storage patterns.

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> updated_device = EndDevice(href="/edev/0", updated_field="new_value")
            >>> result = adapter.put("/edev", 0, updated_device)
            >>> if result.success:
            ...     print("Device updated successfully")
            >>> else:
            ...     print(f"Update failed: {result.error}")
        """
        with self._resource_lock(list_uri):
            self._track_operation("put")

            try:
                with atomic_operation():
                    import pickle

                    list_data = self._db.get_point(self._get_list_key(list_uri))
                    if list_data is None:
                        return AdapterResult(success=False, error="List not found")

                    current_list = pickle.loads(list_data)
                    if not (0 <= index < len(current_list)):
                        return AdapterResult(success=False, error="Index out of range")

                    # Update object
                    current_list[index] = obj

                    # Store updated list
                    self._db.set_point(self._get_list_key(list_uri), pickle.dumps(current_list))

                _log.debug(f"Updated object at index {index} in {list_uri}")
                return AdapterResult(success=True, data=obj, was_update=True)

            except Exception as e:
                _log.error(f"Failed to put item {index} in {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def set_single(self, uri: str, obj: Any, lfdi: str | None = None) -> AdapterResult:
        """Store a single object at a URI (not part of a list).

        This method stores an individual object directly at a URI, independent
        of any list structure. This is useful for singleton resources, configuration
        objects, or other resources that don't belong to collections.

        Args:
            uri: The URI where the object should be stored (e.g., "/config", "/status")
            obj: The object to store. Can be any serializable object.
            lfdi: Optional LFDI (Long Form Device Identifier) to associate with the object.

        Returns:
            AdapterResult: Result of the operation containing:
                - success: True if the object was successfully stored
                - data: The stored object if successful
                - location: The URI where the object was stored
                - error: Error message if the operation failed

        Thread Safety:
            This method is thread-safe and uses write locks for exclusive access
            during the storage operation.

        Performance:
            O(1) operation for storing the object directly at the specified URI.

        Storage Model:
            Single objects are stored directly using the URI as the storage key,
            without any list metadata or indexing overhead.

        Example:
            >>> adapter = ThreadSafeListAdapter(Any)
            >>> config = {"server_name": "ieee2030_5", "port": 8443}
            >>> result = adapter.set_single("/config", config)
            >>> if result.success:
            ...     print(f"Config stored at {result.location}")
            >>>
            >>> # For device-specific settings
            >>> device_settings = DeviceSettings(polling_rate=30)
            >>> adapter.set_single("/edev/123/settings", device_settings)
        """
        with self._write_lock():
            self._track_operation("set_single")

            try:
                # print(f"!!!! STORAGE DEBUG: Starting set_single for URI: {uri}, LFDI: {lfdi}")
                _log.info(f"STORAGE_DEBUG: Starting set_single for URI: {uri}, LFDI: {lfdi}")
                with atomic_operation():
                    import pickle

                    # Store the single object directly
                    obj_key = f"single:{uri}"
                    # print(f"!!!! STORAGE DEBUG: Storing object with key: {obj_key}")
                    _log.info(f"STORAGE_DEBUG: Storing object with key: {obj_key}")
                    # Force synchronous write for critical single objects
                    # Check if the database backend supports synchronous writes
                    if hasattr(self._db, "set_point") and "synchronous" in self._db.set_point.__code__.co_varnames:
                        # SQLite backend - force synchronous write
                        self._db.set_point(obj_key, pickle.dumps(obj), synchronous=True)
                    else:
                        # Other backends
                        self._db.set_point(obj_key, pickle.dumps(obj))
                    # print(f"!!!! STORAGE DEBUG: Object stored successfully")
                    _log.info("STORAGE_DEBUG: Object stored successfully")

                    # Store metadata if LFDI is provided
                    if lfdi is not None:
                        metadata = {
                            "uri": uri,
                            "created": time.time(),
                            "type": obj.__class__.__name__ if obj else None,
                            "lfdi": lfdi,
                        }
                        metadata_key = f"single_meta:{uri}"
                        # print(f"!!!! STORAGE DEBUG: Storing metadata with key: {metadata_key}")
                        _log.info(f"STORAGE_DEBUG: Storing metadata with key: {metadata_key}")
                        self._db.set_point(metadata_key, pickle.dumps(metadata))
                        # print(f"!!!! STORAGE DEBUG: Metadata stored successfully")
                        _log.info("STORAGE_DEBUG: Metadata stored successfully")

                    # Ensure object has the correct href
                    if hasattr(obj, "href"):
                        obj.href = uri

                    # Register mRID automatically if the object has one
                    if hasattr(obj, "mRID") and obj.mRID is not None and hasattr(obj, "href"):
                        try:
                            global _GlobalMRIDs
                            if _GlobalMRIDs is not None:
                                obj_type = type(obj).__name__
                                # Use the actual database key (with single: prefix)
                                _GlobalMRIDs.register_mrid(obj.mRID, obj_key, obj_type)
                                _log.debug(f"Registered mRID {obj.mRID} -> {obj_type}:{obj_key}")
                        except Exception as e:
                            _log.debug(f"mRID registration failed: {e}")

                # Verify storage immediately after commit
                # print(f"!!!! STORAGE DEBUG: Verifying storage for key: {obj_key}")
                _log.info(f"STORAGE_DEBUG: Verifying storage for key: {obj_key}")
                try:
                    stored_data = self._db.get_point(obj_key)
                    if stored_data:
                        # print(f"!!!! STORAGE DEBUG: Verification successful - data found in database")
                        _log.info("STORAGE_DEBUG: Verification successful - data found in database")
                    else:
                        # print(f"!!!! STORAGE DEBUG: Verification FAILED - no data found in database!")
                        _log.error("STORAGE_DEBUG: Verification FAILED - no data found in database!")
                except Exception as e:
                    # print(f"!!!! STORAGE DEBUG: Verification error: {e}")
                    _log.error(f"STORAGE_DEBUG: Verification error: {e}")

                _log.debug(f"Set single object at {uri}")
                return AdapterResult(success=True, data=obj, location=uri)

            except Exception as e:
                _log.error(f"Failed to set single object at {uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get_single(self, uri: str) -> Any:
        """Retrieve a single object stored at a URI.

        This method retrieves an individual object that was stored directly at
        a URI using set_single(). It's the counterpart to set_single() for
        accessing singleton resources and non-list objects.

        Args:
            uri: The URI where the object is stored (e.g., "/config", "/status")

        Returns:
            Any: The object stored at the URI, or None if:
                - No object exists at the specified URI
                - An error occurred during retrieval

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(1) operation for direct URI-based object retrieval.

        Example:
            >>> adapter = ThreadSafeListAdapter(Any)
            >>>
            >>> # Retrieve configuration object
            >>> config = adapter.get_single("/config")
            >>> if config:
            ...     print(f"Server port: {config['port']}")
            >>>
            >>> # Retrieve device-specific settings
            >>> settings = adapter.get_single("/edev/123/settings")
            >>> if settings:
            ...     print(f"Polling rate: {settings.polling_rate}")
        """
        with self._read_lock():
            self._track_operation("get_single")

            try:
                import pickle

                obj_key = f"single:{uri}"
                obj_data = self._db.get_point(obj_key)

                if obj_data is None:
                    return None

                return pickle.loads(obj_data)

            except Exception as e:
                _log.error(f"Failed to get single object from {uri}: {e}")
                return None

    def delete_single(self, uri: str) -> bool:
        """Delete a single object stored at a URI.

        This method removes an individual object that was stored directly at
        a URI using set_single(). It permanently removes the object from storage.

        Args:
            uri: The URI of the object to delete (e.g., "/config", "/status")

        Returns:
            bool: True if the object was successfully deleted or didn't exist,
                False if an error occurred during deletion.

        Thread Safety:
            This method is thread-safe and uses write locks for exclusive access
            during the deletion operation.

        Performance:
            O(1) operation for direct URI-based object deletion.

        Idempotent Operation:
            This method is idempotent - calling it multiple times with the same
            URI will not cause errors, even if the object doesn't exist.

        Example:
            >>> adapter = ThreadSafeListAdapter(Any)
            >>>
            >>> # Delete configuration object
            >>> success = adapter.delete_single("/config")
            >>> if success:
            ...     print("Configuration deleted")
            >>>
            >>> # Delete device-specific settings
            >>> adapter.delete_single("/edev/123/settings")
            >>>
            >>> # Safe to call even if object doesn't exist
            >>> adapter.delete_single("/nonexistent")  # Returns True
        """
        with self._write_lock():
            self._track_operation("delete_single")

            try:
                obj_key = f"single:{uri}"
                return self._db.delete_point(obj_key)

            except Exception as e:
                _log.error(f"Failed to delete single object from {uri}: {e}")
                return False

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> T | None:
        """Fetch an object by property from lists and single objects.

        This implementation searches through all lists and single objects
        for the given property value.

        Args:
            prop_name: The name of the property to search by
            prop_value: The value to search for

        Returns:
            The first matching object if found, otherwise None
        """
        with self._read_lock():
            self._track_operation("fetch_by_property")

            try:
                import pickle

                # First check single objects that might match
                pattern = "single:*"
                for key in self._db.get_keys_matching(pattern):
                    try:
                        obj_data = self._db.get_point(key)
                        if obj_data:
                            obj = pickle.loads(obj_data)
                            if hasattr(obj, prop_name) and getattr(obj, prop_name) == prop_value:
                                return obj
                    except Exception as e:
                        _log.warning(f"Error loading object from {key}: {e}")

                # Then check all lists
                pattern = "list:*"
                for key in self._db.get_keys_matching(pattern):
                    try:
                        list_data = self._db.get_point(key)
                        if list_data:
                            items = pickle.loads(list_data)

                            for item in items:
                                if hasattr(item, prop_name) and getattr(item, prop_name) == prop_value:
                                    return item
                    except Exception as e:
                        _log.warning(f"Error searching list {key}: {e}")

                return None

            except Exception as e:
                _log.error(f"Failed to fetch by property {prop_name}={prop_value}: {e}")
                return None

    def get_resource_list(
        self,
        list_uri: str,
        start: int = 0,
        after: int = 0,
        limit: int = 0,
        sort_by: str | None = None,
        reverse: bool = False,
    ) -> Any:
        """Get a paginated resource list with sorting and filtering capabilities.

        This method provides advanced list retrieval with pagination, sorting,
        and filtering capabilities. It's designed to support IEEE 2030.5 list
        resource requirements including proper pagination metadata.

        Args:
            list_uri: The URI of the list to retrieve (e.g., "/edev", "/programs")
            start: Zero-based starting index for pagination (default: 0)
            after: Alternative pagination parameter, items after this index (default: 0)
            limit: Maximum number of items to return. 0 or unspecified defaults to 10 (default: 0)
            sort_by: Name of the attribute to sort by (e.g., "href", "lFDI")
            reverse: If True, sort in descending order (default: False)

        Returns:
            Any: A list-like object containing the requested items with pagination
                metadata. The exact type depends on the list type but typically
                includes fields like 'all', 'results', and the item collection.

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(n log n) if sorting is requested, O(n) otherwise, where n is the
            total list size. For large lists with frequent pagination, consider
            implementing server-side pagination.

        Pagination:
            Supports both 'start' and 'after' style pagination:
            - start: Returns items starting from the specified index
            - after: Returns items after the specified index
            - limit: Caps the number of returned items

        Example:
            >>> adapter = ThreadSafeListAdapter(EndDevice)
            >>> # Get first 10 devices
            >>> page1 = adapter.get_resource_list("/edev", start=0, limit=10)
            >>>
            >>> # Get next 10 devices sorted by href
            >>> page2 = adapter.get_resource_list("/edev", start=10, limit=10,
            ...                                   sort_by="href")
            >>>
            >>> # Get devices in reverse order
            >>> recent = adapter.get_resource_list("/edev", limit=5,
            ...                                    sort_by="href", reverse=True)
        """
        with self._read_lock():
            self._track_operation("get_resource_list")

            try:
                current_list = self.get_list(list_uri)
                total_count = len(current_list)

                # Apply sorting if requested
                if sort_by and current_list:
                    try:
                        current_list = sorted(current_list, key=lambda x: getattr(x, sort_by, 0), reverse=reverse)
                    except Exception as e:
                        _log.warning(f"Failed to sort by {sort_by}: {e}")

                # Apply pagination
                if after > 0:
                    start = after + 1

                # Default limit is 10 items if not specified (IEEE 2030.5 best practice)
                # This prevents returning massive lists by default
                if limit <= 0:
                    limit = 10

                end_index = start + limit
                page_items = current_list[start:end_index]

                # Create appropriate list type based on metadata
                metadata = self._get_list_metadata(list_uri)
                model_type_name = metadata.get("type", self.model_class.__name__)
                list_class_name = f"{model_type_name}List"
                list_class = getattr(m, list_class_name, None)

                if list_class:
                    result = list_class()
                    result.href = list_uri
                    result.all = total_count
                    result.results = len(page_items)

                    # Set pollRate if the list class has this attribute
                    if hasattr(result, "pollRate"):
                        # Determine the resource type from the list class name
                        from ieee_2030_5.adapters import get_poll_rate

                        # Map list class names to resource types
                        resource_type_map = {
                            "EndDeviceList": "end_device_list",
                            "DERList": "der_list",
                            "DERProgramList": "der_program_list",
                            "DERControlList": "der_control_list",
                            "FunctionSetAssignmentsList": "fsa_list",
                            "MirrorUsagePointList": "mirror_usage_point",
                            "UsagePointList": "usage_point",
                            "LogEventList": "log_event_list",
                            "MeterReadingList": "meter_reading",
                            "ReadingSetList": "reading_set",
                        }

                        resource_type = resource_type_map.get(list_class_name, "default")
                        result.pollRate = get_poll_rate(resource_type)

                    # Set the list items using the metadata type name
                    list_attr = model_type_name
                    setattr(result, list_attr, page_items)

                    return result
                else:
                    # Fallback for unknown list types
                    return {"href": list_uri, "all": total_count, "results": len(page_items), "items": page_items}

            except Exception as e:
                _log.error(f"Failed to get resource list {list_uri}: {e}")
                return None

    def filter_single_dict(self, filter_func: Callable[[str], bool]) -> list[str]:
        """
        Filter single objects based on a filter function applied to their keys.

        Args:
            filter_func: A function that takes a key string and returns a boolean

        Returns:
            List of URIs that match the filter criteria
        """
        with self._read_lock():
            self._track_operation("filter_single_dict")

            try:
                matching_uris = []

                # Find all single object keys
                pattern = "single:*"
                all_keys = self._db.get_keys_matching(pattern)

                for key in all_keys:
                    # Extract the URI part from the key (remove "single:" prefix)
                    uri = key[7:]  # 7 is the length of "single:"

                    # Apply the filter function
                    try:
                        if filter_func(uri):
                            matching_uris.append(uri)
                    except Exception as filter_e:
                        _log.error(f"Filter function failed for URI '{uri}': {filter_e}")

                return matching_uris

            except Exception as e:
                _log.error(f"Failed to filter single dict: {e}", exc_info=True)
                return []

    def get_single_meta_data(self, uri: str) -> dict[str, Any]:
        """
        Get metadata for a single object.

        Args:
            uri: The URI of the object

        Returns:
            Dictionary containing metadata about the object
        """
        with self._read_lock():
            self._track_operation("get_single_meta_data")

            try:
                # First try to get stored metadata
                metadata_key = f"single_meta:{uri}"
                try:
                    metadata_data = self._db.get_point(metadata_key)
                    if metadata_data is not None:
                        import pickle

                        return pickle.loads(metadata_data)
                except Exception:
                    pass  # Fall back to generating metadata from object

                # Basic metadata to return (fallback)
                metadata = {"uri": uri, "created": time.time(), "type": None, "lfdi": None}

                # Get the object to extract more metadata
                obj = self.get_single(uri)
                if obj:
                    # Try to determine type
                    metadata["type"] = obj.__class__.__name__

                    # Try to extract LFDI if available
                    if hasattr(obj, "lfdi"):
                        metadata["lfdi"] = obj.lfdi
                    elif hasattr(obj, "lFDI"):
                        metadata["lfdi"] = obj.lFDI

                    # Try to get creation time if available
                    if hasattr(obj, "createdDateTime"):
                        metadata["created"] = obj.createdDateTime

                return metadata

            except Exception as e:
                _log.error(f"Failed to get single metadata for URI {uri}: {e}")
                return {"uri": uri, "error": str(e)}

    def _get_list_metadata(self, list_uri: str) -> dict[str, Any]:
        """Get metadata for a list."""
        try:
            metadata_data = self._db.get_point(self._get_metadata_key(list_uri))
            if metadata_data:
                import pickle

                return pickle.loads(metadata_data)
        except Exception as e:
            _log.warning(f"Failed to get metadata for {list_uri}: {e}")

        return {"count": 0, "created": time.time()}

    def get_all_keys(self) -> list[str]:
        """Get all keys stored in the adapter for debugging and administrative purposes.

        This method returns all storage keys managed by this adapter, including
        both list keys and single object keys. It's primarily used for debugging,
        administrative operations, and system introspection.

        Returns:
            List[str]: A list of all storage keys. Keys are returned in sorted order
                for consistency. The list includes:
                - List keys (prefixed with "list:")
                - Single object keys (prefixed with "single:")
                - Metadata keys (prefixed with "list_meta:" and "single_meta:")

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(n log n) where n is the total number of keys, due to sorting.
            For large datasets, this may be expensive.

        Example:
            >>> adapter = ThreadSafeListAdapter(MyModel)
            >>> keys = adapter.get_all_keys()
            >>> for key in keys:
            ...     print(f"Key: {key}")

        Note:
            This method returns internal storage keys, not application-level URIs.
            Use print_all() for human-readable resource listings.
        """
        with self._read_lock():
            self._track_operation("get_all_keys")

            try:
                all_keys = []

                # Get list keys
                list_pattern = "list:*"
                all_keys.extend(self._db.get_keys_matching(list_pattern))

                # Get single object keys
                single_pattern = "single:*"
                all_keys.extend(self._db.get_keys_matching(single_pattern))

                # Get metadata keys
                list_meta_pattern = "list_meta:*"
                all_keys.extend(self._db.get_keys_matching(list_meta_pattern))

                single_meta_pattern = "single_meta:*"
                all_keys.extend(self._db.get_keys_matching(single_meta_pattern))

                return sorted(all_keys)

            except Exception as e:
                _log.error(f"Failed to get all keys: {e}")
                return []

    def print_all(self) -> None:
        """Print all resources stored in the adapter for debugging purposes.

        This method provides a comprehensive overview of all stored resources,
        including both lists and single objects. It's primarily intended for
        debugging and development purposes.

        Thread Safety:
            - Uses read lock to prevent modifications during listing
            - Safe to call from multiple threads simultaneously

        Performance:
            - O(n log n) due to sorting of keys
            - May be slow for large datasets due to deserialization

        Output Format:
            - List resources: Shows count and individual item hrefs
            - Single resources: Shows object href
            - Errors are logged as warnings for robustness

        Example Usage:
            ```python
            # Debug adapter contents
            adapter.print_all()

            # Typical output in logs:
            # --- Resource Listing ---
            # list:derlc: 5 items
            #   [0] /derlc/1
            #   [1] /derlc/2
            # single:dcap: /dcap
            # --- End Resource Listing ---
            ```

        Note:
            Output is written to the logger, not stdout. Check log files
            or configure logging to see the output.
        """
        with self._read_lock():
            self._track_operation("print_all")

            try:
                import pickle

                _log.info("--- Resource Listing ---")

                # Print lists
                pattern = "list:*"
                for key in sorted(self._db.get_keys_matching(pattern)):
                    try:
                        list_data = self._db.get_point(key)
                        if list_data:
                            items = pickle.loads(list_data)
                            _log.info(f"{key}: {len(items)} items")
                            for i, item in enumerate(items):
                                href = getattr(item, "href", None)
                                _log.info(f"  [{i}] {href}")
                    except Exception as e:
                        _log.warning(f"Error listing {key}: {e}")

                # Print single objects
                pattern = "single:*"
                for key in sorted(self._db.get_keys_matching(pattern)):
                    try:
                        obj_data = self._db.get_point(key)
                        if obj_data:
                            obj = pickle.loads(obj_data)
                            href = getattr(obj, "href", None)
                            _log.info(f"{key}: {href}")
                    except Exception as e:
                        _log.warning(f"Error listing {key}: {e}")

                _log.info("--- End Resource Listing ---")

            except Exception as e:
                _log.error(f"Failed to print all resources: {e}")


class ThreadSafeEndDeviceAdapter(ThreadSafeAdapter[m.EndDevice]):
    """Thread-safe adapter specialized for IEEE 2030.5 EndDevice objects.

    This adapter provides optimized storage and retrieval for EndDevice objects
    with specialized indexing based on lFDI (Long Form Device Identifier) and
    href values. It's designed to handle the specific requirements of IEEE 2030.5
    end device management including efficient lookups and device registration.

    Key Features:
        - Specialized lFDI-based indexing for fast device lookups
        - href-based indexing for REST API compatibility
        - Thread-safe device registration and updates
        - Automatic index maintenance during device operations
        - Support for device property-based searches

    Indexing Strategy:
        The adapter maintains two specialized indexes:
        - lFDI index: Maps device lFDI bytes to storage indices
        - href index: Maps device href strings to storage indices

        These indexes enable O(1) lookups by the most commonly used device
        identifiers in IEEE 2030.5 protocols.

    Storage Model:
        Devices are stored using a key pattern "enddevice:{index}" where index
        is an auto-incrementing integer. The indexes map device identifiers
        to these storage indices.

    Thread Safety:
        All operations are thread-safe using reader-writer locks optimized
        for read-heavy workloads typical in device management scenarios.

    Example:
        >>> adapter = ThreadSafeEndDeviceAdapter()
        >>>
        >>> # Register a new device
        >>> device = EndDevice(lFDI=b"device123", href="/edev/0")
        >>> result = adapter.add(device)
        >>>
        >>> # Look up by lFDI
        >>> found_device = adapter.fetch_by_lfdi(b"device123")
        >>>
        >>> # Look up by href
        >>> same_device = adapter.fetch_by_href("/edev/0")
    """

    def __init__(self):
        super().__init__(m.EndDevice, ConcurrencyMode.READ_WRITE_LOCK)
        self._lfdi_index_key = "index:enddevice:lfdi"
        self._href_index_key = "index:enddevice:href"
        self._lfdi_metadata_key = "index:enddevice:lfdi_metadata"

    def fetch_index(self, href: str) -> int | None:
        """Extract and return the device index from its href using optimized index lookup.

        This method provides an optimized version of index extraction that uses
        the specialized href index for O(1) lookups instead of string parsing.
        It falls back to the base implementation for compatibility.

        Args:
            href: The device href string (e.g., "/edev/123", "/enddevice/456").
                Should be a valid IEEE 2030.5 resource href.

        Returns:
            int | None: The numeric device index if found, None if:
                - The href is not found in the index
                - The href index is not initialized
                - An error occurred during lookup

        Thread Safety:
            This method is thread-safe and uses read locks for index access.

        Performance:
            - Primary path: O(1) using dedicated href index
            - Fallback path: O(1) string parsing via base implementation
            - Much faster than linear searches for large device collections

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>> index = adapter.fetch_index("/edev/123")  # Returns 123
            >>> if index is not None:
            ...     print(f"Device index: {index}")
            >>>
            >>> # Handle missing device
            >>> missing = adapter.fetch_index("/edev/999")  # Returns None
        """
        self._track_operation("fetch_index")
        try:
            import pickle

            # Get index from href index
            with self._read_lock():
                index_data = self._db.get_point(self._href_index_key)
                if index_data:
                    href_index = pickle.loads(index_data)
                    device_index = href_index.get(href)
                    if device_index is not None:
                        return device_index

            # Fall back to base implementation
            return super().fetch_index(href)
        except Exception as e:
            _log.error(f"Failed to fetch index for href {href}: {e}")
            return None

    def add(self, device: m.EndDevice, device_id: str = None) -> m.EndDevice:
        """Add a new EndDevice to the adapter with automatic indexing.

        This method registers a new EndDevice in the system, automatically
        assigning it a unique index and updating the specialized indexes for
        efficient lookups. The device's href will be generated if not provided.

        Args:
            device: The EndDevice object to add. The device should have at least
                an lFDI (Long Form Device Identifier) set. The href will be
                automatically generated if not provided.

        Returns:
            m.EndDevice: The added device with updated href and any other
                modifications made during the registration process.

        Thread Safety:
            This method is thread-safe and uses write locks for exclusive access
            during device registration.

        Automatic Indexing:
            The method automatically:
            - Assigns a unique numeric index to the device
            - Generates an href if not provided (/edev/{index})
            - Updates the lFDI index for O(1) lFDI-based lookups
            - Updates the href index for O(1) href-based lookups

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>> device = EndDevice(lFDI=b"device_certificate_hash")
            >>> registered_device = adapter.add(device)
            >>> print(f"Device registered at: {registered_device.href}")
            >>> # Device can now be found by lFDI or href
            >>> same_device = adapter.fetch_by_lfdi(b"device_certificate_hash")

        Raises:
            Exception: If the device cannot be stored or indexes cannot be updated.
        """
        with self._write_lock():
            self._track_operation("add")

            try:
                with atomic_operation():
                    import hashlib
                    import pickle

                    # Generate stable device index from device_id (mRID)
                    if device_id:
                        # Use hash of device_id to generate stable index
                        hash_obj = hashlib.sha256(device_id.encode("utf-8"))
                        device_index = int(hash_obj.hexdigest()[:8], 16) % 100000  # Limit to 5 digits
                    else:
                        # Device ID is required for stable indexing
                        raise ValueError(
                            "device_id is required for EndDevice registration. Cannot create stable device index without device_id."
                        )

                    # Set href if not present
                    if not device.href:
                        device.href = f"/edev{hrefs.SEP}{device_index}"

                    # Store device using stable index
                    device_key = f"enddevice:{device_index}"

                    # Check if device already exists at this index
                    if self._db.exists(device_key):
                        existing_data = self._db.get_point(device_key)
                        if existing_data:
                            _log.info(f"Device already exists at index {device_index}, updating: {device.href}")

                    self._db.set_point(device_key, pickle.dumps(device))

                    # Update indices
                    if device.lFDI is not None:
                        self._update_lfdi_index(device.lFDI, device_index, device, device_id)
                    if device.href is not None:
                        self._update_href_index(device.href, device_index)

                _log.info(f"Added end device {device.href}")
                return device

            except Exception as e:
                _log.error(f"Failed to add end device: {e}")
                raise

    def put(self, index: int, device: m.EndDevice) -> AdapterResult:
        """Update an existing EndDevice at a specific index.

        This method updates an EndDevice that is already registered in the system.
        It maintains the specialized indexes and ensures data consistency during
        the update operation.

        Args:
            index: The numeric index of the device to update
            device: The updated EndDevice object. Should contain the new state
                of the device including any modified fields.

        Returns:
            AdapterResult: Result of the update operation containing:
                - success: True if the device was successfully updated
                - data: The updated device if successful
                - was_update: Always True for successful put operations
                - error: Error message if the operation failed

        Thread Safety:
            This method is thread-safe and uses write locks for exclusive access
            during device updates.

        Index Maintenance:
            The method automatically updates the specialized indexes if the
            device's lFDI or href changed during the update. This ensures
            that lookups remain consistent.

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>> # Get existing device
            >>> device = adapter.fetch_by_href("/edev/5")
            >>> if device:
            ...     # Modify device
            ...     device.some_field = "new_value"
            ...     # Update in storage
            ...     result = adapter.put(5, device)
            ...     if result.success:
            ...         print("Device updated successfully")

        Note:
            The index must correspond to an existing device. Use add() for
            new devices.
        """
        with self._write_lock():
            self._track_operation("put")

            try:
                with atomic_operation():
                    import pickle

                    # Store device
                    device_key = f"enddevice:{index}"

                    # Check if device exists
                    if not self._db.exists(device_key):
                        return AdapterResult(success=False, error=f"End device with index {index} not found")

                    # Get existing device to preserve some data
                    existing_data = self._db.get_point(device_key)
                    if existing_data is None:
                        raise RuntimeError(f"Expected existing device at index {index} but found None")
                    existing_device = pickle.loads(existing_data)

                    # Update device
                    self._db.set_point(device_key, pickle.dumps(device))

                    # Update indices if needed
                    if existing_device.lFDI != device.lFDI and device.lFDI is not None:
                        self._update_lfdi_index(device.lFDI, index, device, device_id=None)

                    if existing_device.href != device.href and device.href is not None:
                        self._update_href_index(device.href, index)

                _log.info(f"Updated end device {device.href}")
                return AdapterResult(success=True, data=device, was_update=True)

            except Exception as e:
                _log.error(f"Failed to update end device: {e}")
                return AdapterResult(success=False, error=str(e))

    def fetch_all(
        self, list_obj: m.EndDeviceList | None = None, start: int = 0, after: int = 0, limit: int = 0
    ) -> m.EndDeviceList:
        """Fetch all EndDevice resources with pagination support.

        This method retrieves EndDevice objects from storage with comprehensive
        pagination support. It's optimized for large device collections and
        supports both offset-based and cursor-based pagination patterns.

        Args:
            list_obj: Optional pre-allocated EndDeviceList to populate. If None,
                a new EndDeviceList will be created and returned.
            start: Zero-based starting index for pagination (offset-based).
                Must be >= 0. Default is 0 (start from beginning).
            after: Alternative cursor-based pagination. When specified, starts
                from the device after this index. Takes precedence over start.
            limit: Maximum number of devices to return. If 0 or negative,
                returns all devices from the starting position.

        Returns:
            m.EndDeviceList: A populated EndDeviceList containing:
                - EndDevice: List of retrieved EndDevice objects
                - all: Total count of all devices in storage
                - results: Count of devices returned in this response

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.
            Multiple threads can safely call this method simultaneously.

        Performance:
            - O(k) where k is the number of devices retrieved
            - Index-based access provides efficient pagination
            - Handles large device collections efficiently

        Pagination Behavior:
            - `after` parameter enables cursor-based pagination
            - `start + limit` enables offset-based pagination
            - Returns empty list if no devices exist
            - Gracefully handles out-of-bounds requests

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>>
            >>> # Fetch first 10 devices
            >>> devices = adapter.fetch_all(start=0, limit=10)
            >>> print(f"Retrieved {devices.results} of {devices.all} devices")
            >>>
            >>> # Cursor-based pagination
            >>> next_page = adapter.fetch_all(after=9, limit=10)
            >>>
            >>> # Fetch all devices (use with caution for large datasets)
            >>> all_devices = adapter.fetch_all()
        """
        with self._read_lock():
            self._track_operation("fetch_all")

            try:
                import pickle

                # Get device count
                count_data = self._db.get_point("counter:enddevice")
                if not count_data:
                    # Return empty list
                    if list_obj is None:
                        list_obj = m.EndDeviceList()
                    list_obj.EndDevice = []
                    list_obj.all = 0
                    list_obj.results = 0
                    return list_obj

                device_count = pickle.loads(count_data)

                # Apply pagination
                if after > 0:
                    start = after + 1

                end = min(start + limit, device_count) if limit > 0 else device_count

                # Collect devices
                devices = []
                for i in range(start, end):
                    device_key = f"enddevice:{i}"
                    device_data = self._db.get_point(device_key)

                    if device_data:
                        device = pickle.loads(device_data)
                        devices.append(device)

                # Return as a list object
                if list_obj is None:
                    list_obj = m.EndDeviceList()

                list_obj.EndDevice = devices
                list_obj.all = device_count
                list_obj.results = len(devices)

                return list_obj

            except Exception as e:
                _log.error(f"Failed to fetch all devices: {e}")
                if list_obj is None:
                    list_obj = m.EndDeviceList(EndDevice=[], all=0, results=0)
                return list_obj

    def fetch_by_lfdi(self, lfdi: bytes) -> m.EndDevice | None:
        """Fetch an EndDevice by its Long Form Device Identifier (lFDI).

        This method provides efficient O(1) lookup of EndDevice objects using
        their lFDI, which is the primary identifier used in IEEE 2030.5 protocols
        for device authentication and identification.

        Args:
            lfdi: The Long Form Device Identifier as bytes. This is typically
                derived from the device's certificate or other cryptographic
                material and uniquely identifies the device.

        Returns:
            m.EndDevice | None: The EndDevice object if found, None if:
                - No device exists with the specified lFDI
                - The lFDI index is not initialized
                - An error occurred during retrieval

        Thread Safety:
            This method is thread-safe and uses read locks for concurrent access.

        Performance:
            O(1) average case lookup using a dedicated lFDI index. This is much
            faster than linear searches through device lists.

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>> device_lfdi = b"\\x01\\x02\\x03..."  # Device certificate-derived lFDI
            >>> device = adapter.fetch_by_lfdi(device_lfdi)
            >>> if device:
            ...     print(f"Found device: {device.href}")
            >>> else:
            ...     print("Device not registered")

        Note:
            The lFDI must match exactly (case-sensitive byte comparison).
            IEEE 2030.5 lFDIs are typically derived from certificate fingerprints.
        """
        with self._read_lock():
            self._track_operation("fetch_by_lfdi")

            try:
                import pickle

                # Get index
                index_data = self._db.get_point(self._lfdi_index_key)
                if not index_data:
                    return None

                lfdi_index = pickle.loads(index_data)
                device_index = lfdi_index.get(lfdi)

                # If not found, try alternative format for backward compatibility
                if device_index is None:
                    if isinstance(lfdi, bytes):
                        # Try string format
                        lfdi_str = lfdi.hex()
                        device_index = lfdi_index.get(lfdi_str)
                    else:
                        # Try bytes format
                        try:
                            lfdi_bytes = bytes.fromhex(str(lfdi))
                            device_index = lfdi_index.get(lfdi_bytes)
                        except ValueError:
                            lfdi_bytes = str(lfdi).encode("utf-8")
                            device_index = lfdi_index.get(lfdi_bytes)

                if device_index is None:
                    return None

                # Get device
                device_key = f"enddevice:{device_index}"
                device_data = self._db.get_point(device_key)

                if device_data:
                    return pickle.loads(device_data)

                return None

            except Exception as e:
                _log.error(f"Failed to fetch device by LFDI: {e}")
                return None

    def fetch_lfdi_metadata(self, lfdi: str | bytes) -> dict | None:
        """
        Fast lookup for LFDI metadata without loading the full device.

        Returns dictionary with:
        - device_index: int
        - mRID: str (if available)
        - href: str
        - device_uri: str (e.g. "/edev_10")

        This is much faster than fetch_by_lfdi() for cases where you only
        need basic device metadata for routing/mapping purposes.
        """
        with self._read_lock():
            self._track_operation("fetch_lfdi_metadata")

            try:
                import pickle

                # Normalize LFDI to string format for metadata index lookup
                lfdi_str = lfdi.hex() if isinstance(lfdi, bytes) else str(lfdi)

                # First check the enhanced metadata index
                metadata_data = self._db.get_point(self._lfdi_metadata_key)
                if metadata_data:
                    metadata_index = pickle.loads(metadata_data)
                    if lfdi_str in metadata_index:
                        return metadata_index[lfdi_str].copy()

                # Fallback to legacy index + device lookup for backward compatibility
                index_data = self._db.get_point(self._lfdi_index_key)
                if not index_data:
                    return None

                lfdi_index = pickle.loads(index_data)

                # Try both string and bytes formats for legacy compatibility
                lfdi_bytes = bytes.fromhex(lfdi_str) if isinstance(lfdi, str) else lfdi
                device_index = lfdi_index.get(lfdi_bytes) or lfdi_index.get(lfdi_str)

                if device_index is None:
                    return None

                # Get device for mRID extraction
                device_key = f"enddevice:{device_index}"
                device_data = self._db.get_point(device_key)

                if device_data:
                    device = pickle.loads(device_data)
                    return {
                        "device_index": device_index,
                        "mRID": device.mRID,
                        "href": device.href,
                        "device_uri": f"/edev{hrefs.SEP}{device_index}",
                    }

                return None

            except Exception as e:
                _log.error(f"Failed to fetch LFDI metadata: {e}")
                return None

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> m.EndDevice | None:
        """Fetch an EndDevice by any property with optimized lookups for common properties.

        This method provides efficient property-based lookups with specialized
        optimizations for frequently accessed properties like lFDI and href.
        It automatically routes to the most efficient lookup strategy based
        on the property being searched.

        Args:
            prop_name: The name of the property to search by. Common properties
                include "lFDI", "href", "enabled", "changedTime", etc.
            prop_value: The value to search for. Type should match the expected
                property type (e.g., bytes for lFDI, str for href).

        Returns:
            m.EndDevice | None: The first EndDevice found with the matching
            property value, or None if no match exists.

        Thread Safety:
            This method is thread-safe and uses appropriate locking for all
            lookup strategies including index-based and linear searches.

        Performance:
            - lFDI property: O(1) using dedicated lFDI index
            - href property: O(1) using dedicated href index
            - Other properties: O(n) linear search through all devices

        Optimization Notes:
            For frequently accessed properties other than lFDI/href, consider
            creating specialized methods or indexes to improve performance.

        Example:
            >>> adapter = ThreadSafeEndDeviceAdapter()
            >>>
            >>> # Optimized O(1) lookups
            >>> device = adapter.fetch_by_property("lFDI", device_lfdi_bytes)
            >>> device = adapter.fetch_by_property("href", "/edev/123")
            >>>
            >>> # Linear search for other properties
            >>> enabled_device = adapter.fetch_by_property("enabled", True)
            >>> recent_device = adapter.fetch_by_property("changedTime", timestamp)

        Warning:
            Linear searches can be slow for large device collections. Consider
            using specialized index-based methods when available.
        """
        if prop_name == "lFDI":
            return self.fetch_by_lfdi(prop_value)

        if prop_name == "href":
            # Use href index for efficient lookup
            with self._read_lock():
                self._track_operation("fetch_by_href")

                try:
                    import pickle

                    # Get index
                    index_data = self._db.get_point(self._href_index_key)
                    if not index_data:
                        return None

                    href_index = pickle.loads(index_data)
                    device_index = href_index.get(prop_value)

                    if device_index is None:
                        return None

                    # Get device
                    device_key = f"enddevice:{device_index}"
                    device_data = self._db.get_point(device_key)

                    if device_data:
                        return pickle.loads(device_data)

                    return None

                except Exception as e:
                    _log.error(f"Failed to fetch device by href: {e}")
                    return None

        # For other properties, we need to scan (could be optimized with more indices)
        with self._read_lock():
            self._track_operation("fetch_by_property")

            try:
                import pickle

                # Get device count
                count_data = self._db.get_point("counter:enddevice")
                if not count_data:
                    return None

                device_count = pickle.loads(count_data)

                # Scan devices
                for i in range(device_count):
                    device_key = f"enddevice:{i}"
                    device_data = self._db.get_point(device_key)

                    if device_data:
                        device = pickle.loads(device_data)
                        if hasattr(device, prop_name) and getattr(device, prop_name) == prop_value:
                            return device

                return None

            except Exception as e:
                _log.error(f"Failed to fetch device by {prop_name}: {e}")
                return None

    def _update_lfdi_index(
        self, lfdi: bytes | str, device_index: int, device: m.EndDevice = None, device_id: str = None
    ):
        """Update both legacy LFDI index and enhanced metadata index."""
        try:
            import pickle

            # Convert LFDI to both formats for comprehensive indexing
            if isinstance(lfdi, bytes):
                lfdi_bytes = lfdi
                lfdi_str = lfdi.hex()
            else:
                lfdi_str = str(lfdi)
                try:
                    lfdi_bytes = bytes.fromhex(lfdi_str)
                except ValueError:
                    lfdi_bytes = lfdi_str.encode("utf-8")

            # Update legacy index for backward compatibility - store both formats
            index_data = self._db.get_point(self._lfdi_index_key)
            lfdi_index = {} if index_data is None else pickle.loads(index_data)
            lfdi_index[lfdi_bytes] = device_index  # Store with bytes key
            lfdi_index[lfdi_str] = device_index  # Store with string key for compatibility
            self._db.set_point(self._lfdi_index_key, pickle.dumps(lfdi_index))

            # Update enhanced metadata index if device provided
            if device:
                metadata_data = self._db.get_point(self._lfdi_metadata_key)
                metadata_index = {} if metadata_data is None else pickle.loads(metadata_data)

                # Convert LFDI bytes to string for consistency with lookup methods
                lfdi_str = lfdi.hex() if isinstance(lfdi, bytes) else str(lfdi)

                metadata_index[lfdi_str] = {
                    "device_index": device_index,
                    "mRID": device_id,  # Use device_id as mRID (often the same in GridAPPS-D)
                    "href": device.href,
                    "device_uri": f"/edev{hrefs.SEP}{device_index}",
                }
                self._db.set_point(self._lfdi_metadata_key, pickle.dumps(metadata_index))

        except Exception as e:
            _log.error(f"Failed to update LFDI index: {e}")
            raise

    def _update_href_index(self, href: str, device_index: int):
        """Update the href index."""
        try:
            import pickle

            index_data = self._db.get_point(self._href_index_key)
            href_index = {} if index_data is None else pickle.loads(index_data)

            href_index[href] = device_index
            self._db.set_point(self._href_index_key, pickle.dumps(href_index))

        except Exception as e:
            _log.error(f"Failed to update href index: {e}")
            raise


# Global mRID management with thread safety
class ThreadSafeGlobalMRIDs:
    """Thread-safe global mRID management."""

    def __init__(self):
        self._lock = threading.RLock()
        self._db = get_db()
        self._mrid_prefix = "mrid:"  # Prefix for mRID keys in database

    def _normalize_mrid_to_string(self, mrid) -> str:
        """Normalize mRID to consistent string format for indexing."""
        if isinstance(mrid, bytes):
            # mRID is raw bytes (16 bytes), convert to hex string (32 chars)
            return mrid.hex()
        return str(mrid)

    def new_mrid(self) -> bytes:
        """Generate a new unique mRID using uuid_2030_5."""
        with self._lock:
            try:
                from ieee_2030_5.utils import uuid_2030_5

                # Generate unique mRID using uuid_2030_5
                while True:
                    # uuid_2030_5() returns hex string, convert to actual bytes
                    # This ensures we get 16 bytes instead of 32 ASCII characters
                    hex_string = uuid_2030_5().lower()
                    new_mrid = bytes.fromhex(hex_string)
                    # Check if it's already in use
                    if self.get_location(new_mrid) is None:
                        return new_mrid
            except Exception as e:
                _log.error(f"Failed to generate new mRID: {e}")
                raise

    def register_mrid(self, mrid: str, db_key: str, obj_type: str = None):
        """Register an mRID with its database storage key.

        Args:
            mrid: The mRID to register
            db_key: The database key where the object is stored
            obj_type: Optional type prefix for the stored value
        """
        normalized_mrid = None  # Initialize to avoid undefined variable in error handler
        with self._lock:
            try:
                # Normalize mRID to string for consistent indexing
                normalized_mrid = self._normalize_mrid_to_string(mrid)

                # Create value with type prefix if provided
                value = f"{obj_type}:{db_key}" if obj_type else f"db:{db_key}"

                # Store mRID as individual database key with prefixed value
                mrid_key = f"{self._mrid_prefix}{normalized_mrid}"

                # Ensure we're storing text data as UTF-8
                if isinstance(value, bytes):
                    _log.warning(f"register_mrid received bytes instead of string for {normalized_mrid}, converting")
                    value = value.decode("utf-8") if len(value) > 0 else ""

                # Check if there's already data at this key
                existing_data = self._db.get_point(mrid_key)
                if existing_data is not None:
                    try:
                        existing_value = existing_data.decode("utf-8")
                        if existing_value != value:
                            _log.warning(f"Overwriting mRID {normalized_mrid}: '{existing_value}' -> '{value}'")
                    except UnicodeDecodeError:
                        _log.error(
                            f"Found corrupted binary data for mRID {normalized_mrid}, replacing with correct text data"
                        )

                self._db.set_point(mrid_key, value.encode("utf-8"))
                _log.debug(f"Registered mRID {normalized_mrid} -> {value}")
            except Exception as e:
                # Use mrid if normalized_mrid failed to be set
                mrid_str = normalized_mrid if normalized_mrid else str(mrid)
                _log.error(f"Failed to register mRID {mrid_str}: {e}")
                raise

    def store_and_register(self, item: Any) -> bool:
        """Store an object in the database and register its mRID if present.

        This is the main method to use for storing objects with mRIDs.
        It handles both the database storage and mRID registration.

        Args:
            item: The object to store (must have 'href' and optionally 'mRID')

        Returns:
            True if successful, False otherwise
        """
        try:
            import pickle

            # Object must have an href to be stored
            if not hasattr(item, "href") or not item.href:
                _log.error(f"Cannot store object without href: {type(item).__name__}")
                return False

            # Store the object in the database at its href location
            self._db.set_point(item.href, pickle.dumps(item))
            _log.debug(f"Stored {type(item).__name__} at database key: {item.href}")

            # If it has an mRID, register it with type prefix
            if hasattr(item, "mRID") and item.mRID:
                obj_type = type(item).__name__
                self.register_mrid(item.mRID, item.href, obj_type)
                # Format mRID for logging (handle both bytes and strings)
                mrid_str = self._normalize_mrid_to_string(item.mRID)
                _log.debug(f"Registered mRID {mrid_str} -> {obj_type}:{item.href}")

            return True

        except Exception as e:
            _log.error(f"Failed to store and register object: {e}")
            return False

    def add_item_with_mrid(self, db_key: str, item: Any):
        """Legacy method - for backward compatibility.

        Args:
            db_key: The database key (usually same as href)
            item: The object with an mRID attribute
        """
        # For backward compatibility, store and register the item
        if hasattr(item, "href"):
            self.store_and_register(item)
        else:
            # If no href, just register the mRID
            if hasattr(item, "mRID") and item.mRID:
                self.register_mrid(item.mRID, db_key)

    def get_location(self, mrid: str) -> str | None:
        """Get the database storage key for an mRID.

        Args:
            mrid: The mRID to look up

        Returns:
            The database key where the object is stored, or None if not found
        """
        with self._lock:
            try:
                # Normalize mRID to string for consistent lookup
                normalized_mrid = self._normalize_mrid_to_string(mrid)
                mrid_key = f"{self._mrid_prefix}{normalized_mrid}"

                # Get the database key value
                db_key_bytes = self._db.get_point(mrid_key)
                if db_key_bytes is None:
                    return None

                # Decode and extract the actual database key from the prefixed value
                try:
                    value = db_key_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    # This might be pickled data stored incorrectly - skip it
                    _log.warning(f"Found binary data instead of text for mRID {normalized_mrid}, skipping")
                    return None

                # Value format is "type:db_key" or "db:db_key"
                if ":" in value:
                    _, db_key = value.split(":", 1)
                    return db_key
                else:
                    # Fallback for old format without prefix
                    return value

            except Exception as e:
                _log.error(f"Failed to get location for mRID {mrid}: {e}")
                return None

    def list_all_known_mrids(self) -> dict[str, str]:
        """List all mRIDs currently registered in the system.

        Returns:
            dict: Mapping of mRID -> database_location for all registered mRIDs
        """
        with self._lock:
            try:
                all_mrids = {}

                # Get all keys from database that start with our mRID prefix
                # This is database-specific, so we'll need to implement differently for each backend
                if hasattr(self._db, "get_all_keys_with_prefix"):
                    # If the database supports prefix queries
                    mrid_keys = self._db.get_all_keys_with_prefix(self._mrid_prefix)
                else:
                    # Fallback: try to get keys from internal storage if available
                    mrid_keys = []
                    if hasattr(self._db, "_storage") and hasattr(self._db._storage, "keys"):
                        all_keys = list(self._db._storage.keys())
                        mrid_keys = [k for k in all_keys if k.startswith(self._mrid_prefix)]

                for mrid_key in mrid_keys:
                    try:
                        # Extract mRID from key (remove prefix)
                        mrid = mrid_key[len(self._mrid_prefix) :]

                        # Get the location value
                        db_value = self._db.get_point(mrid_key)
                        if db_value:
                            try:
                                location = db_value.decode("utf-8")
                                all_mrids[mrid] = location
                            except UnicodeDecodeError:
                                all_mrids[mrid] = "<BINARY_DATA_ERROR>"
                    except Exception as e:
                        _log.debug(f"Error processing mRID key {mrid_key}: {e}")

                return all_mrids

            except Exception as e:
                _log.error(f"Failed to list mRIDs: {e}")
                return {}

    def get_item(self, mrid: str) -> Any:
        """Get an item by its mRID.

        Args:
            mrid: The mRID of the object to retrieve

        Returns:
            The object if found, None otherwise
        """
        with self._lock:
            try:
                import pickle

                # First get the database key for this mRID
                db_key = self.get_location(mrid)
                if db_key is None:
                    return None

                # Now retrieve the actual object from the database
                item_data = self._db.get_point(db_key)
                if item_data is None:
                    _log.warning(f"mRID {mrid} points to non-existent database key: {db_key}")
                    return None

                # Deserialize and return the object
                return pickle.loads(item_data)
            except Exception as e:
                _log.error(f"Failed to get item with mRID {mrid}: {e}")
                return None

    def list_mrids(self) -> list[str]:
        """List all registered mRIDs.

        Returns:
            List of all mRID strings
        """
        with self._lock:
            try:
                # Get all keys with mRID prefix
                all_keys = []
                # This would need a method to scan keys in the database
                # For now, return empty list - would need to implement db.scan_keys()
                _log.debug("list_mrids not fully implemented - needs database key scanning")
                return all_keys
            except Exception as e:
                _log.error(f"Failed to list mRIDs: {e}")
                return []

    def __len__(self) -> int:
        """Get the number of items in the registry."""
        # For now, we can't easily count all mRID keys without scanning
        # This would need database support for prefix scanning
        return 0  # TODO: Implement when database supports key prefix scanning

    def debug_registry_contents(self):
        """Debug method to list all entries in the global registry."""
        with self._lock:
            try:
                # This would need database support for prefix scanning
                _log.info("Debug registry contents not fully implemented - needs database key scanning")
                # For debugging, we could manually check a few known mRIDs if needed
            except Exception as e:
                _log.error(f"Failed to debug registry contents: {e}")

    def debug_mrid_lookup(self, mrid: str):
        """Debug method to show detailed mRID lookup information.

        Args:
            mrid: The mRID to debug
        """
        with self._lock:
            try:
                normalized_mrid = self._normalize_mrid_to_string(mrid)
                mrid_key = f"{self._mrid_prefix}{normalized_mrid}"

                _log.info(f"=== mRID Debug Info for '{mrid}' ===")
                _log.info(f"  Normalized mRID: '{normalized_mrid}'")
                _log.info(f"  Database key: '{mrid_key}'")

                # Check if mRID exists in database
                raw_value = self._db.get_point(mrid_key)
                if raw_value:
                    value = raw_value.decode("utf-8")
                    _log.info(f"  Raw database value: '{value}'")

                    # Parse the value
                    if ":" in value:
                        obj_type, db_location = value.split(":", 1)
                        _log.info(f"  Object type: '{obj_type}'")
                        _log.info(f"  Database location: '{db_location}'")

                        # Check if object exists at location
                        obj_data = self._db.get_point(db_location)
                        if obj_data:
                            _log.info(f"  Object found at location: {len(obj_data)} bytes")
                            try:
                                import pickle

                                obj = pickle.loads(obj_data)
                                _log.info(f"  Object type in storage: {type(obj).__name__}")
                                if hasattr(obj, "href"):
                                    _log.info(f"  Object href: {obj.href}")
                            except Exception as e:
                                _log.error(f"  Failed to deserialize object: {e}")
                        else:
                            _log.error(f"  ERROR: No object found at location '{db_location}'")
                    else:
                        _log.info(f"  Legacy format (no type prefix): '{value}'")
                else:
                    _log.error("  ERROR: mRID not found in database")

                _log.info("=== End mRID Debug Info ===")

            except Exception as e:
                _log.error(f"Failed to debug mRID lookup for '{mrid}': {e}")


# Global adapter instances with proper initialization
_adapters_lock = threading.Lock()
_initialized = False

# Global adapter instances
ListAdapter: ThreadSafeListAdapter | None = None
EndDeviceAdapter: ThreadSafeEndDeviceAdapter | None = None
_GlobalMRIDs: ThreadSafeGlobalMRIDs | None = None


def get_global_mrids_instance():
    """Get the global MRIDs instance, ensuring proper initialization."""
    ensure_adapters_initialized()
    return _GlobalMRIDs


def initialize_adapters():
    """Initialize all global adapter instances.

    This function creates and configures the global adapter instances that are
    used throughout the IEEE 2030.5 server. It ensures that adapters are
    initialized exactly once, even in multi-threaded environments.

    The function is idempotent - it can be called multiple times safely and
    will only perform initialization on the first call.

    Global Adapters Created:
        ListAdapter: Generic adapter for IEEE 2030.5 List resources
        EndDeviceAdapter: Specialized adapter for EndDevice resources with indexing
        GlobalMRIDs: Global mRID registry for cross-resource lookups

    Thread Safety:
        This function is thread-safe and uses a lock to ensure adapters are
        initialized exactly once even if called concurrently.

    Initialization:
        This function is automatically called when the module is imported,
        so manual calls are typically not necessary.

    Example:
        >>> # Usually not needed - called automatically on import
        >>> initialize_adapters()
        >>>
        >>> # Access global adapters
        >>> if EndDeviceAdapter is not None:
        ...     device = EndDeviceAdapter.fetch_by_href("/edev/123")
    """
    global ListAdapter, EndDeviceAdapter, _GlobalMRIDs, _initialized

    if _initialized:
        return

    with _adapters_lock:
        if _initialized:
            return

        _log.info("Initializing thread-safe adapters...")

        # Initialize adapters
        ListAdapter = ThreadSafeListAdapter(object)  # Generic list adapter
        EndDeviceAdapter = ThreadSafeEndDeviceAdapter()
        _GlobalMRIDs = ThreadSafeGlobalMRIDs()  # Global mRID registry

        # Add compatibility method to ListAdapter instance
        ListAdapter.list_size = lambda uri: ListAdapter.get_list_size(uri)

        _initialized = True
        _log.info("Thread-safe adapters initialized")

        # Update global adapter references in __init__.py
        try:
            from . import _update_global_adapters

            _update_global_adapters()
        except ImportError:
            pass  # Module might not have this function yet


def ensure_adapters_initialized():
    """Ensure adapters are initialized (lazy initialization)."""
    if not _initialized:
        initialize_adapters()


def get_adapter_stats() -> dict[str, Any]:
    """Get performance statistics from all adapters.

    This function collects and returns performance metrics from all global
    adapter instances. The statistics include operation counts, timing
    information, and other performance-related data useful for monitoring
    and debugging.

    Returns:
        Dict[str, Any]: Dictionary containing statistics for each adapter:
            - 'list_adapter': Statistics from the global ListAdapter
            - 'enddevice_adapter': Statistics from the global EndDeviceAdapter

        Each adapter statistics include:
            - operation_count: Count of operations by type
            - last_operation_time: Timestamp of last operation by type
            - Additional adapter-specific metrics

    Thread Safety:
        This function is thread-safe and can be called concurrently.

    Example:
        >>> stats = get_adapter_stats()
        >>> print(f"EndDevice operations: {stats['enddevice_adapter']['operation_count']}")
        >>> print(f"List operations: {stats['list_adapter']['operation_count']}")

    Note:
        Returns empty dict if adapters have not been initialized yet.
    """
    if not _initialized:
        return {}

    return {
        "list_adapter": ListAdapter.get_stats() if ListAdapter is not None else {},
        "enddevice_adapter": EndDeviceAdapter.get_stats() if EndDeviceAdapter is not None else {},
    }


# Don't initialize adapters on module import - wait for configuration
# initialize_adapters() will be called after point store is configured
