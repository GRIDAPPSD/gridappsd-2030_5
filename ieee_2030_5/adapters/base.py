# ieee_2030_5/adapters/base.py
"""
Thread-safe base adapter classes for IEEE 2030.5 server.
Provides concurrency control for all adapter operations.
"""
import logging
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Callable
from collections import defaultdict
import ieee_2030_5.models as m
from ieee_2030_5.persistance.points import get_db, atomic_operation
_log = logging.getLogger(__name__)
T = TypeVar('T')
@dataclass
class AdapterResult:
    """Result of an adapter operation with metadata."""
    success: bool
    data: Any = None
    error: str | None = None
    was_update: bool = False
    location: str | None = None
class ConcurrencyMode:
    """Concurrency control modes for adapters."""
    READ_WRITE_LOCK = "rw_lock"      # Reader-writer locks (best for read-heavy)
    MUTEX = "mutex"                   # Simple mutual exclusion
    OPTIMISTIC = "optimistic"         # Optimistic locking with retry
class ResourceLockManager:
    """Manages fine-grained locks for individual resources."""

    def __init__(self):
        self._locks: Dict[str, threading.RLock] = {}
        self._locks_lock = threading.Lock()

    def get_resource_lock(self, resource_id: str) -> threading.RLock:
        """Get or create a lock for a specific resource."""
        with self._locks_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = threading.RLock()
            return self._locks[resource_id]

    @contextmanager
    def lock_resource(self, resource_id: str):
        """Context manager for locking a specific resource."""
        lock = self.get_resource_lock(resource_id)
        acquired = lock.acquire(timeout=30)  # 30 second timeout
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for resource {resource_id}")
        try:
            yield
        finally:
            lock.release()
