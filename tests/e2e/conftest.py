"""Pytest configuration for end-to-end tests.

End-to-end tests require real Yandex Cloud credentials and make actual API calls to
validate the complete speech recognition workflow with real audio files.
"""

import os
from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials


# E2E-specific fixtures that require real credentials
@pytest.fixture
def yandex_credentials() -> YandexCredentials:
    """Provide real Yandex credentials for E2E tests."""
    api_key = os.environ.get("YANDEX_API_KEY") or pytest.fail(
        "YANDEX_API_KEY environment variable not set. "
        "E2E tests require real Yandex Cloud credentials."
    )
    folder_id = os.environ.get("YANDEX_FOLDER_ID") or pytest.fail(
        "YANDEX_FOLDER_ID environment variable not set. "
        "E2E tests require real Yandex Cloud credentials."
    )

    return YandexCredentials(
        api_key=api_key,
        folder_id=folder_id,
    )


@pytest.fixture
def yandex_stt(yandex_credentials: YandexCredentials) -> STT:
    """Create an STT instance with real Yandex credentials for E2E tests."""
    return STT(
        api_key=yandex_credentials.api_key,
        folder_id=yandex_credentials.folder_id,
        language="ru-RU",
    )


# Pytest configuration for E2E tests
def pytest_configure(config: Config) -> None:
    """Configure E2E test markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test (requires real credentials and API calls)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark tests based on their names and requirements."""
    for item in items:
        # Mark all tests in this directory as e2e
        item.add_marker(pytest.mark.e2e)

        # Mark slow tests
        if "slow" in item.nodeid or "performance" in item.name:
            item.add_marker(pytest.mark.slow)
