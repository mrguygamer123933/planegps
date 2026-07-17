"""Abstract display backend."""

from __future__ import annotations

import abc

from ..config import Config
from ..models import DetectionState


class Display(abc.ABC):
    """Base class for output backends.

    The application calls :meth:`start` once, then :meth:`render` on every
    detection cycle, and :meth:`stop` on shutdown. Some backends (e.g. web)
    keep a long-lived server running in the background and simply cache the
    latest state on ``render``.
    """

    name: str = "base"

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    def start(self) -> None:  # pragma: no cover - optional hook
        """Called once before the first render."""

    @abc.abstractmethod
    def render(self, state: DetectionState) -> None:
        """Present the latest detection state."""
        raise NotImplementedError

    def stop(self) -> None:  # pragma: no cover - optional hook
        """Called once on shutdown."""

    def blocks(self) -> bool:
        """Whether the main thread should idle-loop after starting.

        Web keeps a server thread alive; console/LED just render per cycle.
        Both return True here because the app owns the poll loop; the flag is
        reserved for future backends that take over the main thread.
        """
        return False
