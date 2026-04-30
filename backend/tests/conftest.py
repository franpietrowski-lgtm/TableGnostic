import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env so direct-imports of `routes.*` (which chain to
# `core.config`) don't KeyError on MONGO_URL / DB_NAME.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import pytest_asyncio  # noqa: F401  # ensure asyncio plugin loaded
import pytest

# Default asyncio mode for this dir
pytest_plugins = ["pytest_asyncio"]


def pytest_collection_modifyitems(config, items):
    pass
