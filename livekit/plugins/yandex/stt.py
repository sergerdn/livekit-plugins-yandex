"""Yandex SpeechKit STT implementation for LiveKit Agents."""

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

from __future__ import annotations

import asyncio
import logging
import weakref
from dataclasses import dataclass
from typing import Any, Union

import aiohttp
import grpc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    stt,
    utils,
)
from livekit.agents.types import NOT_GIVEN, NotGivenOr
from livekit.agents.utils import AudioBuffer, is_given
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yandex.cloud.ai.stt.v3 import stt_pb2

from livekit import rtc

from ._utils import YandexCredentials, convert_audio_frame_to_pcm
from .exceptions import (
    YandexAPIError,
    YandexAudioFormatError,
    YandexAuthenticationError,
    YandexConfigurationError,
    YandexNetworkError,
    YandexTimeoutError,
)
from .log import log_timing, log_with_context, logger
from .models import YandexSTTLanguages, YandexSTTModels
from .yandex_api import (
    create_audio_chunk,
    create_grpc_metadata,
    create_session_request,
    create_streaming_options,
    parse_streaming_response,
)


@dataclass
class STTOptions:
    """Configuration options for Yandex SpeechKit STT."""

    model: str
    language: Union[str, None]
    detect_language: bool
    interim_results: bool
    profanity_filter: bool
    sample_rate: int
    audio_encoding: str
    folder_id: str
    grpc_endpoint: str


