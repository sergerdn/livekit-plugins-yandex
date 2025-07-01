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
"""Pytest configuration for functional tests.

Functional tests validate the behavior of components in isolation using mocked
dependencies. They do NOT require real credentials or make actual API calls.
"""
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials


# Functional-specific fixtures that use mocks instead of real credentials
@pytest.fixture
def mock_yandex_credentials_functional() -> YandexCredentials:
    """Provide mock Yandex credentials for functional tests."""
    return YandexCredentials(
        api_key="AQVN_functional_test_api_key_1234567890abcdef",
        folder_id="b1g_functional_test_folder_id",
    )


@pytest.fixture
def mock_yandex_stt_functional(mock_yandex_credentials_functional: YandexCredentials) -> STT:
    """Create an STT instance with mock credentials for functional tests."""
    return STT(
        api_key=mock_yandex_credentials_functional.api_key,
        folder_id=mock_yandex_credentials_functional.folder_id,
        language="ru-RU",
    )


@pytest.fixture
def mock_grpc_channel() -> MagicMock:
    """Mock gRPC channel for functional tests."""
    mock_channel = MagicMock()
    mock_channel.close = MagicMock()
    return mock_channel


@pytest.fixture
def mock_speech_stream() -> AsyncMock:
    """Mock speech stream for functional tests."""
    mock_stream = AsyncMock()
    mock_stream.aclose = AsyncMock()
    mock_stream._closed = False
    return mock_stream


# Note: Audio file fixtures (fixtures_dir, sample_audio_files) are available from the global tests/conftest.py


# Pytest configuration for functional tests
def pytest_configure(config: Config) -> None:
    """Configure functional test markers."""
    config.addinivalue_line(
        "markers", "functional: mark test as a functional test (uses mocks, no real API calls)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark tests based on their names and requirements."""
    for item in items:
        # Mark all tests in this directory as functional
        item.add_marker(pytest.mark.functional)

        # Mark slow tests
        if "slow" in item.nodeid or "performance" in item.name:
            item.add_marker(pytest.mark.slow)


# Note: event_loop fixture is available from the global tests/conftest.py


def pytest_sessionstart(session: pytest.Session) -> None:
    """Functional test session start."""
    print("Starting functional tests - using mocks, no real API calls")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Functional test session finish."""
    if exitstatus == 0:
        print("Functional tests completed successfully")
    else:
        print(f"Functional tests completed with exit status: {exitstatus}")
