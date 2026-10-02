"""Retry helper with exponential backoff + jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

from chimera_vox.constants import MAX_RETRIES, RETRY_BASE_DELAY, RETRY_MAX_DELAY

T = TypeVar("T")
log = logging.getLogger(__name__)


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    label: str = "operation",
) -> T:
    """Call an async function with exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == max_retries:
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(0, delay * 0.3)  # jitter
            log.warning(
                "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                label,
                attempt,
                max_retries,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
    if last_exc is None:
        raise RuntimeError("retry_async completed without result or exception")
    raise last_exc
