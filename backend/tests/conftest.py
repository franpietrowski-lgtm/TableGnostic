import pytest_asyncio  # noqa: F401  # ensure asyncio plugin loaded
import pytest

# Default asyncio mode for this dir
pytest_plugins = ["pytest_asyncio"]


def pytest_collection_modifyitems(config, items):
    pass
