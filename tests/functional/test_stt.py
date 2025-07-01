# Copyright 2023 LiveKit, Inc.
#
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
"""Functional tests for Yandex SpeechKit STT plugin.

These tests validate component behavior in isolation using mocked dependencies.
They do NOT require real credentials or make actual API calls.

To run these tests:
1. Run: make test_functional
"""

from pathlib import Path
from typing import Dict

import pytest

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials


@pytest.mark.functional
@pytest.mark.slow
class TestYandexSTTAudioProcessing:
    """Functional tests for audio processing with real audio files."""

    def test_audio_files_available(self, sample_audio_files: Dict[str, Path]) -> None:
        """Test that audio files are available for testing."""
        if not sample_audio_files:
            pytest.skip("No audio test files available - see tests/fixtures/README.md")

        # Check that at least one audio file exists
        assert len(sample_audio_files) > 0

        # Verify files actually exist
        for name, path in sample_audio_files.items():
            assert path.exists(), f"Audio file {name} does not exist at {path}"
            assert path.suffix.lower() in [
                ".wav",
                ".mp3",
                ".opus",
            ], f"Unsupported audio format: {path.suffix}"

    def test_audio_file_properties(self, sample_audio_files: Dict[str, Path]) -> None:
        """Test audio file properties and format validation."""
        if not sample_audio_files:
            pytest.skip("No audio test files available")

        for name, path in sample_audio_files.items():
            # Basic file checks
            assert path.stat().st_size > 0, f"Audio file {name} is empty"
            assert path.stat().st_size < 50 * 1024 * 1024, f"Audio file {name} is too large (>50MB)"

            # Check file extension
            assert path.suffix.lower() in [
                ".wav",
                ".mp3",
                ".opus",
            ], f"Unsupported format: {path.suffix}"

    @pytest.mark.asyncio
    async def test_stt_stream_creation_async(self, mock_yandex_stt_functional: STT) -> None:
        """Test STT stream creation in an async context."""
        # This test verifies that stream creation works in a proper async context
        stream = mock_yandex_stt_functional.stream()
        assert stream is not None

        # Clean up
        await stream.aclose()

    def test_convert_audio_frame_function_exists(self) -> None:
        """Test that the audio conversion function exists."""
        from livekit.plugins.yandex._utils import convert_audio_frame_to_pcm

        assert callable(convert_audio_frame_to_pcm)


@pytest.mark.functional
@pytest.mark.slow
class TestYandexSTTPerformance:
    """Performance tests for STT functionality with real credentials."""

    def test_stt_initialization_performance(
        self, mock_yandex_credentials_functional: YandexCredentials
    ) -> None:
        """Test STT initialization performance."""
        import time

        start_time = time.time()

        for _ in range(10):
            STT(
                api_key=mock_yandex_credentials_functional.api_key,
                folder_id=mock_yandex_credentials_functional.folder_id,
            )

        end_time = time.time()

        total_time = end_time - start_time

        # Should be able to create 10 instances in less than 1 second
        assert total_time < 1.0, f"STT initialization too slow: {total_time:.2f}s for 10 instances"
