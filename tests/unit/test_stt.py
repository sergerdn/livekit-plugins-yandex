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
"""Unit tests for Yandex SpeechKit STT plugin.

These tests do not require real credentials or network access. They test the core
functionality, configuration, and error handling.
"""

import os
from unittest.mock import patch

import pytest

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials
from livekit.plugins.yandex.models import YandexSTTLanguages, YandexSTTModels


@pytest.mark.unit
class TestYandexCredentials:
    """Unit tests for YandexCredentials class."""

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
        """Test credentials loading from environment."""
        creds = YandexCredentials.from_env()

        assert creds.api_key == "env_api_key"
        assert creds.folder_id == "env_folder_id"

    @patch.dict(os.environ, {}, clear=True)
    def test_credentials_from_env_empty(self) -> None:
        """Test credentials loading from an empty environment."""
        creds = YandexCredentials.from_env()

        assert creds.api_key is None
        assert creds.folder_id is None


@pytest.mark.unit
class TestYandexSTTConfiguration:
    """Unit tests for STT configuration and initialization."""

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

    def test_stt_default_configuration(self) -> None:
        """Test STT default configuration values."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id")

        assert stt._opts.model == "general"
        assert stt._opts.language == "ru-RU"
        assert stt._opts.sample_rate == 16000
        assert stt._opts.interim_results is True
        assert stt._opts.profanity_filter is False

    def test_stt_custom_configuration(self) -> None:
        """Test STT with custom configuration."""
        stt = STT(
            api_key="test_api_key",
            folder_id="test_folder_id",
            model="premium",
            language="en-US",
            sample_rate=8000,
            interim_results=False,
            profanity_filter=True,
        )

        assert stt._opts.model == "premium"
        assert stt._opts.language == "en-US"
        assert stt._opts.sample_rate == 8000
        assert stt._opts.interim_results is False
        assert stt._opts.profanity_filter is True

    def test_stream_method_exists(self) -> None:
        """Test that a stream method exists and is callable."""
        stt = STT(api_key="test_api_key", folder_id="test_folder_id")

        # Stream creation requires async context, so we just test that the method exists
        assert hasattr(stt, "stream")
        assert callable(stt.stream)


@pytest.mark.unit
class TestYandexSTTModels:
    """Unit tests for STT models and language definitions."""

    def test_language_types_exist(self) -> None:
        """Test that language types are defined."""
        # Test that the Literal types exist and can be imported
        assert YandexSTTLanguages is not None
        assert YandexSTTModels is not None

    def test_stt_with_valid_language_codes(self) -> None:
        """Test STT initialization with valid language codes."""
        stt = STT(
            api_key="test_api_key",
            folder_id="test_folder_id",
            language="en-US",
            model="general",
        )

        assert stt._opts.language == "en-US"
        assert stt._opts.model == "general"


@pytest.mark.unit
class TestYandexSTTUtilities:
    """Unit tests for utility functions."""

    def test_grpc_metadata_creation(self) -> None:
        """Test gRPC metadata creation."""
        from livekit.plugins.yandex._utils import create_grpc_metadata

        creds = YandexCredentials(api_key="test_api_key", folder_id="test_folder_id")

        metadata = create_grpc_metadata(creds)

        assert len(metadata) == 2
        assert ("authorization", "Api-Key test_api_key") in metadata
        assert ("x-folder-id", "test_folder_id") in metadata

    def test_grpc_metadata_missing_api_key(self) -> None:
        """Test gRPC metadata creation without API key."""
        from livekit.plugins.yandex._utils import create_grpc_metadata

        creds = YandexCredentials(folder_id="test_folder_id")
        metadata = create_grpc_metadata(creds)

        assert len(metadata) == 1
        assert ("x-folder-id", "test_folder_id") in metadata

    def test_grpc_metadata_missing_folder_id(self) -> None:
        """Test gRPC metadata creation without folder ID."""
        from livekit.plugins.yandex._utils import create_grpc_metadata

        creds = YandexCredentials(api_key="test_api_key")
        metadata = create_grpc_metadata(creds)

        assert len(metadata) == 1
        assert ("authorization", "Api-Key test_api_key") in metadata


@pytest.mark.unit
class TestYandexSTTYandexAPI:
    """Unit tests for Yandex API functionality."""

    def test_streaming_options_creation(self) -> None:
        """Test streaming options creation."""
        from livekit.plugins.yandex.yandex_api import create_streaming_options

        opts = create_streaming_options(
            model="general", language="ru-RU", sample_rate=16000, profanity_filter=False
        )

        assert opts is not None
        assert hasattr(opts, "recognition_model")
        assert opts.recognition_model is not None

    def test_audio_chunk_creation(self) -> None:
        """Test audio chunk creation."""
        from livekit.plugins.yandex.yandex_api import create_audio_chunk

        audio_data = b"test_audio_data"
        request = create_audio_chunk(audio_data)

        assert request.chunk is not None
        assert request.chunk.data == audio_data

    def test_session_request_creation(self) -> None:
        """Test session request creation."""
        from livekit.plugins.yandex.yandex_api import (
            create_session_request,
            create_streaming_options,
        )

        opts = create_streaming_options()
        request = create_session_request(opts)

        assert request.session_options is not None
        assert request.session_options == opts
