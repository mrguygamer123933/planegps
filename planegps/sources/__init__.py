"""Flight data source providers."""

from __future__ import annotations

from ..config import Config
from .base import FlightDataSource


def create_source(cfg: Config) -> FlightDataSource:
    """Factory: build the configured data source."""
    provider = cfg.data_source.provider.lower()
    if provider == "mock":
        from .mock import MockSource

        return MockSource(cfg)
    if provider == "opensky":
        from .opensky import OpenSkySource

        return OpenSkySource(cfg)
    if provider in ("flightradar24", "fr24"):
        from .flightradar24 import FlightRadar24Source

        return FlightRadar24Source(cfg)
    raise ValueError(f"Unknown data source provider: {provider!r}")


__all__ = ["FlightDataSource", "create_source"]
