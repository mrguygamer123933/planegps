"""Abstract flight data source."""

from __future__ import annotations

import abc

from ..config import Config
from ..models import Flight


class FlightDataSource(abc.ABC):
    """Base class for anything that can return live aircraft states."""

    name: str = "base"

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    @abc.abstractmethod
    def fetch(self) -> list[Flight]:
        """Return the current set of aircraft near the configured location.

        Implementations should raise on hard errors; the detector decides how
        to surface them.
        """
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - optional hook
        """Release any resources (sockets, sessions)."""
