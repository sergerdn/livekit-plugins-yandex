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
"""Consolidated fixture validation tests.

These tests validate that the test infrastructure is properly set up before running
functional and e2e tests.
They check basic requirements without making external API calls.

All tests in this file are marked with
@pytest.mark.dependency(name="fixture_validation") so that other tests can depend on
fixture validation passing.
"""

import logging
import os
from typing import NoReturn

import pytest

from tests import FIXTURES_DIR

logger = logging.getLogger("test-fixture-validation")


@pytest.mark.dependency()
class TestFixtureValidation:
    """Basic fixture validation tests that run before all dependent tests."""

    @pytest.mark.dependency(name="fixtures_directory", scope="session")
    def test_fixtures_directory_exists(self) -> None:
        """Test that the fixtures directory exists and is accessible."""
        logger.info("")
        logger.info("run:test_fixtures_directory_exists")

        assert FIXTURES_DIR.exists(), f"Fixtures directory does not exist: {FIXTURES_DIR}"
        assert FIXTURES_DIR.is_dir(), f"Fixtures path is not a directory: {FIXTURES_DIR}"

    @pytest.mark.dependency(name="audio_fixtures", depends=["fixtures_directory"], scope="session")
    def test_audio_fixtures_available(self) -> None:
        """Test that audio fixtures are available."""
        logger.info("")
        logger.info("run:test_audio_fixtures_available")

        # Find all WAV files in the fixtures directory
        wav_files = list(FIXTURES_DIR.glob("*.wav"))

        assert len(wav_files) > 0, f"No WAV files found in fixtures directory: {FIXTURES_DIR}"

        # Check for basic file categories
        russian_files = [f for f in wav_files if f.name.startswith("russian_")]
        english_files = [f for f in wav_files if f.name.startswith("english_")]

        assert len(russian_files) > 0, "No Russian audio files found"
        assert len(english_files) > 0, "No English audio files found"

    @pytest.mark.dependency(name="e2e_credentials", scope="session")
    def test_e2e_credentials_available(self) -> None:
        """Test that e2e credentials are available."""
        # Yandex credentials (required for e2e tests) - raise early if missing
        yandex_api_key = os.environ.get("YANDEX_API_KEY") or self._raise_missing_env(
            "YANDEX_API_KEY"
        )
        yandex_folder_id = os.environ.get("YANDEX_FOLDER_ID") or self._raise_missing_env(
            "YANDEX_FOLDER_ID"
        )

        # LiveKit credentials (required for e2e_agent tests) - raise early if missing
        livekit_api_key = os.environ.get("LIVEKIT_API_KEY") or self._raise_missing_env(
            "LIVEKIT_API_KEY"
        )
        livekit_api_secret = os.environ.get("LIVEKIT_API_SECRET") or self._raise_missing_env(
            "LIVEKIT_API_SECRET"
        )
        livekit_ws_url = os.environ.get("LIVEKIT_WS_URL") or self._raise_missing_env(
            "LIVEKIT_WS_URL"
        )

        # Basic format validation
        assert len(yandex_api_key.strip()) > 10, "YANDEX_API_KEY appears too short"
        assert len(yandex_folder_id.strip()) > 5, "YANDEX_FOLDER_ID appears too short"
        assert len(livekit_api_key.strip()) > 10, "LIVEKIT_API_KEY appears too short"
        assert len(livekit_api_secret.strip()) > 10, "LIVEKIT_API_SECRET appears too short"
        assert livekit_ws_url.startswith(
            ("ws://", "wss://")
        ), "LIVEKIT_WS_URL should start with ws:// or wss://"

    def _raise_missing_env(self, env_var: str) -> NoReturn:
        """Raise EnvironmentError for missing environment variable."""
        raise EnvironmentError(f"{env_var} not set - e2e tests cannot run")
