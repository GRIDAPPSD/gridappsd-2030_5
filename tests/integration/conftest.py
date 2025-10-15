"""
Shared fixtures and configuration for integration tests.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command line options for integration tests."""
    parser.addoption(
        "--integration", action="store_true", default=False, help="Run integration tests (requires server startup)"
    )
    parser.addoption("--server-port", action="store", default=8443, type=int, help="Port for test server")
    parser.addoption(
        "--skip-server-start",
        action="store_true",
        default=False,
        help="Skip starting test server (use existing running server)",
    )


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    """Automatically mark integration tests."""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def integration_test_config():
    """Base configuration for integration tests."""
    return {"run_integration": True, "server_timeout": 30, "request_timeout": 10, "database_wait_time": 2}
