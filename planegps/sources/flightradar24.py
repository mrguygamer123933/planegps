"""FlightRadar24 data source (via the unofficial ``FlightRadarAPI`` package).

This provider is optional. Install it with::

    pip install "planegps[flightradar24]"

FlightRadar24 has no official public API, so this uses a community client and
may break if their internal endpoints change. It does, however, provide rich
data including origin/destination airports and aircraft type.
"""

from __future__ import annotations

from ..config import Config
from ..geo import bounding_box
from ..models import Flight
from .base import FlightDataSource


class FlightRadar24Source(FlightDataSource):
    name = "flightradar24"

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        try:
            from FlightRadar24 import FlightRadar24API
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise RuntimeError(
                "The 'FlightRadarAPI' package is required for the flightradar24 "
                "provider. Install it with: pip install 'planegps[flightradar24]'"
            ) from exc
        self._api = FlightRadar24API()

    def fetch(self) -> list[Flight]:
        lamin, lomin, lamax, lomax = bounding_box(
            self.cfg.location.latitude,
            self.cfg.location.longitude,
            self.cfg.detection.radius_m * 1.5,
        )
        # FlightRadar24 bounds string: "lat_max,lat_min,lon_min,lon_max"
        bounds = f"{lamax},{lamin},{lomin},{lomax}"
        raw = self._api.get_flights(bounds=bounds)
        flights: list[Flight] = []
        for fr in raw:
            flights.append(
                Flight(
                    icao24=getattr(fr, "icao_24bit", "") or getattr(fr, "id", ""),
                    callsign=getattr(fr, "callsign", None),
                    registration=getattr(fr, "registration", None),
                    aircraft_type=getattr(fr, "aircraft_code", None),
                    airline=getattr(fr, "airline_icao", None),
                    origin=getattr(fr, "origin_airport_iata", None),
                    destination=getattr(fr, "destination_airport_iata", None),
                    latitude=_maybe_float(getattr(fr, "latitude", None)),
                    longitude=_maybe_float(getattr(fr, "longitude", None)),
                    altitude_m=_feet_to_m(getattr(fr, "altitude", None)),
                    heading=_maybe_float(getattr(fr, "heading", None)),
                    ground_speed_ms=_knots_to_ms(getattr(fr, "ground_speed", None)),
                    on_ground=_maybe_float(getattr(fr, "altitude", None)) in (0, 0.0),
                )
            )
        return flights


def _maybe_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _feet_to_m(value):
    v = _maybe_float(value)
    return None if v is None else v * 0.3048


def _knots_to_ms(value):
    v = _maybe_float(value)
    return None if v is None else v * 0.514444
