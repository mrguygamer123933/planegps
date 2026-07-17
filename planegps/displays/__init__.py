"""Display backends (monitor / web, console, LED board)."""

from __future__ import annotations

from ..config import Config
from .base import Display


def create_display(cfg: Config) -> Display:
    """Factory: build the configured display backend."""
    backend = cfg.display.backend.lower()
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


__all__ = ["Display", "create_display"]
