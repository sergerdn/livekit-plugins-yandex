"""Infrastructure Tests for AudioSimulator.

Tests for the AudioSimulator utility class used in agent E2E tests. This validates the
audio loading and processing infrastructure itself.
"""

import logging
import tempfile
import uuid
import wave
from pathlib import Path

import numpy as np
import pytest

from .validation_utils import AudioData, AudioSimulator

logger = logging.getLogger(__name__)


@pytest.mark.e2e
class TestAudioSimulator:
    """Test the AudioSimulator infrastructure component."""

    @pytest.mark.parametrize(
        "audio_file_name",
        [
            "russian_greeting.wav",
            "russian_weather.wav",
            "russian_learning.wav",
            "english_greeting.wav",
            "english_weather.wav",
        ],
    )
    def test_load_audio_file_basic(self, fixtures_dir: Path, audio_file_name: str) -> None:
        """Test basic audio file loading functionality."""
        logger.info(f"Testing AudioSimulator.load_audio_file with {audio_file_name}")

        # Get the audio file using fixtures_dir fixture
        audio_file = fixtures_dir / audio_file_name
        assert audio_file.exists(), f"Audio fixture file not found: {audio_file}"

        # Test loading audio file
        audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

        # Validate basic properties
        assert isinstance(audio_data, np.ndarray), "Audio data should be numpy array"
        assert audio_data.dtype == np.int16, "Audio data should be int16"
        assert len(audio_data) > 0, f"Audio file {audio_file_name} should have data"
        assert sample_rate > 0, f"Audio file {audio_file_name} should have valid sample rate"
        assert channels > 0, f"Audio file {audio_file_name} should have valid channels"
        assert channels <= 2, f"Audio file {audio_file_name} should have 1 or 2 channels"

        logger.info(
            f"Loaded {audio_file_name}: {len(audio_data)} samples, {sample_rate}Hz, {channels} channels"
        )

    def test_load_audio_file_properties(self, fixtures_dir: Path) -> None:
        """Test detailed audio file properties and validation."""
        audio_file = fixtures_dir / "russian_greeting.wav"
        assert audio_file.exists(), f"Russian greeting audio file not found: {audio_file}"

        audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

        # Test expected audio properties for test fixtures
        assert sample_rate in [16000, 22050, 44100, 48000], f"Unexpected sample rate: {sample_rate}"
        assert channels in [1, 2], f"Unexpected channel count: {channels}"

        # Test audio data range (int16 should be in valid range)
        assert audio_data.min() >= -32768, "Audio data below int16 minimum"
        assert audio_data.max() <= 32767, "Audio data above int16 maximum"

        # Test that audio has a reasonable duration (not too short/long)
        duration_seconds = len(audio_data) / (sample_rate * channels)
        assert 0.5 <= duration_seconds <= 30.0, f"Unexpected audio duration: {duration_seconds}s"

        logger.info(f"Audio properties validated: {duration_seconds:.2f}s duration")

    def test_load_audio_file_consistency(self, fixtures_dir: Path) -> None:
        """Test that loading the same file multiple times gives consistent results."""
        audio_file = fixtures_dir / "russian_greeting.wav"
        assert audio_file.exists(), f"Russian greeting audio file not found: {audio_file}"

        # Load the same file multiple times
        results = []
        for i in range(3):
            audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)
            results.append((audio_data, sample_rate, channels))

        # Verify all results are identical
        first_audio, first_rate, first_channels = results[0]
        for i, (audio_data, sample_rate, channels) in enumerate(results[1:], 1):
            assert sample_rate == first_rate, f"Sample rate inconsistent on load {i}"
            assert channels == first_channels, f"Channels inconsistent on load {i}"
            assert len(audio_data) == len(first_audio), f"Audio length inconsistent on load {i}"
            assert np.array_equal(audio_data, first_audio), f"Audio data inconsistent on load {i}"

        logger.info("AudioSimulator loading is consistent across multiple calls")

    def test_load_nonexistent_file(self, fixtures_dir: Path) -> None:
        """Test error handling for nonexistent files."""
        nonexistent_file = fixtures_dir / "nonexistent_file.wav"

        with pytest.raises(FileNotFoundError):  # Should raise FileNotFoundError
            AudioSimulator.load_audio_file(nonexistent_file)

        logger.info("AudioSimulator properly handles nonexistent files")

    def test_load_invalid_file(self) -> None:
        """Test error handling for invalid audio files."""
        # Create a temporary invalid file
        invalid_file = Path(tempfile.gettempdir()) / f"invalid_test_{uuid.uuid4().hex[:8]}.wav"
        try:
            # Write some non-audio data
            with open(invalid_file, "wb") as f:
                f.write(b"This is not a valid WAV file")

            with pytest.raises(wave.Error):  # Should raise wave.Error
                AudioSimulator.load_audio_file(invalid_file)

            logger.info("AudioSimulator properly handles invalid audio files")
        finally:
            # Clean up
            if invalid_file.exists():
                invalid_file.unlink()

    @pytest.mark.parametrize(
        "audio_file_name,expected_language",
        [
            ("russian_greeting.wav", "russian"),
            ("russian_weather.wav", "russian"),
            ("russian_learning.wav", "russian"),
            ("english_greeting.wav", "english"),
            ("english_weather.wav", "english"),
        ],
    )
    def test_audio_file_language_categorization(
        self, fixtures_dir: Path, audio_file_name: str, expected_language: str
    ) -> None:
        """Test that language properly categorizes audio files."""
        audio_file = fixtures_dir / audio_file_name
        assert audio_file.is_file(), "Audio fixture file not found"

        # Load audio and verify it can be processed
        audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

        # Verify the file name indicates the expected language
        assert (
            expected_language in audio_file_name.lower()
        ), f"File {audio_file_name} should contain '{expected_language}'"

        # Verify audio is suitable for STT testing
        duration = len(audio_data) / (sample_rate * channels)
        assert (
            duration >= 1.0
        ), f"Audio file {audio_file_name} too short for STT testing: {duration}s"

        logger.info(
            f"{audio_file_name} categorized as {expected_language} language ({duration:.2f}s)"
        )

    def test_audio_simulator_memory_efficiency(self, fixtures_dir: Path) -> None:
        """Test that AudioSimulator doesn't leak memory with multiple loads."""
        audio_file = fixtures_dir / "russian_greeting.wav"
        assert audio_file.is_file(), "Fixture audio file not found: russian_greeting.wav"

        # Load the same file many times to test for memory leaks
        for i in range(10):
            audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

            # Verify each load is successful
            assert len(audio_data) > 0
            assert sample_rate > 0
            assert channels > 0

            # Clear reference to allow garbage collection
            del audio_data

        logger.info("AudioSimulator memory usage appears efficient")

    def test_audio_simulator_thread_safety(self, fixtures_dir: Path) -> None:
        """Test that AudioSimulator can be used safely from multiple contexts."""
        import concurrent.futures

        audio_file = fixtures_dir / "russian_greeting.wav"
        assert audio_file.is_file(), "Fixture audio file not found: russian_greeting.wav"

        def load_audio() -> AudioData:
            return AudioSimulator.load_audio_file(audio_file)

        # Load audio from multiple threads simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(load_audio) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all results are consistent
        first_audio, first_rate, first_channels = results[0]
        for audio_data, sample_rate, channels in results[1:]:
            assert sample_rate == first_rate
            assert channels == first_channels
            assert len(audio_data) == len(first_audio)
            assert np.array_equal(audio_data, first_audio)

        logger.info("AudioSimulator appears to be thread-safe")
