"""Data models shared across the application."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Flight:
    """A single aircraft observed near the configured location.

    Fields are intentionally permissive: different data sources populate
    different subsets, so anything unknown stays ``None``.
    """

    icao24: str
    callsign: str | None = None
    registration: str | None = None
    aircraft_type: str | None = None
    airline: str | None = None
    origin: str | None = None
    destination: str | None = None
    origin_country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    heading: float | None = None
    ground_speed_ms: float | None = None
    vertical_rate_ms: float | None = None
    on_ground: bool = False
    timestamp: float = field(default_factory=time.time)

    # Populated by the detector relative to the configured location.
    distance_m: float | None = None
    bearing_deg: float | None = None
    elevation_deg: float | None = None  # angle above the horizon (90 = overhead)

    @property
    def label(self) -> str:
        """A short human-friendly identifier for the flight."""
        if self.callsign and self.callsign.strip():
            return self.callsign.strip()
        if self.registration:
            return self.registration
        return self.icao24

    @property
    def route(self) -> str:
        origin = self.origin or "?"
        dest = self.destination or "?"
        return f"{origin} \u2192 {dest}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DetectionState:
    """Snapshot of the current sky around the configured location."""

    location_name: str
    latitude: float
    longitude: float
    radius_m: float
    overhead: list[Flight] = field(default_factory=list)
    nearby: list[Flight] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)
    source: str = "unknown"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_m": self.radius_m,
            "overhead": [f.to_dict() for f in self.overhead],
            "nearby": [f.to_dict() for f in self.nearby],
            "updated_at": self.updated_at,
            "source": self.source,
            "error": self.error,
        }
