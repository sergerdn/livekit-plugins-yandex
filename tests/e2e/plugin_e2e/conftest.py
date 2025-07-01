"""Pytest configuration for end-to-end tests.

End-to-end tests require real Yandex Cloud credentials and make actual API calls to
validate the complete speech recognition workflow with real audio files.
"""

import os
from pathlib import Path
from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

# Note: YandexCredentials and other shared fixtures are available from the global tests/conftest.py


def pytest_configure(config: Config) -> None:
    """Configure custom pytest markers for e2e tests."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end (requires credentials and network)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running (may take several seconds)")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark e2e tests."""
    for item in items:
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


# Note: real_credentials fixture is available from the global tests/conftest.py


def pytest_sessionstart(session: pytest.Session) -> None:
    """Print e2e test session information."""
    print("\nStarting End-to-End Tests for Yandex SpeechKit STT Plugin")
    print("=" * 70)

    # Check credentials
    api_key = os.environ.get("YANDEX_API_KEY")
    folder_id = os.environ.get("YANDEX_FOLDER_ID")

    if api_key and folder_id:
        print("Credentials available")
        print(f"API Key: {api_key[:15]}...")
        print(f"Folder ID: {folder_id}")
    else:
        print("Credentials missing - e2e tests will be skipped")

    # Check audio fixtures
    fixtures_dir = Path("tests/fixtures")
    if fixtures_dir.exists():
        audio_files = list(fixtures_dir.glob("*.wav"))
        print(f"Audio fixtures: {len(audio_files)} files available")
        for audio_file in sorted(audio_files):
            size_kb = round(audio_file.stat().st_size / 1024, 1)
            print(f"   {audio_file.name}: {size_kb} KB")
    else:
        print("Audio fixtures missing - run 'make fixtures' to generate")

    print()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Print e2e test session results."""
    print("\nEnd-to-End Test Session Complete")
    print(f"Exit status: {exitstatus}")

    if exitstatus == 0:
        print("All e2e tests passed - plugin is working correctly with real Yandex Cloud API!")
    else:
        print("Some e2e tests failed - check logs for details")
    print("=" * 70)
