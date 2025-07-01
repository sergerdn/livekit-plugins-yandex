# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Pytest configuration for unit tests.

Unit tests do not require real credentials or network access. They test individual
components in isolation using mocks and test data.
"""

from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

from livekit.plugins.yandex._utils import YandexCredentials


# Unit test-specific fixtures
@pytest.fixture
def mock_yandex_credentials() -> YandexCredentials:
    """Provide mock Yandex credentials with realistic-looking values."""
    return YandexCredentials(
        api_key="AQVN1234567890abcdef1234567890abcdef1234",
        folder_id="b1g1234567890abcdef",
    )


@pytest.fixture
def empty_yandex_credentials() -> YandexCredentials:
    """Provide empty Yandex credentials for testing validation."""
    return YandexCredentials()


# Pytest configuration for unit tests
def pytest_configure(config: Config) -> None:
    """Configure unit test markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (no external dependencies)")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark all tests in this directory as unit tests."""
    for item in items:
        item.add_marker(pytest.mark.unit)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Unit test session start."""
    print("Running unit tests - no external dependencies required")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Unit test session finish."""
    if exitstatus == 0:
        print("Unit tests completed successfully")
    else:
        print(f"Unit tests completed with exit status: {exitstatus}")
