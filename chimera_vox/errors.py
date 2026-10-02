"""Custom exceptions for ChimeraVox."""


class ChimeraVoxError(Exception):
    """Base exception."""


class ConfigError(ChimeraVoxError):
    """Invalid configuration."""


class HealthCheckError(ChimeraVoxError):
    """Pre-flight health check failed."""


class ProviderError(ChimeraVoxError):
    """A video provider failed."""


class AllProvidersFailedError(ChimeraVoxError):
    """Every provider in the fallback chain failed."""


class TTSGenerationError(ChimeraVoxError):
    """TTS generation failed."""


class StitchingError(ChimeraVoxError):
    """Video stitching failed."""


class UpscalingError(ChimeraVoxError):
    """Upscaling failed."""


class FFmpegError(ChimeraVoxError):
    """FFmpeg binary or subprocess error."""
