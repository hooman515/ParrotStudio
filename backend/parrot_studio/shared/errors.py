from __future__ import annotations

from dataclasses import dataclass


class ParrotError(Exception):
    code = "PARROT_ERROR"

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class MissingAPIKeyError(ParrotError):
    code = "API_KEY_MISSING"


class ProviderUnavailableError(ParrotError):
    code = "PROVIDER_UNAVAILABLE"


class RateLimitError(ParrotError):
    code = "RATE_LIMIT"


class NetworkFailureError(ParrotError):
    code = "NETWORK_FAILURE"


class NoAudioDetectedError(ParrotError):
    code = "NO_AUDIO_DETECTED"


@dataclass
class ErrorInfo:
    code: str
    message: str
    retryable: bool = False


def error_info(exc: Exception) -> ErrorInfo:
    if isinstance(exc, ParrotError):
        return ErrorInfo(exc.code, exc.message, exc.retryable)
    return ErrorInfo("INTERNAL_ERROR", str(exc), False)
