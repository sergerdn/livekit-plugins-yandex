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
"""Main pytest configuration for Yandex SpeechKit STT plugin tests.

This file provides a common configuration for all test types. Specific test directories
(unit/, functional/, integration/) have their own conftest.py files with specialized
fixtures and configuration.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Callable, Dict, Generator, List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials

from . import FIXTURES_DIR, PROJECT_DIR

# Configure logging for all tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@pytest.fixture
def mock_yandex_stt(mock_yandex_credentials: YandexCredentials) -> STT:
    """Create an STT instance with mock Yandex credentials."""
    return STT(
        api_key=mock_yandex_credentials.api_key,
        folder_id=mock_yandex_credentials.folder_id,
        language="ru-RU",
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures' directory."""
    assert FIXTURES_DIR.is_dir(), "Fixtures directory not found"

    return FIXTURES_DIR


@pytest.fixture
def sample_audio_files(fixtures_dir: Path) -> dict[str, Path]:
    """Dictionary of available sample audio files.

    Returns:
        dict: Mapping of language codes to audio file paths
    """
    audio_files = {}

    # Check for Russian audio samples
    russian_files = {
        "russian_greeting.wav": "ru_greeting",
        "russian_weather.wav": "ru_weather",
        "russian_learning.wav": "ru_learning",
    }

    for filename, key in russian_files.items():
        file_path = fixtures_dir / filename
        if file_path.exists():
            audio_files[key] = file_path

    # Check for English audio samples
    english_files = {
        "english_greeting.wav": "en_greeting",
        "english_weather.wav": "en_weather",
        "english_learning.wav": "en_learning",
    }

    for filename, key in english_files.items():
        file_path = fixtures_dir / filename
        if file_path.exists():
            audio_files[key] = file_path

    # Check for special samples
    special_files = {
        "mixed_languages.wav": "mixed_languages",
        "silence.wav": "silence",
    }

    for filename, key in special_files.items():
        file_path = fixtures_dir / filename
        if file_path.exists():
            audio_files[key] = file_path

    return audio_files


@pytest.fixture
def skip_if_no_credentials() -> Callable[[], None]:
    """Skip the test if no real credentials are available."""

    def _skip_if_no_credentials() -> None:
        has_api_key = bool(os.environ.get("YANDEX_API_KEY"))
        has_folder_id = bool(os.environ.get("YANDEX_FOLDER_ID"))

        if not (has_folder_id and has_api_key):
            pytest.skip(
                "Missing Yandex credentials - ensure YANDEX_FOLDER_ID and YANDEX_API_KEY are set"
            )

    return _skip_if_no_credentials


@pytest.fixture
def skip_if_no_audio() -> Callable[[Dict[str, str]], None]:
    """Skip the test if no audio files are available."""

    def _skip_if_no_audio(audio_files: Dict[str, str]) -> None:
        if not audio_files:
            pytest.skip("No audio test files available - see tests/fixtures/README.md")

    return _skip_if_no_audio


# Pytest markers for different test types
def pytest_configure(config: Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (no external dependencies)")
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires credentials)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark tests based on their names and requirements."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "real_" in item.name:
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "slow" in item.nodeid or "performance" in item.name:
            item.add_marker(pytest.mark.slow)

        # Default to unit test if no other marker
        if not any(marker.name in ["integration", "slow"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Environment validation
def pytest_sessionstart(session: pytest.Session) -> None:
    """Validate environment at session start."""
    print("Starting Yandex SpeechKit STT Plugin Tests")

    # Check if .env file exists
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        print(f"Found .env file: {env_file}")
    else:
        print(f"No .env file found: {env_file}")
        print("Create .env file for functional tests (see .env.example)")

    # Check for test fixtures
    assert FIXTURES_DIR.exists(), "Test fixtures directory not found"

    audio_files = list(FIXTURES_DIR.glob("*.wav"))
    if audio_files:
        print(f"Found {len(audio_files)} audio test files")
    else:
        print("No audio test files found in tests/fixtures/")
        print("Add audio files for functional tests (see tests/fixtures/README.md)")

    # Check for credentials (without exposing them)
    has_api_key = bool(os.environ.get("YANDEX_API_KEY"))
    has_folder_id = bool(os.environ.get("YANDEX_FOLDER_ID"))

    if has_api_key:
        print("Yandex credentials available")
    else:
        print("No Yandex credentials found")
        print("Set YANDEX_API_KEY for integration tests")

    if has_folder_id:
        print("Yandex folder ID available")
    else:
        print("No Yandex folder ID found")
        print("Set YANDEX_FOLDER_ID for integration tests")

    print()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up after a test session."""
    print(f"Test session finished with exit status: {exitstatus}")
