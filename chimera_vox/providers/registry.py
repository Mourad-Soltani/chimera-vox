"""Provider registry and fallback chain builder."""

from __future__ import annotations

from chimera_vox.errors import ConfigError
from chimera_vox.providers.base import Provider
from chimera_vox.providers.cogvideox import CogVideoXProvider
from chimera_vox.providers.ltx_turbo import LTXTurboProvider
from chimera_vox.providers.wan_animate import WanAnimateProvider

_REGISTRY: dict[str, type[Provider]] = {
    "ltx": LTXTurboProvider,
    "cogvideox": CogVideoXProvider,
    "wan": WanAnimateProvider,
}


def build_provider_chain(
    names: list[str], hf_token: str | None = None
) -> list[Provider]:
    """Instantiate providers in the given order."""
    chain: list[Provider] = []
    for name in names:
        key = name.strip().lower()
        if key not in _REGISTRY:
            raise ConfigError(
                f"Unknown provider '{name}'. Choose from: {', '.join(_REGISTRY)}"
            )
        chain.append(_REGISTRY[key](hf_token=hf_token))
    return chain


def available_provider_names() -> list[str]:
    return list(_REGISTRY.keys())
