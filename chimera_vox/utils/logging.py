"""Logging setup using Rich."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)


def setup_logging(verbose: bool = False) -> None:
    """Configure root logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=_console, rich_tracebacks=True, show_path=verbose)],
        force=True,
    )


def get_console() -> Console:
    return _console
