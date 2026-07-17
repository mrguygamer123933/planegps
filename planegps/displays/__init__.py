"""Display backends (monitor / web, console, LED board)."""

from __future__ import annotations

import re

from ..config import Config
from .base import Display


def _make_one(cfg: Config, backend: str) -> Display:
    backend = backend.lower()
    if backend in ("web", "monitor"):
        from .web import WebDisplay

        return WebDisplay(cfg)
    if backend == "console":
        from .console import ConsoleDisplay

        return ConsoleDisplay(cfg)
    if backend == "led":
        from .led_matrix import LedMatrixDisplay

        return LedMatrixDisplay(cfg)
    raise ValueError(f"Unknown display backend: {backend!r}")


def create_display(cfg: Config) -> Display:
    """Build the configured display backend(s).

    ``display.backend`` may list several backends separated by ``,`` or ``+``
    (e.g. ``web,led``) to drive them simultaneously.
    """
    backends = [b for b in re.split(r"[,+]", cfg.display.backend) if b.strip()]
    if not backends:
        raise ValueError("No display backend configured")
    if len(backends) == 1:
        return _make_one(cfg, backends[0])

    from .multi import MultiDisplay

    return MultiDisplay(cfg, [_make_one(cfg, b) for b in backends])


__all__ = ["Display", "create_display"]
