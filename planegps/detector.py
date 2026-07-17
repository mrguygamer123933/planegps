"""Core detection logic: turn raw flights into an overhead/nearby snapshot."""

from __future__ import annotations

from .config import Config
from .geo import bearing_deg, haversine_m
from .models import DetectionState, Flight
from .sources.base import FlightDataSource


class Detector:
    """Filters raw flights by distance/altitude relative to the location."""

    def __init__(self, cfg: Config, source: FlightDataSource) -> None:
        self.cfg = cfg
        self.source = source

    def _annotate(self, flight: Flight) -> Flight:
        if flight.latitude is None or flight.longitude is None:
            return flight
        flight.distance_m = haversine_m(
            self.cfg.location.latitude,
            self.cfg.location.longitude,
            flight.latitude,
            flight.longitude,
        )
        flight.bearing_deg = bearing_deg(
            self.cfg.location.latitude,
            self.cfg.location.longitude,
            flight.latitude,
            flight.longitude,
        )
        return flight

    def _altitude_ok(self, flight: Flight) -> bool:
        alt = flight.altitude_m
        if alt is None:
            return True
        det = self.cfg.detection
        if alt < det.min_altitude_m:
            return False
        if det.max_altitude_m is not None and alt > det.max_altitude_m:
            return False
        return True

    def detect(self) -> DetectionState:
        """Fetch and classify flights. Errors are captured on the state."""
        loc = self.cfg.location
        det = self.cfg.detection
        state = DetectionState(
            location_name=loc.name,
            latitude=loc.latitude,
            longitude=loc.longitude,
            radius_m=det.radius_m,
            source=self.source.name,
        )
        try:
            raw = self.source.fetch()
        except Exception as exc:  # surface as state error rather than crashing loop
            state.error = f"{type(exc).__name__}: {exc}"
            return state

        annotated = [self._annotate(f) for f in raw if not f.on_ground]
        annotated = [f for f in annotated if f.distance_m is not None]

        overhead = [
            f
            for f in annotated
            if f.distance_m is not None
            and f.distance_m <= det.radius_m
            and self._altitude_ok(f)
        ]
        overhead.sort(key=lambda f: f.distance_m or 0.0)

        # "nearby" = anything we can see in the requested window, for context.
        nearby = sorted(annotated, key=lambda f: f.distance_m or 0.0)[:25]

        state.overhead = overhead
        state.nearby = nearby
        return state
