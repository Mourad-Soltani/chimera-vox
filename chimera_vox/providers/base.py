"""Abstract provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProviderResult:
    """Result of a single clip generation."""

    path: Path
    duration: float
    provider_name: str


@dataclass
class ProviderHealth:
    """Health status for a provider."""

    reachable: bool
    message: str


class Provider(ABC):
    """Base class for video generation providers."""

    name: str

    def __init__(self, hf_token: str | None = None) -> None:
        self.hf_token = hf_token

    @abstractmethod
    async def generate_clip(
        self,
        image: Path,
        prompt: str,
        duration: float,
    ) -> ProviderResult:
        """Generate a video clip from an image + prompt."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check whether the provider Space is reachable."""
