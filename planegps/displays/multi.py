"""Fan-out display that drives several backends at once (e.g. web + LED)."""

from __future__ import annotations

from ..config import Config
from ..models import DetectionState
from .base import Display


class MultiDisplay(Display):
    """Wraps multiple displays; forwards every lifecycle call to each."""

    def __init__(self, cfg: Config, displays: list[Display]) -> None:
        super().__init__(cfg)
        self._displays = displays
        self.name = "+".join(d.name for d in displays)

    def start(self) -> None:
        for d in self._displays:
            d.start()

    def render(self, state: DetectionState) -> None:
        for d in self._displays:
            d.render(state)

    def stop(self) -> None:
        for d in self._displays:
            d.stop()
