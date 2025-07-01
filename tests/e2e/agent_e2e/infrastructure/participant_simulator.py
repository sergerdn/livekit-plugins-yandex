"""Participant Simulation for LiveKit Agent Testing.

This module provides utilities for simulating real participants joining LiveKit rooms
and publishing audio tracks from test fixture files.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from livekit import rtc

from ..validation_utils import AudioSimulator

logger = logging.getLogger("participant-simulator")


class ParticipantSimulator:
    """Simulates a real participant joining LiveKit rooms and speaking."""

    def __init__(self, room: rtc.Room, participant_identity: str) -> None:
        """Initialize participant simulator.

        Args:
            room: Connected LiveKit room
            participant_identity: Identity of this participant
        """
        self.room = room
        self.participant_identity = participant_identity
        self._audio_source: Optional[rtc.AudioSource] = None
        self._audio_track: Optional[rtc.LocalAudioTrack] = None
        self._is_publishing = False
        self._participant_thread: Optional[threading.Thread] = None
        self._participant_loop: Optional[asyncio.AbstractEventLoop] = None

    def start_speaking_in_thread(self, audio_file: Path, loop: bool = False) -> None:
        """Start speaking in a separate thread to avoid event loop conflicts."""
        if self._participant_thread and self._participant_thread.is_alive():
            logger.warning(f"Participant {self.participant_identity} thread already running")
            return

        logger.info(f"Starting participant {self.participant_identity} in separate thread")

        def run_participant() -> None:
            """Run participant in its own event loop."""
            # Create a new event loop for this thread
            self._participant_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._participant_loop)

            try:
                # Run the async speaking method
                logger.info(f"Running participant thread for {audio_file.name}")
                self._participant_loop.run_until_complete(
                    self._async_start_speaking_threaded(audio_file, loop)
                )
                logger.info("Participant thread completed successfully")
            finally:
                self._participant_loop.close()

        # Start thread
        self._participant_thread = threading.Thread(target=run_participant, daemon=True)
        self._participant_thread.start()

    async def _async_start_speaking_threaded(self, audio_file: Path, loop: bool = False) -> None:
        """Threaded version of start speaking that handles audio streaming in the
        thread."""
        if self._is_publishing:
            logger.warning(f"Participant {self.participant_identity} is already speaking")
            return

        logger.info(f"Participant {self.participant_identity} starting to speak: {audio_file.name}")

        # Load audio file
        audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

        # Create an audio source and track
        logger.info(f"Creating audio source: {sample_rate}Hz, {channels} channels")
        self._audio_source = rtc.AudioSource(sample_rate, channels)
        self._audio_track = rtc.LocalAudioTrack.create_audio_track(
            "participant-audio", self._audio_source
        )

        # Publish the audio track with generous timeout for live tests
        logger.info("Publishing audio track to room...")

        publication = await asyncio.wait_for(
            self.room.local_participant.publish_track(
                self._audio_track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
            ),
            timeout=30.0,  # Generous timeout for live network conditions
        )

        logger.info(f"Audio track published: {publication.sid}")
        self._is_publishing = True

        # Stream audio data directly in this thread
        logger.info("Starting audio streaming in thread...")
        await self._stream_audio_data_threaded(audio_data, sample_rate, channels, loop)
        logger.info("Audio streaming completed in thread")

    async def _stream_audio_data_threaded(
        self,
        audio_data: np.ndarray[np.int16],
        sample_rate: int,
        channels: int,
        loop: bool = False,
    ) -> None:
        """Threaded version of audio streaming that runs in the participant thread."""
        logger.info(
            f"Starting threaded audio streaming: {len(audio_data)} samples, "
            f"{sample_rate}Hz, {channels} channels"
        )

        if not self._audio_source:
            logger.error("No audio source available for streaming!")
            return

        # Calculate chunk size for real-time streaming (100ms chunks)
        chunk_duration = 0.1  # 100ms
        chunk_size = int(sample_rate * chunk_duration * channels)

        logger.info(f"Streaming audio in {chunk_size} sample chunks ({chunk_duration * 1000}ms)")

        while self._is_publishing:
            # Stream audio in chunks
            for i in range(0, len(audio_data), chunk_size):
                if not self._is_publishing:
                    break

                chunk = audio_data[i : i + chunk_size]

                # Pad last chunk if necessary
                if len(chunk) < chunk_size:
                    padding = np.zeros(chunk_size - len(chunk), dtype=np.int16)
                    chunk = np.concatenate([chunk, padding])

                # Create audio frame
                frame = rtc.AudioFrame(
                    data=chunk.tobytes(),
                    sample_rate=sample_rate,
                    num_channels=channels,
                    samples_per_channel=len(chunk) // channels,
                )

                # Debug: Check if audio has content
                if i < 5:  # Log first few chunks
                    chunk_rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    logger.info(
                        f"Publishing chunk {i // chunk_size + 1}: {len(chunk)} samples, RMS: {chunk_rms:.1f}"
                    )

                # Capture audio to source
                await self._audio_source.capture_frame(frame)

                # Wait for real-time playback
                await asyncio.sleep(chunk_duration)

            # If not looping, stop after one playback
            if not loop:
                break

            logger.info("Looping audio playback...")

        logger.info("Threaded audio streaming completed")

    async def _async_start_speaking(self, audio_file: Path, loop: bool = False) -> None:
        """Start publishing audio from a file as if the participant is speaking (async
        version).

        Args:
            audio_file: Path to an audio file to publish
            loop: Whether to loop the audio continuously
        """
        if self._is_publishing:
            logger.warning(f"Participant {self.participant_identity} is already speaking")
            return

        logger.info(f"Participant {self.participant_identity} starting to speak: {audio_file.name}")

        # Load audio file
        audio_data, sample_rate, channels = AudioSimulator.load_audio_file(audio_file)

        # Create an audio source and track
        logger.info(f"Creating audio source: {sample_rate}Hz, {channels} channels")
        self._audio_source = rtc.AudioSource(sample_rate, channels)
        self._audio_track = rtc.LocalAudioTrack.create_audio_track(
            "participant-audio", self._audio_source
        )

        # Publish the audio track with timeout
        logger.info("Publishing audio track to room...")

        publication = await asyncio.wait_for(
            self.room.local_participant.publish_track(
                self._audio_track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
            ),
            timeout=10.0,  # 10-second timeout
        )

        logger.info(f"Audio track published: {publication.sid}")
        self._is_publishing = True

        # Start streaming audio data (await it directly instead of creating a task)
        logger.info("Starting audio streaming...")
        await self._stream_audio_data(audio_data, sample_rate, channels, loop)
        logger.info("Audio streaming completed")

    async def start_speaking(self, audio_file: Path, loop: bool = False) -> None:
        """Alias for _async_start_speaking for backward compatibility."""
        await self._async_start_speaking(audio_file, loop)

    async def stop_speaking(self) -> None:
        """Stop publishing audio."""
        if not self._is_publishing:
            return

        logger.info(f"Participant {self.participant_identity} stopping speaking")

        if self._audio_track:
            await self.room.local_participant.unpublish_track(self._audio_track.sid)
            self._audio_track = None

        if self._audio_source:
            self._audio_source = None
        self._is_publishing = False

    async def _stream_audio_data(
        self,
        audio_data: np.ndarray[np.int16],
        sample_rate: int,
        channels: int,
        loop: bool = False,
    ) -> None:
        """Stream audio data to the audio source.

        Args:
            audio_data: Audio data to stream
            sample_rate: Sample rate of audio
            channels: Number of audio channels
            loop: Whether to loop the audio
        """
        logger.info(
            f"Starting audio streaming: {len(audio_data)} samples, {sample_rate}Hz, {channels} channels"
        )

        if not self._audio_source:
            logger.error("No audio source available for streaming!")
            return

        # Calculate chunk size for real-time streaming (100ms chunks)
        chunk_duration = 0.1  # 100ms
        chunk_size = int(sample_rate * chunk_duration * channels)

        logger.info(f"Streaming audio in {chunk_size} sample chunks ({chunk_duration * 1000}ms)")

        while self._is_publishing:
            # Stream audio in chunks
            for i in range(0, len(audio_data), chunk_size):
                if not self._is_publishing:
                    break

                chunk = audio_data[i : i + chunk_size]

                # Pad last chunk if necessary
                if len(chunk) < chunk_size:
                    padding = np.zeros(chunk_size - len(chunk), dtype=np.int16)
                    chunk = np.concatenate([chunk, padding])

                # Create audio frame
                frame = rtc.AudioFrame(
                    data=chunk.tobytes(),
                    sample_rate=sample_rate,
                    num_channels=channels,
                    samples_per_channel=len(chunk) // channels,
                )

                # Debug: Check if audio has content
                if i < 5:  # Log first few chunks
                    chunk_rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    logger.info(
                        f"Publishing chunk {i + 1}: {len(chunk)} samples, RMS: {chunk_rms:.1f}"
                    )

                # Capture audio to source
                await self._audio_source.capture_frame(frame)

                # Wait for real-time playback
                await asyncio.sleep(chunk_duration)

            # If not looping, stop after one playback
            if not loop:
                break

            logger.info("Looping audio playback...")

        logger.info("Audio streaming completed")

    async def join_room_and_speak(
        self,
        audio_file: Path,
        duration: Optional[float] = None,
        loop: bool = False,
    ) -> None:
        """Convenience method to join a room and start speaking.

        Args:
            audio_file: Audio file to play
            duration: How long to speak (None = play a file once)
            loop: Whether to loop audio continuously
        """
        logger.info(
            f"Participant {self.participant_identity} joining room and speaking: {audio_file.name}"
        )

        # Start speaking
        await self.start_speaking(audio_file, loop=loop)

        # Wait for a specified duration or until audio completes
        if duration:
            await asyncio.sleep(duration)
            await self.stop_speaking()
        elif not loop:
            # Calculate audio duration and wait for it to complete
            audio_data, sample_rate, _ = AudioSimulator.load_audio_file(audio_file)
            audio_duration = len(audio_data) / sample_rate
            await asyncio.sleep(audio_duration + 1.0)  # +1s buffer

    async def wait_for_audio_completion(self, audio_file: Path) -> None:
        """Wait for an audio file to complete playing.

        Args:
            audio_file: Audio file being played
        """
        # Calculate audio duration
        audio_data, sample_rate, _ = AudioSimulator.load_audio_file(audio_file)
        audio_duration = len(audio_data) / sample_rate

        total_wait = audio_duration + 2.0
        logger.info(
            f"Waiting {audio_duration:.1f}s for audio completion + 2.0s buffer = {total_wait:.1f}s total"
        )
        await asyncio.sleep(total_wait)  # +2s buffer for live tests

    @property
    def is_speaking(self) -> bool:
        """Check if the participant is currently speaking."""
        return self._is_publishing

    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """Wait for the participant thread to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if thread completed, False if timeout
        """
        if self._participant_thread:
            self._participant_thread.join(timeout)
            return not self._participant_thread.is_alive()
        return True

    def stop_thread(self) -> None:
        """Stop the participant thread."""
        if self._participant_loop and self._participant_loop.is_running():
            # Schedule stop in the participant's event loop
            asyncio.run_coroutine_threadsafe(self.stop_speaking(), self._participant_loop)

    async def cleanup(self) -> None:
        """Clean up participant resources."""
        logger.info(f"Cleaning up participant {self.participant_identity}")

        # Stop a thread if running
        self.stop_thread()

        # Wait for the thread to complete (generous timeout for live tests)
        if self._participant_thread:
            self._participant_thread.join(timeout=15.0)  # Increased for live tests

        await self.stop_speaking()