class STT(stt.STT[YandexSTTLanguages]):
    """Yandex SpeechKit Speech-to-Text implementation."""

    def __init__(
        self,
        *,
        model: Union[YandexSTTModels, str] = "general",
        language: Union[YandexSTTLanguages, str] = "ru-RU",
        detect_language: bool = False,
        interim_results: bool = True,
        profanity_filter: bool = False,
        sample_rate: int = 16000,
        api_key: Union[str, None] = None,
        folder_id: Union[str, None] = None,
        grpc_endpoint: str = "stt.api.cloud.yandex.net:443",
        http_session: Union[aiohttp.ClientSession, None] = None,
    ) -> None:
        """Create a new instance of Yandex SpeechKit STT.

        Args:
            model: Recognition model to use (default: "general")
            language: Language code for recognition (default: "ru-RU")
            detect_language: Enable automatic language detection (default: False)
            interim_results: Enable interim results (default: True)
            profanity_filter: Enable profanity filtering (default: False)
            sample_rate: Audio sample rate in Hz (default: 16000)
            api_key: Yandex Cloud API key
            folder_id: Yandex Cloud folder ID
            grpc_endpoint: gRPC endpoint for SpeechKit API
            http_session: Optional HTTP session for API requests

        Note:
            api_key and folder_id must be provided.
            These can also be set via environment variables:
            - YANDEX_API_KEY
            - YANDEX_FOLDER_ID
        """
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=True, interim_results=interim_results)
        )

        # Validate sample rate early
        if sample_rate not in [8000, 16000, 48000]:
            raise YandexAudioFormatError(
                f"Unsupported sample rate: {sample_rate}Hz. "
                "Supported rates: 8000, 16000, 48000 Hz"
            )

        # Get credentials from arguments or environment
        try:
            if api_key or folder_id:
                # Use provided arguments
                self._credentials = YandexCredentials(
                    api_key=api_key,
                    folder_id=folder_id,
                )
            else:
                # Load from environment
                self._credentials = YandexCredentials.from_env()
        except Exception as e:
            raise YandexConfigurationError(f"Failed to load credentials: {e}") from e

        if not self._credentials.folder_id:
            raise YandexConfigurationError(
                "Yandex Cloud folder_id is required. "
                "Set YANDEX_FOLDER_ID environment variable or pass folder_id parameter."
            )

        if not self._credentials.api_key:
            raise YandexAuthenticationError(
                "Yandex Cloud API key is required. "
                "Set YANDEX_API_KEY environment variable or pass api_key parameter."
            )

        log_with_context(
            logging.INFO,
            "Initialized Yandex STT",
            model=model,
            language=language,
            sample_rate=sample_rate,
            interim_results=interim_results,
        )

        self._opts = STTOptions(
            model=model,
            language=language if not detect_language else None,
            detect_language=detect_language,
            interim_results=interim_results,
            profanity_filter=profanity_filter,
            sample_rate=sample_rate,
            audio_encoding="LINEAR16_PCM",
            folder_id=self._credentials.folder_id,
            grpc_endpoint=grpc_endpoint,
        )

        self._session = http_session
        self._streams = weakref.WeakSet[SpeechStream]()

    def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists for token refresh operations."""
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[Union[YandexSTTLanguages, str]] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> stt.SpeechEvent:
        """Recognize speech from audio buffer (batch recognition).

        Note: This implementation uses streaming recognition internally
        as Yandex SpeechKit v3 primarily focuses on streaming.
        """
        # For batch recognition, we'll use the streaming API internally
        # and collect all results
        config = self._sanitize_options(language=language)

        try:
            # Create a temporary stream for batch processing
            stream = SpeechStream(
                stt=self,
                opts=config,
                conn_options=conn_options,
                credentials=self._credentials,
            )

            # Send all audio data
            combined_frame = rtc.combine_audio_frames(buffer)
            stream.push_frame(combined_frame)
            stream.flush()

            # Wait for final result
            final_event = None
            async for event in stream:
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    final_event = event
                    break

            await stream.aclose()

            if final_event:
                return final_event
            else:
                # Return an empty result if no transcription
                return stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[
                        stt.SpeechData(
                            text="",
                            language="",
                        )
                    ],
                )

        except Exception as e:
            if isinstance(e, (APIConnectionError, APIStatusError, APITimeoutError)):
                raise
            raise APIConnectionError() from e

    def stream(
        self,
        *,
        language: NotGivenOr[Union[YandexSTTLanguages, str]] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> SpeechStream:
        """Create a streaming transcription session."""
        config = self._sanitize_options(language=language)
        stream = SpeechStream(
            stt=self,
            opts=config,
            conn_options=conn_options,
            credentials=self._credentials,
        )
        self._streams.add(stream)
        return stream

    def _sanitize_options(
        self, *, language: NotGivenOr[Union[YandexSTTLanguages, str]] = NOT_GIVEN
    ) -> STTOptions:
        """Sanitize and validate options."""
        config = STTOptions(
            model=self._opts.model,
            language=self._opts.language,
            detect_language=self._opts.detect_language,
            interim_results=self._opts.interim_results,
            profanity_filter=self._opts.profanity_filter,
            sample_rate=self._opts.sample_rate,
            audio_encoding=self._opts.audio_encoding,
            folder_id=self._opts.folder_id,
            grpc_endpoint=self._opts.grpc_endpoint,
        )

        if is_given(language):
            config.language = language
            config.detect_language = False

        if config.detect_language:
            config.language = None

        return config


class SpeechStream(stt.SpeechStream):
    """Yandex SpeechKit streaming speech recognition."""

    def __init__(
        self,
        *,
        stt: STT,
        opts: STTOptions,
        conn_options: APIConnectOptions,
        credentials: YandexCredentials,
    ) -> None:
        super().__init__(stt=stt, conn_options=conn_options, sample_rate=opts.sample_rate)

        self._opts = opts
        self._credentials = credentials
        self._grpc_channel: Union[grpc.aio.Channel, None] = None
        self._grpc_stub: Union[Any, None] = None
        self._stream_call = None
        self._closed = False
        self._session_started = False

        logger.info("Initializing Yandex SpeechKit streaming session")

    async def _run(self) -> None:
        """Required abstract method implementation."""
        await self._main_task()

    async def _main_task(self) -> None:
        """Main streaming task with gRPC implementation."""
        session_id = id(self)

        with log_timing("streaming_session", session_id=session_id):
            try:
                log_with_context(
                    logging.INFO,
                    "Starting Yandex SpeechKit streaming session",
                    session_id=session_id,
                    language=self._opts.language,
                    model=self._opts.model,
                    sample_rate=self._opts.sample_rate,
                )

                # Create gRPC channel with extended timeout and keepalive options
                await self._create_grpc_connection()

                # Create metadata for authentication
                metadata = create_grpc_metadata(self._credentials)

                # Start streaming session with retry logic
                await self._start_streaming_session_with_retry(metadata, session_id)

            except grpc.RpcError as e:
                self._handle_grpc_error(e, session_id)
            except Exception as e:
                log_with_context(
                    logging.ERROR,
                    f"Unexpected error in streaming task: {e}",
                    session_id=session_id,
                    error_type=type(e).__name__,
                )
                raise YandexAPIError(f"Streaming session failed: {e}") from e

    async def _create_grpc_connection(self) -> None:
        """Create gRPC connection with proper configuration."""
        try:
            channel_options = [
                ("grpc.keepalive_time_ms", 60000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_time_between_pings_ms", 30000),
                ("grpc.http2.min_ping_interval_without_data_ms", 300000),
                ("grpc.max_receive_message_length", 4 * 1024 * 1024),
                ("grpc.max_send_message_length", 4 * 1024 * 1024),
            ]

            self._grpc_channel = grpc.aio.secure_channel(
                self._opts.grpc_endpoint, grpc.ssl_channel_credentials(), options=channel_options
            )

            # Create gRPC stub - import the stub class directly for async channels
            from yandex.cloud.ai.stt.v3 import stt_service_pb2_grpc

            self._grpc_stub = stt_service_pb2_grpc.RecognizerStub(self._grpc_channel)

            log_with_context(
                logging.DEBUG,
                f"Created gRPC connection to {self._opts.grpc_endpoint}",
                endpoint=self._opts.grpc_endpoint,
            )

        except Exception as e:
            raise YandexNetworkError(f"Failed to create gRPC connection: {e}") from e

    def _handle_grpc_error(self, error: grpc.RpcError, session_id: int) -> None:
        """Handle gRPC errors with specific exception types."""
        code = error.code()
        details = error.details()

        log_with_context(
            logging.ERROR,
            f"gRPC error: {code.name} - {details}",
            session_id=session_id,
            grpc_code=code.name,
        )

        if code == grpc.StatusCode.UNAUTHENTICATED:
            raise YandexAuthenticationError(f"Authentication failed: {details}") from error
        elif code == grpc.StatusCode.UNAVAILABLE:
            raise YandexNetworkError(f"Service unavailable: {details}") from error
        elif code == grpc.StatusCode.DEADLINE_EXCEEDED:
            raise YandexTimeoutError(f"Request timeout: {details}") from error
        elif code == grpc.StatusCode.RESOURCE_EXHAUSTED:
            raise YandexAPIError(f"Rate limit exceeded: {details}", retryable=True) from error
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            raise YandexAPIError(f"Invalid request: {details}", retryable=False) from error
        elif code == grpc.StatusCode.INTERNAL and details and "RST_STREAM" in details:
            # Handle connection reset as a retryable network error
            raise YandexNetworkError(f"Connection reset: {details}") from error
        else:
            raise YandexAPIError(f"gRPC error {code.name}: {details}") from error

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((YandexNetworkError, YandexTimeoutError)),
    )
    async def _start_streaming_session_with_retry(
        self, metadata: list[tuple[str, str]], session_id: int
    ) -> None:
        """Start a streaming session with retry logic for transient failures."""
        try:
            await self._start_streaming_session(metadata, session_id)
        except (YandexNetworkError, YandexTimeoutError) as e:
            log_with_context(
                logging.WARNING,
                f"Retryable error in streaming session: {e}",
                session_id=session_id,
                retryable=e.retryable,
            )
            raise

    async def _start_streaming_session(
        self, metadata: list[tuple[str, str]], session_id: int
    ) -> None:
        """Start the gRPC streaming session."""
        try:
            # Create streaming options
            streaming_opts = create_streaming_options(
                language=self._opts.language,
                model=self._opts.model,
                detect_language=self._opts.detect_language,
                interim_results=self._opts.interim_results,
                profanity_filter=self._opts.profanity_filter,
                sample_rate=self._opts.sample_rate,
                audio_encoding=self._opts.audio_encoding,
            )

            # Create request iterator
            request_iterator = self._create_request_iterator(streaming_opts)

            # Start streaming call with a 1-hour timeout for long-running agent sessions
            if not self._grpc_stub:
                raise YandexAPIError("gRPC stub not initialized")

            streaming_timeout = 3600.0  # 1 hour for long-running agent sessions
            self._stream_call = self._grpc_stub.RecognizeStreaming(
                request_iterator,
                metadata=metadata,
                timeout=streaming_timeout,
            )

            log_with_context(
                logging.DEBUG,
                "Started gRPC streaming call",
                session_id=session_id,
                timeout=streaming_timeout,
            )

            # Process responses
            response_count = 0
            if self._stream_call:
                async for response in self._stream_call:
                    response_count += 1
                    await self._process_response(response, session_id)

            log_with_context(
                logging.INFO,
                "Streaming session completed normally",
                session_id=session_id,
                responses_processed=response_count,
            )

        except grpc.RpcError:
            # Let the main task handle gRPC errors
            raise
        except Exception as e:
            log_with_context(
                logging.ERROR,
                f"Error in streaming session: {e}",
                session_id=session_id,
                error_type=type(e).__name__,
            )
            raise
        finally:
            # Ensure we're marked as closed when streaming ends
            if not self._closed:
                log_with_context(
                    logging.DEBUG,
                    "Marking stream as closed after session end",
                    session_id=session_id,
                )
                self._closed = True

    async def _create_request_iterator(self, streaming_opts: Any) -> Any:
        """Create async iterator for streaming requests."""
        # Send session options first
        yield create_session_request(streaming_opts)
        self._session_started = True

        # Process audio frames from the input queue
        frame_count = 0
        while not self._closed:
            try:
                # Wait for an audio frame with timeout
                frame = await asyncio.wait_for(self._input_ch.recv(), timeout=0.1)

                if frame is None:
                    logger.debug("Received None frame, ending stream")
                    break

                # Check if this is a flush sentinel (end of stream marker)
                if hasattr(frame, "__class__") and "FlushSentinel" in frame.__class__.__name__:
                    logger.debug("Received flush sentinel, ending stream")
                    break

                # Convert frame to audio chunk with error handling
                try:
                    # Check if a frame is actually an AudioFrame before conversion
                    if hasattr(frame, "data") and hasattr(frame, "sample_rate"):
                        # Import AudioFrame type for proper type checking
                        from livekit import rtc

                        if isinstance(frame, rtc.AudioFrame):
                            # Convert LiveKit AudioFrame to PCM bytes for Yandex API
                            # This function also handles FlushSentinel (end-of-stream markers)
                            # by returning empty bytes when the stream ends
                            audio_data = convert_audio_frame_to_pcm(frame)
                            if audio_data:  # Only yield if we have actual audio data
                                yield create_audio_chunk(audio_data)
                                frame_count += 1

                        if frame_count % 100 == 0:  # Log every 100 frames
                            log_with_context(
                                logging.DEBUG,
                                f"Processed {frame_count} audio frames",
                                frame_count=frame_count,
                            )

                except Exception as e:
                    log_with_context(
                        logging.ERROR,
                        f"Failed to convert audio frame: {e}",
                        error_type=type(e).__name__,
                    )
                    # Continue processing other frames
                    continue

            except asyncio.TimeoutError:
                # No frame available, continue
                continue
            except Exception as e:
                # Check if it's a channel-closed error (expected during shutdown)
                if "ChanClosed" in str(type(e).__name__):
                    log_with_context(
                        logging.DEBUG,
                        "Input channel closed, stopping audio processing",
                        error_type=type(e).__name__,
                    )
                    break
                else:
                    log_with_context(
                        logging.ERROR,
                        f"Error processing audio frame: {e}",
                        frame_count=frame_count,
                        error_type=type(e).__name__,
                    )
                    break

        log_with_context(
            logging.DEBUG,
            "Request iterator finished",
            total_frames=frame_count,
        )

    async def _process_response(self, response: stt_pb2.StreamingResponse, session_id: int) -> None:
        """Process streaming response from Yandex SpeechKit."""
        try:
            # Parse response using the official API parser
            parsed = parse_streaming_response(response)
            event_type = parsed.get("event_type")

            log_with_context(
                logging.DEBUG,
                f"Processing response: {event_type}",
                session_id=session_id,
                event_type=event_type,
                has_alternatives=bool(parsed.get("alternatives")),
            )

            if event_type == "partial" and parsed["alternatives"]:
                # Interim results
                for text in parsed["alternatives"]:
                    event = stt.SpeechEvent(
                        type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                text=text,
                                language=self._opts.language or "ru-RU",
                                start_time=parsed["start_time"],
                                end_time=parsed["end_time"],
                                confidence=parsed["confidence"],
                            )
                        ],
                    )
                    self._event_ch.send_nowait(event)

                    log_with_context(
                        logging.DEBUG,
                        f"Sent interim result: {text[:50]}...",
                        session_id=session_id,
                        text_length=len(text),
                        confidence=parsed["confidence"],
                    )

            elif event_type == "final" and parsed["alternatives"]:
                # Final results
                for text in parsed["alternatives"]:
                    # Filter out empty transcriptions to avoid noise
                    if not text.strip():
                        log_with_context(
                            logging.DEBUG,
                            "Skipping empty final result",
                            session_id=session_id,
                            confidence=parsed["confidence"],
                        )
                        continue

                    event = stt.SpeechEvent(
                        type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                text=text,
                                language=self._opts.language or "ru-RU",
                                start_time=parsed["start_time"],
                                end_time=parsed["end_time"],
                                confidence=parsed["confidence"],
                            )
                        ],
                    )
                    self._event_ch.send_nowait(event)

                    log_with_context(
                        logging.INFO,
                        f"Sent final result: {text}",
                        session_id=session_id,
                        text_length=len(text),
                        confidence=parsed["confidence"],
                    )

            elif event_type == "end_of_utterance":
                # End of utterance
                event = stt.SpeechEvent(
                    type=stt.SpeechEventType.END_OF_SPEECH,
                    alternatives=[],
                )
                self._event_ch.send_nowait(event)

                log_with_context(
                    logging.DEBUG,
                    "Sent end of speech event",
                    session_id=session_id,
                )

        except Exception as e:
            log_with_context(
                logging.ERROR,
                f"Error processing response: {e}",
                session_id=session_id,
                error_type=type(e).__name__,
            )

    async def aclose(self) -> None:
        """Close the streaming session."""
        if self._closed:
            return

        self._closed = True
        logger.info("Closing Yandex SpeechKit streaming session")

        try:
            if self._stream_call:
                # For gRPC async generators, we need to close them properly
                if hasattr(self._stream_call, "cancel"):
                    self._stream_call.cancel()
                elif hasattr(self._stream_call, "aclose"):
                    await self._stream_call.aclose()
                # For async generators, we just need to let them finish naturally

            if self._grpc_channel:
                await self._grpc_channel.close(grace=None)
        except Exception as e:
            logger.warning(f"Error closing gRPC resources: {e}")

        await super().aclose()