class ReadWriteLock:
    """Reader-writer lock implementation for read-heavy workloads."""

    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_ready = threading.Condition(threading.RLock())
        self._write_ready = threading.Condition(threading.RLock())

    @contextmanager
    def reader(self):
        """Acquire reader lock."""
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
        """Acquire writer lock."""
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
    """Base class for all thread-safe adapters."""

    _lock: ReadWriteLock | threading.RLock

    def __init__(self,
                 model_class: Type[T],
                 concurrency_mode: str = ConcurrencyMode.READ_WRITE_LOCK):
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

    def fetch_index(self, href: str) -> Optional[int]:
        """Extract and return the resource index from its href.
        This method is provided for backward compatibility with older code.

        Args:
            href: The resource href string

        Returns:
            The resource index if found, otherwise None
        """
        self._track_operation("fetch_index")
        try:
            # Try to extract index from href directly
            parts = href.split('/')
            if parts and parts[-1].isdigit():
                return int(parts[-1])

            # If that fails, try to look up the object and then extract its index
            obj = self.fetch_by_href(href)
            if obj and hasattr(obj, 'href'):
                parts = obj.href.split('/')
                if parts and parts[-1].isdigit():
                    return int(parts[-1])

            return None
        except Exception as e:
            _log.error(f"Failed to fetch index for href {href}: {e}")
            return None

    def fetch_by_href(self, href: str) -> Optional[T]:
        """Fetch an object by its href.

        This is a generic method that can be used by any adapter to find
        objects by their href. It will use an optimized index lookup if available,
        or fall back to property-based search.

        Args:
            href: The href to search for

        Returns:
            The object if found, otherwise None
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

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> Optional[T]:
        """Fetch an object by a specific property.

        This is a base implementation that should be overridden by subclasses
        with more efficient lookup mechanisms if available.

        Args:
            prop_name: The name of the property to search by
            prop_value: The value to search for

        Returns:
            The object if found, otherwise None
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

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter performance statistics."""
        return {
            'operation_counts': dict(self._operation_count),
            'last_operation_times': dict(self._last_operation_time),
            'concurrency_mode': self.concurrency_mode
        }


class ThreadSafeListAdapter(ThreadSafeAdapter[T]):
    """Thread-safe adapter for managing lists of IEEE 2030.5 objects."""

    def __init__(self, model_class: Type[T]):
        super().__init__(model_class, ConcurrencyMode.READ_WRITE_LOCK)
        self._db = get_db()

    def _get_list_key(self, list_uri: str) -> str:
        """Get storage key for a list."""
        return f"list:{list_uri}"

    def _get_metadata_key(self, list_uri: str) -> str:
        """Get storage key for list metadata."""
        return f"list_meta:{list_uri}"

    def initialize_uri(self, list_uri: str, obj_type: Type[T] | None = None, **kwargs) -> bool:
        """Initialize a new list URI.

        Args:
            list_uri: The URI to initialize
            obj_type: The object type for this list
            **kwargs: Additional arguments for backward compatibility
                - list_uri: Alternative way to specify the URI
                - obj: Alternative way to specify the object type

        Returns:
            bool: True if initialized, False if already existed
        """
        # Support for both positional and named arguments
        if obj_type is None:
            # Check for 'obj' parameter for backward compatibility
            obj_type = kwargs.get('obj')

        # If list_uri is provided as a named parameter, use it
        if 'list_uri' in kwargs and not list_uri:
            list_uri = kwargs.get('list_uri', '')

        if not list_uri or not obj_type:
            raise ValueError("Both list_uri and obj_type/obj must be provided")

        list_key = self._get_list_key(list_uri)

        with self._write_lock():
            self._track_operation("initialize_uri")

            if self._db.exists(list_key):
                return False    # Already exists

            try:
                with atomic_operation():
                    # Initialize empty list
                    import pickle
                    empty_list: list[T] = []
                    self._db.set_point(list_key, pickle.dumps(empty_list))

                    # Store metadata
                    metadata = {'type': obj_type.__name__, 'created': time.time(), 'count': 0}
                    self._db.set_point(self._get_metadata_key(list_uri), pickle.dumps(metadata))

                _log.debug(f"Initialized list URI: {list_uri}")
                return True
            except Exception as e:
                _log.error(f"Failed to initialize URI {list_uri}: {e}")
                raise

    def append(self, list_uri: str, obj: T) -> AdapterResult:
        """Append an object to a list."""
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
                    if not hasattr(obj, 'href') or not obj.href:
                        obj.href = f"{list_uri}/{len(current_list)}"  # type: ignore[attr-defined]

                    # Append object
                    current_list.append(obj)

                    # Store updated list
                    self._db.set_point(list_key, pickle.dumps(current_list))

                    # Update metadata
                    metadata = self._get_list_metadata(list_uri)
                    metadata['count'] = len(current_list)
                    metadata['last_modified'] = time.time()
                    self._db.set_point(self._get_metadata_key(list_uri),
                                     pickle.dumps(metadata))

                _log.debug(f"Appended object to {list_uri}, new count: {len(current_list)}")
                return AdapterResult(success=True, data=obj, location=obj.href)  # type: ignore[attr-defined]

            except Exception as e:
                _log.error(f"Failed to append to {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get_list(self, list_uri: str) -> List[T]:
        """Get the complete list."""
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
        """Get the size of a list efficiently."""
        with self._read_lock():
            self._track_operation("get_list_size")

            metadata = self._get_list_metadata(list_uri)
            return metadata.get('count', 0)

    # For backward compatibility
    def list_size(self, list_uri: str) -> int:
        """Alias for get_list_size for backward compatibility."""
        return self.get_list_size(list_uri)

    def set_list(self, list_uri: str, items: List[T]) -> AdapterResult:
        """Replace the entire list with new items."""
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
                    metadata['count'] = len(items)
                    metadata['last_modified'] = time.time()
                    self._db.set_point(self._get_metadata_key(list_uri),
                                     pickle.dumps(metadata))

                _log.debug(f"Set list {list_uri} with {len(items)} items")
                return AdapterResult(success=True, data=items)

            except Exception as e:
                _log.error(f"Failed to set list {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get(self, list_uri: str, index: int) -> Optional[T]:
        """Get an object by index."""
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
        """Update an object at a specific index."""
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
                    self._db.set_point(self._get_list_key(list_uri),
                                     pickle.dumps(current_list))

                _log.debug(f"Updated object at index {index} in {list_uri}")
                return AdapterResult(success=True, data=obj, was_update=True)

            except Exception as e:
                _log.error(f"Failed to put item {index} in {list_uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def set_single(self, uri: str, obj: Any) -> AdapterResult:
        """Store a single object at a URI (not part of a list)."""
        with self._write_lock():
            self._track_operation("set_single")

            try:
                with atomic_operation():
                    import pickle

                    # Store the single object directly
                    obj_key = f"single:{uri}"
                    self._db.set_point(obj_key, pickle.dumps(obj))

                    # Ensure object has the correct href
                    if hasattr(obj, 'href'):
                        obj.href = uri

                _log.debug(f"Set single object at {uri}")
                return AdapterResult(success=True, data=obj, location=uri)

            except Exception as e:
                _log.error(f"Failed to set single object at {uri}: {e}")
                return AdapterResult(success=False, error=str(e))

    def get_single(self, uri: str) -> Any:
        """Get a single object from a URI."""
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
        """Delete a single object from a URI."""
        with self._write_lock():
            self._track_operation("delete_single")

            try:
                obj_key = f"single:{uri}"
                return self._db.delete_point(obj_key)

            except Exception as e:
                _log.error(f"Failed to delete single object from {uri}: {e}")
                return False

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> Optional[T]:
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
                pattern = f"single:*"
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
                pattern = f"list:*"
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

    def get_resource_list(self,
                         list_uri: str,
                         start: int = 0,
                         after: int = 0,
                         limit: int = 0,
                         sort_by: str | None = None,
                         reverse: bool = False) -> Any:
        """Get a paginated resource list."""
        with self._read_lock():
            self._track_operation("get_resource_list")

            try:
                current_list = self.get_list(list_uri)
                total_count = len(current_list)

                # Apply sorting if requested
                if sort_by and current_list:
                    try:
                        current_list = sorted(current_list,
                                            key=lambda x: getattr(x, sort_by, 0),
                                            reverse=reverse)
                    except Exception as e:
                        _log.warning(f"Failed to sort by {sort_by}: {e}")

                # Apply pagination
                if after > 0:
                    start = after + 1

                if limit > 0:
                    end_index = start + limit
                    page_items = current_list[start:end_index]
                else:
                    page_items = current_list[start:]

                # Create appropriate list type based on model class
                list_class_name = f"{self.model_class.__name__}List"
                list_class = getattr(m, list_class_name, None)

                if list_class:
                    result = list_class()
                    result.href = list_uri
                    result.all = total_count
                    result.results = len(page_items)

                    # Set the list items
                    list_attr = self.model_class.__name__
                    setattr(result, list_attr, page_items)

                    return result
                else:
                    # Fallback for unknown list types
                    return {
                        'href': list_uri,
                        'all': total_count,
                        'results': len(page_items),
                        'items': page_items
                    }

            except Exception as e:
                _log.error(f"Failed to get resource list {list_uri}: {e}")
                return None


    def filter_single_dict(self, filter_func: Callable[[str], bool]) -> List[str]:
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
                import pickle
                matching_uris = []

                # Find all single object keys
                pattern = f"single:*"
                for key in self._db.get_keys_matching(pattern):
                    # Extract the URI part from the key (remove "single:" prefix)
                    uri = key[7:]    # 7 is the length of "single:"

                    # Apply the filter function
                    if filter_func(uri):
                        matching_uris.append(uri)

                return matching_uris

            except Exception as e:
                _log.error(f"Failed to filter single dict: {e}")
                return []

    def get_single_meta_data(self, uri: str) -> Dict[str, Any]:
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
                # Basic metadata to return
                metadata = {
                    'uri': uri,
                    'created': time.time(),
                    'type': None,
                    'lfdi': None
                }

                # Get the object to extract more metadata
                obj = self.get_single(uri)
                if obj:
                    # Try to determine type
                    metadata['type'] = obj.__class__.__name__

                    # Try to extract LFDI if available
                    if hasattr(obj, 'lfdi'):
                        metadata['lfdi'] = obj.lfdi
                    elif hasattr(obj, 'lFDI'):
                        metadata['lfdi'] = obj.lFDI

                    # Try to get creation time if available
                    if hasattr(obj, 'createdDateTime'):
                        metadata['created'] = obj.createdDateTime

                return metadata

            except Exception as e:
                _log.error(f"Failed to get single metadata for URI {uri}: {e}")
                return {'uri': uri, 'error': str(e)}

    def _get_list_metadata(self, list_uri: str) -> Dict[str, Any]:
        """Get metadata for a list."""
        try:
            metadata_data = self._db.get_point(self._get_metadata_key(list_uri))
            if metadata_data:
                import pickle
                return pickle.loads(metadata_data)
        except Exception as e:
            _log.warning(f"Failed to get metadata for {list_uri}: {e}")

        return {'count': 0, 'created': time.time()}

    def print_all(self):
        """Print all resources for debugging purposes."""
        with self._read_lock():
            self._track_operation("print_all")

            try:
                import pickle
                _log.info("--- Resource Listing ---")

                # Print lists
                pattern = f"list:*"
                for key in sorted(self._db.get_keys_matching(pattern)):
                    try:
                        list_data = self._db.get_point(key)
                        if list_data:
                            items = pickle.loads(list_data)
                            _log.info(f"{key}: {len(items)} items")
                            for i, item in enumerate(items):
                                href = getattr(item, 'href', None)
                                _log.info(f"  [{i}] {href}")
                    except Exception as e:
                        _log.warning(f"Error listing {key}: {e}")

                # Print single objects
                pattern = f"single:*"
                for key in sorted(self._db.get_keys_matching(pattern)):
                    try:
                        obj_data = self._db.get_point(key)
                        if obj_data:
                            obj = pickle.loads(obj_data)
                            href = getattr(obj, 'href', None)
                            _log.info(f"{key}: {href}")
                    except Exception as e:
                        _log.warning(f"Error listing {key}: {e}")

                _log.info("--- End Resource Listing ---")

            except Exception as e:
                _log.error(f"Failed to print all resources: {e}")
class ThreadSafeEndDeviceAdapter(ThreadSafeAdapter[m.EndDevice]):
    """Thread-safe adapter for EndDevice objects."""

    def __init__(self):
        super().__init__(m.EndDevice, ConcurrencyMode.READ_WRITE_LOCK)
        self._lfdi_index_key = "index:enddevice:lfdi"
        self._href_index_key = "index:enddevice:href"

    def fetch_index(self, href: str) -> Optional[int]:
        """Extract and return the device index from its href.
        Uses the optimized href index for faster lookups.

        Args:
            href: The device href string

        Returns:
            The device index if found, otherwise None
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

    def add(self, device: m.EndDevice) -> m.EndDevice:
        """Add a new end device."""
        with self._write_lock():
            self._track_operation("add")

            try:
                with atomic_operation():
                    import pickle

                    # Get current count for href generation
                    count_key = "counter:enddevice"
                    count_data = self._db.get_point(count_key)
                    current_count = 0 if count_data is None else pickle.loads(count_data)

                    # Set href if not present
                    if not device.href:
                        device.href = f"/edev/{current_count}"

                    # Store device
                    device_key = f"enddevice:{current_count}"
                    self._db.set_point(device_key, pickle.dumps(device))

                    # Update indices
                    if device.lFDI is not None:
                        self._update_lfdi_index(device.lFDI, current_count)
                    if device.href is not None:
                        self._update_href_index(device.href, current_count)

                    # Update counter
                    self._db.set_point(count_key, pickle.dumps(current_count + 1))

                _log.info(f"Added end device {device.href}")
                return device

            except Exception as e:
                _log.error(f"Failed to add end device: {e}")
                raise

    def put(self, index: int, device: m.EndDevice) -> AdapterResult:
        """Update an existing end device."""
        with self._write_lock():
            self._track_operation("put")

            try:
                with atomic_operation():
                    import pickle

                    # Store device
                    device_key = f"enddevice:{index}"

                    # Check if device exists
                    if not self._db.exists(device_key):
                        return AdapterResult(
                            success=False,
                            error=f"End device with index {index} not found"
                        )

                    # Get existing device to preserve some data
                    existing_data = self._db.get_point(device_key)
                    if existing_data is None:
                        raise RuntimeError(f"Expected existing device at index {index} but found None")
                    existing_device = pickle.loads(existing_data)

                    # Update device
                    self._db.set_point(device_key, pickle.dumps(device))

                    # Update indices if needed
                    if existing_device.lFDI != device.lFDI and device.lFDI is not None:
                        self._update_lfdi_index(device.lFDI, index)

                    if existing_device.href != device.href and device.href is not None:
                        self._update_href_index(device.href, index)

                _log.info(f"Updated end device {device.href}")
                return AdapterResult(success=True, data=device, was_update=True)

            except Exception as e:
                _log.error(f"Failed to update end device: {e}")
                return AdapterResult(success=False, error=str(e))

    def fetch_all(self, list_obj=None, start: int = 0, after: int = 0, limit: int = 0) -> Any:
        """Fetch all end devices with pagination."""
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

                if limit > 0:
                    end = min(start + limit, device_count)
                else:
                    end = device_count

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

    def fetch_by_lfdi(self, lfdi: bytes) -> Optional[m.EndDevice]:
        """Fetch end device by LFDI."""
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

    def fetch_by_property(self, prop_name: str, prop_value: Any) -> Optional[m.EndDevice]:
        """Fetch end device by property (optimized for common properties)."""
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

    def _update_lfdi_index(self, lfdi: bytes, device_index: int):
        """Update the LFDI index."""
        try:
            import pickle

            index_data = self._db.get_point(self._lfdi_index_key)
            lfdi_index = {} if index_data is None else pickle.loads(index_data)

            lfdi_index[lfdi] = device_index
            self._db.set_point(self._lfdi_index_key, pickle.dumps(lfdi_index))

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

# Global adapter instances with proper initialization
_adapters_lock = threading.Lock()
_initialized = False

# Global adapter instances
ListAdapter: ThreadSafeListAdapter | None = None
EndDeviceAdapter: ThreadSafeEndDeviceAdapter | None = None

def initialize_adapters():
    """Initialize all global adapter instances."""
    global ListAdapter, EndDeviceAdapter, _initialized

    if _initialized:
        return

    with _adapters_lock:
        if _initialized:
            return

        _log.info("Initializing thread-safe adapters...")

        # Initialize adapters
        ListAdapter = ThreadSafeListAdapter(object)  # Generic list adapter
        EndDeviceAdapter = ThreadSafeEndDeviceAdapter()

        _initialized = True
        _log.info("Thread-safe adapters initialized")

def get_adapter_stats() -> Dict[str, Any]:
    """Get performance statistics from all adapters."""
    if not _initialized:
        return {}

    return {
        'list_adapter': ListAdapter.get_stats() if ListAdapter is not None else {},
        'enddevice_adapter': EndDeviceAdapter.get_stats() if EndDeviceAdapter is not None else {},
    }

# Initialize adapters on module import
initialize_adapters()
