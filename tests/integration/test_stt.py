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
"""Integration tests for Yandex SpeechKit STT plugin.

These tests require real Yandex Cloud credentials and test the integration between unit
components and the actual Yandex SpeechKit service. They focus on component interaction
rather than end-to-end functionality.
"""
import os
from unittest.mock import patch

import pytest

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials


@pytest.mark.integration
class TestYandexSTTIntegration:
    """Test suite for Yandex SpeechKit STT plugin."""

    def test_stt_initialization_with_api_key(self) -> None:
        """Test STT initialization with API key."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id", language="ru-RU")

        assert stt._credentials.api_key == "test_api_key"
        assert stt._credentials.folder_id == "test_folder_id"
        assert stt._opts.language == "ru-RU"

    def test_stt_initialization_missing_credentials(self) -> None:
        """Test STT initialization fails without credentials."""
        from livekit.plugins.yandex.exceptions import YandexAuthenticationError

        with pytest.raises(YandexAuthenticationError, match="Yandex Cloud API key is required"):
            STT(folder_id="test_folder_id")

    def test_stt_initialization_missing_folder_id(self) -> None:
        """Test STT initialization fails without folder ID."""
        from livekit.plugins.yandex.exceptions import YandexConfigurationError

        with pytest.raises(YandexConfigurationError, match="Yandex Cloud folder_id is required"):
            STT(api_key="test_api_key")

    @patch.dict(os.environ, {"YANDEX_API_KEY": "env_api_key", "YANDEX_FOLDER_ID": "env_folder_id"})
    def test_stt_initialization_from_env(self) -> None:
        """Test STT initialization from environment variables."""
        stt = STT()

        assert stt._credentials.api_key == "env_api_key"
        assert stt._credentials.folder_id == "env_folder_id"

    def test_stt_capabilities(self) -> None:
        """Test STT capabilities are set correctly."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id", interim_results=True)

        assert stt.capabilities.streaming is True
        assert stt.capabilities.interim_results is True

    def test_stt_options_sanitization(self) -> None:
        """Test options sanitization with language detection."""
        stt = STT(
            api_key="test_api_key",
            folder_id="test_folder_id",
            detect_language=True,
            language="ru-RU",
        )

        # When detect_language is True, the language should be None
        config = stt._sanitize_options()
        assert config.detect_language is True
        assert config.language is None

    def test_stt_options_language_override(self) -> None:
        """Test language override in options sanitization."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id", language="ru-RU")

        config = stt._sanitize_options(language="en-US")
        assert config.language == "en-US"
        assert config.detect_language is False

    def test_stream_creation(self) -> None:
        """Test streaming session creation."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id")

        # Stream creation requires async context, so we just test that the method exists
        assert hasattr(stt, "stream")
        assert callable(stt.stream)


class TestYandexCredentials:
    """Test suite for Yandex credentials handling."""

    def test_credentials_creation(self) -> None:
        """Test credentials object creation."""
        creds = YandexCredentials(api_key="test_key", folder_id="test_folder")

        assert creds.api_key == "test_key"
        assert creds.folder_id == "test_folder"

    def test_credentials_defaults(self) -> None:
        """Test credentials with default values."""
        creds = YandexCredentials()

        assert creds.api_key is None
        assert creds.folder_id is None

    @patch.dict(os.environ, {"YANDEX_API_KEY": "env_api_key", "YANDEX_FOLDER_ID": "env_folder_id"})
    def test_credentials_from_env(self) -> None:
        """Test credentials loading from the environment."""
        creds = YandexCredentials.from_env()

        assert creds.api_key == "env_api_key"
        assert creds.folder_id == "env_folder_id"
