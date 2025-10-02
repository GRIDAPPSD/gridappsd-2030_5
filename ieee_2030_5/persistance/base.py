"""
Abstract base class for point store implementations.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager


class PointStoreBase(ABC):
    """Abstract base class for point store implementations."""

    @abstractmethod
    def set_point(self, key: str, value: bytes) -> None:
        """
        Set a point into the key/value store.

        Args:
            key: The key to store the value under
            value: The bytes value to store
        """
        pass

    @abstractmethod
    def get_point(self, key: str) -> bytes | None:
        """
        Retrieve a point from the key/value store.

        Args:
            key: The key to retrieve

        Returns:
            The stored bytes value, or None if key doesn't exist
        """
        pass

    @abstractmethod
    def delete_point(self, key: str) -> bool:
        """
        Delete a point from the store.

        Args:
            key: The key to delete

        Returns:
            True if the key existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    def get_hrefs(self) -> list[str]:
        """
        Get all stored href keys.

        Returns:
            List of all keys in the store
        """
        pass

    @abstractmethod
    def get_keys_matching(self, pattern: str) -> list[str]:
        """
        Get all keys that match a pattern.

        Args:
            pattern: Pattern to match (supports '*' as wildcard)

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all points from the store. Use with caution!"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Get the number of stored points."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the store."""
        pass

    @abstractmethod
    def bulk_set(self, items: dict[str, bytes]) -> None:
        """
        Set multiple points in a single operation.

        Args:
            items: Dictionary mapping keys to values
        """
        pass

    @abstractmethod
    def bulk_get(self, keys: list[str]) -> dict[str, bytes]:
        """
        Get multiple points in a single operation.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary mapping found keys to their values
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection and storage."""
        pass

    @abstractmethod
    @contextmanager
    def atomic_operation(self):
        """
        Context manager for atomic operations across multiple point operations.

        Example:
            with db.atomic_operation():
                db.set_point("key1", b"value1")
                db.set_point("key2", b"value2")
                # Both operations committed together, or both rolled back on error
        """
        pass
