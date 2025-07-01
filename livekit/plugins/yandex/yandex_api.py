"""Yandex Cloud SpeechKit API helpers using official SDK.

This module provides helper functions for working with the official Yandex Cloud
SpeechKit STT API v3.
"""

from typing import Any, Dict, List, Optional, Tuple

import grpc

# Import official Yandex Cloud protobuf definitions
from yandex.cloud.ai.stt.v3 import stt_pb2, stt_service_pb2_grpc

from ._utils import YandexCredentials
from .exceptions import YandexAuthenticationError, YandexConfigurationError


def create_streaming_options(  # pylint: disable=R0913
    language: Optional[str] = None,
    model: str = "general",
    detect_language: bool = False,
    interim_results: bool = True,
    profanity_filter: bool = False,
    sample_rate: int = 16000,
    audio_encoding: str = "LINEAR16_PCM",
) -> stt_pb2.StreamingOptions:
    """Create streaming options for Yandex SpeechKit STT API v3."""

    # Set up the audio format
    if audio_encoding == "LINEAR16_PCM":
        audio_encoding_enum = stt_pb2.RawAudio.LINEAR16_PCM
    else:
        audio_encoding_enum = stt_pb2.RawAudio.LINEAR16_PCM  # Default

    raw_audio = stt_pb2.RawAudio(
        audio_encoding=audio_encoding_enum, sample_rate_hertz=sample_rate, audio_channel_count=1
    )

    audio_format = stt_pb2.AudioFormatOptions(raw_audio=raw_audio)

    # Set up text normalization
    text_normalization = stt_pb2.TextNormalizationOptions(
        text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
        profanity_filter=profanity_filter,
        literature_text=False,
    )

    # Set up language restriction
    language_restriction = None
    if language and not detect_language:
        language_restriction = stt_pb2.LanguageRestrictionOptions(
            restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST, language_code=[language]
        )

    # Set up a recognition model
    recognition_model = stt_pb2.RecognitionModelOptions(
        audio_format=audio_format,
        text_normalization=text_normalization,
        audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME,
    )

    if language_restriction:
        recognition_model.language_restriction.CopyFrom(language_restriction)

    # Create streaming options
    streaming_options = stt_pb2.StreamingOptions(recognition_model=recognition_model)

    return streaming_options


def create_session_request(streaming_options: stt_pb2.StreamingOptions) -> stt_pb2.StreamingRequest:
    """Create a session request with streaming options."""
    return stt_pb2.StreamingRequest(session_options=streaming_options)


def create_audio_chunk(audio_data: bytes) -> stt_pb2.StreamingRequest:
    """Create audio chunk request."""
    chunk = stt_pb2.AudioChunk(data=audio_data)
    return stt_pb2.StreamingRequest(chunk=chunk)


def create_grpc_channel(endpoint: str = "stt.api.cloud.yandex.net:443") -> grpc.Channel:
    """Create a secure gRPC channel to Yandex Cloud."""
    credentials = grpc.ssl_channel_credentials()
    return grpc.secure_channel(endpoint, credentials)


def create_recognizer_stub(channel: grpc.Channel) -> stt_service_pb2_grpc.RecognizerStub:
    """Create recognizer stub from gRPC channel."""
    return stt_service_pb2_grpc.RecognizerStub(channel)


def create_grpc_metadata(credentials: YandexCredentials) -> List[Tuple[str, str]]:
    """Create gRPC metadata for authentication."""
    if not credentials.api_key:
        raise YandexAuthenticationError("API key is required for gRPC metadata")
    if not credentials.folder_id:
        raise YandexConfigurationError("Folder ID is required for gRPC metadata")

    return [
        ("authorization", f"Api-Key {credentials.api_key}"),
        ("x-folder-id", credentials.folder_id),
    ]


def parse_streaming_response(response: stt_pb2.StreamingResponse) -> Dict[str, Any]:
    """Parse streaming response into a standardized format."""
    result: Dict[str, Any] = {
        "event_type": None,
        "alternatives": [],
        "is_final": False,
        "confidence": 0.0,
        "start_time": 0.0,
        "end_time": 0.0,
    }

    # Determine an event type
    event_type = response.WhichOneof("Event")
    result["event_type"] = event_type

    if event_type == "partial" and len(response.partial.alternatives) > 0:
        # Interim results
        result["alternatives"] = [alt.text for alt in response.partial.alternatives]
        result["is_final"] = False
        if response.partial.alternatives:
            alt = response.partial.alternatives[0]
            result["confidence"] = getattr(alt, "confidence", 0.0)
            result["start_time"] = getattr(alt, "start_time_ms", 0) / 1000.0
            result["end_time"] = getattr(alt, "end_time_ms", 0) / 1000.0

    elif event_type == "final":
        # Final results
        result["alternatives"] = [alt.text for alt in response.final.alternatives]
        result["is_final"] = True
        if response.final.alternatives:
            alt = response.final.alternatives[0]
            result["confidence"] = getattr(alt, "confidence", 0.0)
            result["start_time"] = getattr(alt, "start_time_ms", 0) / 1000.0
            result["end_time"] = getattr(alt, "end_time_ms", 0) / 1000.0

    elif event_type == "final_refinement":
        # Final refinement results
        if hasattr(response.final_refinement, "normalized_text"):
            result["alternatives"] = [
                alt.text for alt in response.final_refinement.normalized_text.alternatives
            ]
        result["is_final"] = True

    elif event_type == "eou_update":
        # End of utterance - keep the original event type
        pass

    elif event_type == "status_code":
        # Status code update - add status_code as a separate field
        if hasattr(response, "status_code") and hasattr(response.status_code, "code_type"):
            result["status_code"] = response.status_code.code_type

    return result
