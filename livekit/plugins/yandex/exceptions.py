"""Basic custom exceptions for Yandex SpeechKit STT plugin."""

from livekit.agents import APIConnectionError, APIStatusError, APITimeoutError


class YandexSTTError(Exception):
    """Base exception for Yandex SpeechKit STT errors."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class YandexAuthenticationError(YandexSTTError, APIConnectionError):
    """Authentication errors (invalid API key, missing credentials)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=False)


class YandexNetworkError(YandexSTTError, APIConnectionError):
    """Network errors (connection timeout, DNS resolution)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=True)


class YandexAPIError(YandexSTTError, APIStatusError):
    """API errors (rate limits, service unavailable)."""

    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message, retryable=retryable)


class YandexTimeoutError(YandexSTTError, APITimeoutError):
    """Timeout errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=True)


class YandexAudioFormatError(YandexSTTError):
    """Audio format errors (unsupported sample rate, invalid encoding)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=False)


class YandexConfigurationError(YandexSTTError):
    """Configuration errors (missing credentials, invalid settings)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=False)
