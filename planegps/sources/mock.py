"""A deterministic-ish mock data source.

Generates synthetic aircraft that drift across the sky near the configured
location so the app can be demoed and tested completely offline (no network
or API key required). Planes move a little on every :meth:`fetch`, and new
ones occasionally appear, so the display looks live.
"""

from __future__ import annotations

import math
import random
import time

from ..config import Config
from ..geo import EARTH_RADIUS_M
from ..models import Flight
from .base import FlightDataSource

# Registrations below are real aircraft with photos on planespotters.net, so the
# dashboard's photo panel shows an actual picture of the type in the demo.
# (airline, callsign_prefix, aircraft_type, origin, destination, registration)
_FLEET = [
    ("British Airways", "BAW", "A380", "LHR", "JFK", "G-XLEB"),
    ("British Airways", "BAW", "A320", "LHR", "EDI", "G-EUYB"),
    ("British Airways", "BAW", "B777", "LHR", "BOS", "G-VIIP"),
    ("Lufthansa", "DLH", "A380", "FRA", "LHR", "D-AIMA"),
    ("KLM", "KLM", "B737", "AMS", "LHR", "PH-BXA"),
    ("Emirates", "UAE", "A380", "DXB", "LHR", "A6-EUV"),
    ("Ryanair", "RYR", "B738", "STN", "DUB", "EI-EFZ"),
    ("Air France", "AFR", "A319", "CDG", "LHR", "F-GRHA"),
    ("United", "UAL", "B789", "EWR", "LHR", "N24972"),
    ("Qatar Airways", "QTR", "A350", "DOH", "LHR", "A7-ALA"),
    ("easyJet", "EZY", "A319", "LGW", "GVA", "G-EZBY"),
    ("Delta", "DAL", "A333", "ATL", "LHR", "N801NW"),
]

_COUNTRIES = [
    "United Kingdom",
    "Germany",
    "Netherlands",
    "United Arab Emirates",
    "Ireland",
    "France",
    "United States",
    "Qatar",
]


def _offset(lat: float, lon: float, dx_m: float, dy_m: float) -> tuple[float, float]:
    """Offset a lat/lon by east/north meters."""
    dlat = math.degrees(dy_m / EARTH_RADIUS_M)
    dlon = math.degrees(dx_m / (EARTH_RADIUS_M * math.cos(math.radians(lat))))
    return lat + dlat, lon + dlon


class _MockPlane:
    def __init__(self, rng: random.Random, base_lat: float, base_lon: float, radius_m: float):
        airline, prefix, ac_type, origin, dest, registration = rng.choice(_FLEET)
        self.airline = airline
        self.callsign = f"{prefix}{rng.randint(10, 999)}"
        self.icao24 = f"{rng.randint(0, 0xFFFFFF):06x}"
        self.registration = registration
        self.aircraft_type = ac_type
        self.origin = origin
        self.destination = dest
        self.origin_country = rng.choice(_COUNTRIES)
        self.altitude_m = rng.uniform(600, 11000)
        self.ground_speed_ms = rng.uniform(120, 260)
        self.vertical_rate_ms = rng.uniform(-6, 6)
        self.heading = rng.uniform(0, 360)
        # Spawn at a random distance/angle from home. Distance is uniform in
        # [0, 2*radius], so roughly half of the fleet starts within the
        # detection circle (reliable "overhead" traffic for demos/tests) while
        # the rest populate the surrounding area.
        dist = rng.uniform(0, radius_m * 2)
        angle = rng.uniform(0, 2 * math.pi)
        self.x = math.cos(angle) * dist
        self.y = math.sin(angle) * dist
        self._base = (base_lat, base_lon)
        self._last = time.time()

    def advance(self, now: float) -> None:
        dt = max(0.0, now - self._last)
        self._last = now
        rad = math.radians(self.heading)
        self.x += math.sin(rad) * self.ground_speed_ms * dt
        self.y += math.cos(rad) * self.ground_speed_ms * dt
        self.altitude_m = max(150.0, self.altitude_m + self.vertical_rate_ms * dt)

    def far_away(self, radius_m: float) -> bool:
        return math.hypot(self.x, self.y) > radius_m * 4

    def to_flight(self) -> Flight:
        lat, lon = _offset(self._base[0], self._base[1], self.x, self.y)
        return Flight(
            icao24=self.icao24,
            callsign=self.callsign,
            registration=self.registration,
            aircraft_type=self.aircraft_type,
            airline=self.airline,
            origin=self.origin,
            destination=self.destination,
            origin_country=self.origin_country,
            latitude=lat,
            longitude=lon,
            altitude_m=round(self.altitude_m, 1),
            heading=round(self.heading, 1),
            ground_speed_ms=round(self.ground_speed_ms, 1),
            vertical_rate_ms=round(self.vertical_rate_ms, 2),
            on_ground=False,
        )


class MockSource(FlightDataSource):
    name = "mock"

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        self._rng = random.Random(cfg.data_source.mock_seed)
        self._num = max(1, cfg.data_source.mock_num_planes)
        self._planes: list[_MockPlane] = [self._spawn() for _ in range(self._num)]

    def _spawn(self) -> _MockPlane:
        return _MockPlane(
            self._rng,
            self.cfg.location.latitude,
            self.cfg.location.longitude,
            self.cfg.detection.radius_m,
        )

    def fetch(self) -> list[Flight]:
        now = time.time()
        for plane in self._planes:
            plane.advance(now)
        # Respawn planes that drift too far so the sky stays populated.
        self._planes = [p for p in self._planes if not p.far_away(self.cfg.detection.radius_m)]
        while len(self._planes) < self._num:
            self._planes.append(self._spawn())
        return [p.to_flight() for p in self._planes]
