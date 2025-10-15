#!/usr/bin/env python3
"""
High traffic concurrency tests for GridAPPSD adapter lock fixes.

This test simulates high traffic scenarios with concurrent HTTP PUT requests
and GridAPPSD adapter publishing to verify lock contention is resolved.
"""

import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import Mock

import pytest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.models as m
from ieee_2030_5.persistance.points import ZODBPointStore

# Only import GridAPPSD if available
try:
    from ieee_2030_5.adapters.gridappsd_adapter import GridAPPSDAdapter, HouseLookup

    GRIDAPPSD_AVAILABLE = True
except ImportError:
    GRIDAPPSD_AVAILABLE = False


@pytest.fixture(scope="session")
def high_traffic_database():
    """Set up database for high traffic testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "high_traffic_test.fs"
        db = ZODBPointStore(db_path)

        # Replace global database
        original_db = getattr(adpt.ListAdapter, "_db", None)
        adpt.get_list_adapter()._db = db
        adpt.initialize_adapters()

        yield db

        # Restore
        if original_db:
            adpt.get_list_adapter()._db = original_db

        try:
            if hasattr(db, "_storage"):
                db._storage.close()
            if hasattr(db, "_db"):
                db._db.close()
        except Exception:
            pass


@pytest.fixture
def traffic_adapter(monkeypatch):
    """Create GridAPPSD adapter for traffic testing."""
    if not GRIDAPPSD_AVAILABLE:
        pytest.skip("GridAPPSD not available")

    # Set required environment variables
    monkeypatch.setenv("GRIDAPPSD_SIMULATION_ID", "traffic_test_sim_456")
    monkeypatch.setenv("GRIDAPPSD_SERVICE_NAME", "traffic_test_service")

    # Mock GridAPPSD connection
    mock_gapps = Mock()
    mock_gapps.connected = True
    mock_gapps.subscribe = Mock()

    # Create adapter with proper config
    adapter = GridAPPSDAdapter(
        gapps=mock_gapps,
        gridappsd_configuration={
            "field_bus_def": {"id": "traffic_test_bus"},
            "publish_interval_seconds": 1,  # Fast publishing for stress test
            "house_named_inverters_regex": None,
            "utility_named_inverters_regex": None,
            "model_name": "traffic_test_model",
            "default_pin": "123456",
        },
        tls=Mock(),
    )

    # Set up test inverters
    adapter._inverters = [
        HouseLookup(mRID=f"house_{i:03d}", name=f"House{i}", lfdi=f"lfdi_house_{i:03d}")
        for i in range(50)  # 50 houses for realistic load
    ]

    return adapter


def create_traffic_der_status(house_id: int, soc_value: int, timestamp: int = None) -> tuple:
    """Create DERStatus for traffic testing."""
    if timestamp is None:
        timestamp = int(time.time())

    uri = f"/der/{house_id}/ders"
    lfdi = f"lfdi_house_{house_id:03d}"

    der_status = m.DERStatus(
        href=uri,
        readingTime=timestamp,
        stateOfChargeStatus=m.StateOfChargeStatusType(dateTime=timestamp, value=soc_value),
        inverterStatus=m.InverterStatusType(
            dateTime=timestamp,
            value=1,  # Operating
        ),
    )

    return uri, lfdi, der_status


@pytest.mark.skipif(not GRIDAPPSD_AVAILABLE, reason="GridAPPSD not installed")
class TestHighTrafficLocks:
    """Test lock behavior under high traffic conditions."""

    def test_concurrent_writes_and_reads(self, high_traffic_database, traffic_adapter):
        """Test concurrent HTTP PUT writes and adapter reads."""

        num_writers = 20  # Simulate 20 concurrent clients
        num_reads = 50  # Simulate 50 read operations
        writes_per_thread = 10

        write_results = []
        read_results = []
        exceptions = []

        def write_worker(thread_id: int):
            """Simulate HTTP PUT operations."""
            try:
                for i in range(writes_per_thread):
                    house_id = (thread_id * writes_per_thread + i) % 50
                    soc_value = 50 + (house_id + i) % 50
                    timestamp = int(time.time()) + i

                    uri, lfdi, der_status = create_traffic_der_status(house_id, soc_value, timestamp)

                    # Simulate HTTP PUT processing
                    result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
                    write_results.append((thread_id, i, result.success))

                    # Small delay to simulate realistic timing
                    time.sleep(0.001)
            except Exception as e:
                exceptions.append(f"Write thread {thread_id}: {e}")

        def read_worker(read_id: int):
            """Simulate adapter get_message_for_bus operations."""
            try:
                for i in range(5):  # Multiple reads per thread
                    message = traffic_adapter.get_message_for_bus()
                    read_results.append((read_id, i, len(message)))

                    # Realistic adapter polling interval
                    time.sleep(0.01)
            except Exception as e:
                exceptions.append(f"Read thread {read_id}: {e}")

        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=30) as executor:
            # Start writers
            write_futures = [executor.submit(write_worker, thread_id) for thread_id in range(num_writers)]

            # Start readers slightly after writers begin
            time.sleep(0.05)
            read_futures = [executor.submit(read_worker, read_id) for read_id in range(num_reads)]

            # Wait for completion
            all_futures = write_futures + read_futures
            for future in as_completed(all_futures):
                try:
                    future.result()
                except Exception as e:
                    exceptions.append(f"Future execution: {e}")

        # Verify no exceptions occurred
        if exceptions:
            pytest.fail(f"Concurrency exceptions occurred: {exceptions[:5]}")  # Show first 5

        # Verify writes succeeded
        successful_writes = sum(1 for _, _, success in write_results if success)
        total_writes = num_writers * writes_per_thread

        assert successful_writes == total_writes, f"Only {successful_writes}/{total_writes} writes succeeded"

        # Verify reads occurred without errors
        assert len(read_results) == num_reads * 5, f"Expected {num_reads * 5} reads, got {len(read_results)}"

        # Verify final state
        final_message = traffic_adapter.get_message_for_bus()
        assert isinstance(final_message, dict)

        print(f"✅ Concurrent test completed: {successful_writes} writes, {len(read_results)} reads")
        print(f"✅ Final message contains {len(final_message)} houses")

    def test_rapid_publishing_stress(self, high_traffic_database, traffic_adapter):
        """Test rapid publishing cycles under load."""

        # Store initial data
        for i in range(25):
            uri, lfdi, der_status = create_traffic_der_status(i, 75 + i)
            result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
            assert result.success

        publishing_results = []
        exceptions = []

        def rapid_publisher(pub_id: int):
            """Simulate rapid publishing cycles."""
            try:
                for cycle in range(20):  # 20 rapid cycles
                    start_time = time.time()
                    message = traffic_adapter.get_message_for_bus()
                    processing_time = time.time() - start_time

                    publishing_results.append((pub_id, cycle, len(message), processing_time))

                    # Very short interval to stress test
                    time.sleep(0.002)
            except Exception as e:
                exceptions.append(f"Publisher {pub_id}: {e}")

        # Run multiple concurrent publishers
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(rapid_publisher, pub_id) for pub_id in range(10)]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    exceptions.append(f"Publisher future: {e}")

        # Verify no exceptions
        if exceptions:
            pytest.fail(f"Publishing exceptions: {exceptions[:3]}")

        # Verify all publishing cycles completed
        assert len(publishing_results) == 200  # 10 publishers * 20 cycles

        # Verify reasonable performance (no deadlocks causing timeouts)
        avg_processing_time = sum(time for _, _, _, time in publishing_results) / len(publishing_results)
        assert avg_processing_time < 0.1, f"Average processing time too high: {avg_processing_time:.3f}s"

        print(f"✅ Rapid publishing test: 200 cycles completed, avg time: {avg_processing_time:.3f}s")

    def test_mixed_workload_performance(self, high_traffic_database, traffic_adapter):
        """Test performance under mixed read/write workload."""

        results = {"writes": [], "reads": [], "errors": []}

        def mixed_workload_worker(worker_id: int):
            """Worker performing mixed read/write operations."""
            try:
                for i in range(15):
                    # Write operation
                    house_id = (worker_id * 15 + i) % 50
                    uri, lfdi, der_status = create_traffic_der_status(house_id, 80 + i)

                    write_start = time.time()
                    result = adpt.get_list_adapter().set_single(uri, der_status, lfdi)
                    write_time = time.time() - write_start

                    results["writes"].append((worker_id, i, result.success, write_time))

                    # Read operation
                    read_start = time.time()
                    message = traffic_adapter.get_message_for_bus()
                    read_time = time.time() - read_start

                    results["reads"].append((worker_id, i, len(message), read_time))

                    # Brief pause
                    time.sleep(0.005)
            except Exception as e:
                results["errors"].append(f"Worker {worker_id}: {e}")

        # Execute mixed workload
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(mixed_workload_worker, worker_id) for worker_id in range(15)]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    results["errors"].append(f"Future: {e}")

        # Verify results
        if results["errors"]:
            pytest.fail(f"Mixed workload errors: {results['errors'][:3]}")

        # Check operation counts
        assert len(results["writes"]) == 225  # 15 workers * 15 writes
        assert len(results["reads"]) == 225  # 15 workers * 15 reads

        # Check success rates
        successful_writes = sum(1 for _, _, success, _ in results["writes"] if success)
        assert successful_writes == 225, f"Only {successful_writes}/225 writes succeeded"

        # Check performance
        avg_write_time = sum(time for _, _, _, time in results["writes"]) / len(results["writes"])
        avg_read_time = sum(time for _, _, _, time in results["reads"]) / len(results["reads"])

        assert avg_write_time < 0.05, f"Average write time too high: {avg_write_time:.3f}s"
        assert avg_read_time < 0.05, f"Average read time too high: {avg_read_time:.3f}s"

        print(f"✅ Mixed workload completed: avg write={avg_write_time:.3f}s, avg read={avg_read_time:.3f}s")

    def test_deadlock_detection(self, high_traffic_database, traffic_adapter):
        """Test that lock fixes prevent deadlocks under extreme contention."""

        deadlock_detected = threading.Event()
        operations_completed = []

        def stress_worker(worker_id: int):
            """High stress operations to test for deadlocks."""
            try:
                for i in range(30):
                    if deadlock_detected.is_set():
                        break

                    # Rapid write
                    house_id = worker_id % 50
                    uri, lfdi, der_status = create_traffic_der_status(house_id, worker_id + i)
                    adpt.get_list_adapter().set_single(uri, der_status, lfdi)

                    # Immediate read
                    message = traffic_adapter.get_message_for_bus()

                    operations_completed.append((worker_id, i))

                    # No sleep - maximum contention
            except Exception as e:
                if "deadlock" in str(e).lower() or "timeout" in str(e).lower():
                    deadlock_detected.set()
                    pytest.fail(f"Potential deadlock detected in worker {worker_id}: {e}")

        # Start timeout monitor
        def timeout_monitor():
            time.sleep(5)  # 5 second timeout
            if not deadlock_detected.is_set() and len(operations_completed) < 200:
                deadlock_detected.set()
                pytest.fail("Operations appear deadlocked - completed too slowly")

        timeout_thread = threading.Thread(target=timeout_monitor)
        timeout_thread.start()

        # Execute high contention workload
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(stress_worker, worker_id) for worker_id in range(20)]

            for future in as_completed(futures):
                if deadlock_detected.is_set():
                    break
                future.result()

        timeout_thread.join(timeout=1)

        # Verify no deadlocks
        assert not deadlock_detected.is_set(), "Deadlock or extreme slowdown detected"
        assert len(operations_completed) >= 400, f"Only {len(operations_completed)} operations completed"

        print(f"✅ Deadlock test passed: {len(operations_completed)} operations completed without deadlock")


if __name__ == "__main__":
    # Run high traffic tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
