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

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Union

from livekit import rtc


@dataclass
class YandexCredentials:
    """Yandex Cloud authentication credentials."""

    api_key: Union[str, None] = None
    folder_id: Union[str, None] = None

    @classmethod
    def from_env(cls) -> "YandexCredentials":
        """Create credentials from environment variables.

        Returns:
            YandexCredentials instance
        """
        return cls(
            api_key=os.environ.get("YANDEX_API_KEY"),
            folder_id=os.environ.get("YANDEX_FOLDER_ID"),
        )


def convert_audio_frame_to_pcm(frame: rtc.AudioFrame) -> bytes:
    """Convert LiveKit AudioFrame to LINEAR16_PCM format for Yandex SpeechKit."""
    # Handle FlushSentinel - a special marker object sent by LiveKit agents framework
    # to signal the end of an audio stream. It's not a real audio frame, so we return
    # empty bytes to indicate no audio data should be processed.
    # We check by class name to avoid importing internal LiveKit types.
    if hasattr(frame, "__class__") and "FlushSentinel" in frame.__class__.__name__:
        return b""  # Return empty bytes for flush sentinel

    # Check if a frame has required attributes
    if not hasattr(frame, "sample_rate") or not hasattr(frame, "data"):
        return b""  # Return empty bytes for invalid frames

    # Ensure the audio is in the correct format (16-bit PCM, little-endian)
    # Yandex expects LINEAR16_PCM format
    # Note: Sample rate conversion should be handled before calling the plugin
    if frame.sample_rate != 16000:
        raise NotImplementedError(
            f"Sample rate conversion not implemented. Expected 16000 Hz, "
            f"got {frame.sample_rate} Hz. Please convert audio to 16000 Hz before calling the plugin."
        )

    # Convert numpy array to bytes
    # The frame.data is already in the correct format for most cases
    return frame.data.tobytes()


def validate_language_code(language: str) -> str:
    """Validate and normalize language code for Yandex SpeechKit."""
    # Map common language codes to Yandex format
    language_mapping = {
        "ru": "ru-RU",
        "en": "en-US",
        "russian": "ru-RU",
        "english": "en-US",
    }

    normalized = language_mapping.get(language.lower(), language)
    return normalized


class PeriodicCollector:
    """Utility class for collecting periodic statistics."""

    def __init__(self, callback: Callable[[Any], None], duration: float):
        self._callback = callback
        self._duration = duration
        self._task: Union[asyncio.Task[None], None] = None
        self._data: List[Any] = []
        self._start_time = time.time()

    def start(self) -> None:
        """Start the periodic collection."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        """Stop the periodic collection."""
        if self._task and not self._task.done():
            self._task.cancel()

    def add_data(self, data: Any) -> None:
        """Add data to the collection."""
        self._data.append(data)

    async def _run(self) -> None:
        """Run the periodic collection loop."""
        try:
            while True:
                await asyncio.sleep(self._duration)
                if self._data:
                    self._callback(self._data.copy())
                    self._data.clear()
        except asyncio.CancelledError:
            pass


def create_grpc_metadata(credentials: YandexCredentials) -> list[tuple[str, str]]:
    """Create gRPC metadata for authentication."""
    metadata = []

    if credentials.api_key:
        metadata.append(("authorization", f"Api-Key {credentials.api_key}"))

    if credentials.folder_id:
        metadata.append(("x-folder-id", credentials.folder_id))

    return metadata
