"""Validation utilities for agent E2E tests.

This module contains validation functions and utility classes
"""

import asyncio
import logging
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, NamedTuple, Optional

import numpy as np

if TYPE_CHECKING:
    from livekit.plugins.yandex.stt import SpeechStream

logger = logging.getLogger(__name__)


class AudioData(NamedTuple):
    """Named tuple for audio file data with clear field names.

    Attributes:
        audio_data: NumPy array containing audio samples as int16 values
        sample_rate: Audio sampling frequency in Hz (e.g., 16000, 44100)
        channels: Number of audio channels (1 for mono, 2 for stereo)
    """

    audio_data: np.ndarray[Any, np.dtype[np.int16]]
    sample_rate: int
    channels: int


def validate_russian_transcription(
    transcription: str, expected_keywords: Optional[List[str]] = None
) -> bool:
    """Validate that the transcription contains Russian text and expected keywords."""
    if not transcription or not transcription.strip():
        return False

    # Check for Cyrillic characters (Russian text)
    has_cyrillic = any("\u0400" <= char <= "\u04ff" for char in transcription)
    if not has_cyrillic:
        logger.warning(f"No Cyrillic characters found in: '{transcription}'")
        return False

    # Check for expected keywords if provided
    if expected_keywords:
        transcription_lower = transcription.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in transcription_lower]

        if not found_keywords:
            logger.warning(f"No expected keywords {expected_keywords} found in: '{transcription}'")
            return False

        logger.info(f"Found keywords {found_keywords} in transcription")

    return True


def validate_expected_transcription(
    actual_transcription: str,
    expected_text: str,
    expected_keywords: List[str],
    description: str = "transcription",
) -> bool:
    """Validate transcription against expected results with word overlap analysis."""
    logger.info(f"Validating {description}: '{actual_transcription}'")

    # Basic Russian validation with expected keywords
    if not validate_russian_transcription(actual_transcription, expected_keywords):
        return False

    # Check similarity to the expected text (allowing for minor variations)
    actual_lower = actual_transcription.lower().strip()
    expected_lower = expected_text.lower().strip()

    # Simple word overlap check (at least 50% of expected words should be present)
    expected_words = set(expected_lower.split())
    actual_words = set(actual_lower.split())

    if expected_words:
        overlap = len(expected_words.intersection(actual_words))
        overlap_ratio = overlap / len(expected_words)

        logger.info(f"Word overlap: {overlap}/{len(expected_words)} ({overlap_ratio:.2%})")

        if overlap_ratio >= 0.5:  # At least 50% word overlap
            logger.info(f"{description} validation passed")
            return True
        else:
            logger.warning(f"{description} validation failed - insufficient word overlap")
            return False

    return True


class AudioSimulator:
    """Helper class for processing real audio files in agent tests."""

    @staticmethod
    def load_audio_file(audio_file: Path) -> AudioData:
        """Load REAL audio file and return structured audio data.

        Args:
            audio_file: Path to the WAV audio file to load

        Returns:
            AudioData: Named tuple containing audio_data (np.ndarray),
                      sample_rate (int), and channels (int)

        Raises:
            FileNotFoundError: If the audio file doesn't exist
            wave.Error: If the file is not a valid WAV file
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        with wave.open(str(audio_file), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())

            # Convert to a numpy array
            audio_data = np.frombuffer(frames, dtype=np.int16)

            logger.info(
                f"Loaded REAL audio: {audio_file.name} - {sample_rate}Hz, "
                f"{channels} channels, {len(audio_data)} samples"
            )
            return AudioData(audio_data, sample_rate, channels)


async def collect_transcriptions(
    stt_stream: "SpeechStream", timeout: float = 10.0, expected_transcriptions: int = 1
) -> List[str]:
    """Collect transcription results from the STT stream with timeout."""
    transcriptions = []

    async def collect_task() -> None:
        async for event in stt_stream:
            if hasattr(event, "type") and event.type == "final_transcript":
                if hasattr(event, "alternatives") and event.alternatives:
                    text = event.alternatives[0].text
                    transcriptions.append(text)
                    logger.info(f"Transcription received: '{text}'")

                    if len(transcriptions) >= expected_transcriptions:
                        break

    await asyncio.wait_for(collect_task(), timeout=timeout)

    return transcriptions
