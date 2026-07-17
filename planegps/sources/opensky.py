"""OpenSky Network REST API data source.

Free, no key required for anonymous (rate-limited) access; optional
credentials raise the rate limit. See https://openskynetwork.github.io/opensky-api/

Note: the ``/states/all`` endpoint does not include origin/destination
airports, so those fields stay ``None``. ``origin_country`` and live position
data are populated.
"""

from __future__ import annotations

import requests

from ..config import Config
from ..geo import bounding_box
from ..models import Flight
from .base import FlightDataSource

_API_URL = "https://opensky-network.org/api/states/all"

# Index positions in the OpenSky "states" vector.
_S_ICAO24 = 0
_S_CALLSIGN = 1
_S_ORIGIN_COUNTRY = 2
_S_LON = 5
_S_LAT = 6
_S_BARO_ALT = 7
_S_ON_GROUND = 8
_S_VELOCITY = 9
_S_HEADING = 10
_S_VERT_RATE = 11
_S_GEO_ALT = 13


def _f(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class OpenSkySource(FlightDataSource):
    name = "opensky"

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        self._session = requests.Session()
        user = cfg.data_source.opensky_username
        pwd = cfg.data_source.opensky_password
        self._auth = (user, pwd) if user and pwd else None

    def fetch(self) -> list[Flight]:
        lamin, lomin, lamax, lomax = bounding_box(
            self.cfg.location.latitude,
            self.cfg.location.longitude,
            # widen the request box a bit so edge aircraft aren't clipped
            self.cfg.detection.radius_m * 1.5,
        )
        params = {"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax}
        resp = self._session.get(_API_URL, params=params, auth=self._auth, timeout=15)
        resp.raise_for_status()
        payload = resp.json() or {}
        states = payload.get("states") or []
        flights: list[Flight] = []
        for s in states:
            if len(s) < 14:
                continue
            alt = _f(s[_S_GEO_ALT])
            if alt is None:
                alt = _f(s[_S_BARO_ALT])
            callsign = (s[_S_CALLSIGN] or "").strip() or None
            flights.append(
                Flight(
                    icao24=str(s[_S_ICAO24]),
                    callsign=callsign,
                    origin_country=s[_S_ORIGIN_COUNTRY],
                    latitude=_f(s[_S_LAT]),
                    longitude=_f(s[_S_LON]),
                    altitude_m=alt,
                    heading=_f(s[_S_HEADING]),
                    ground_speed_ms=_f(s[_S_VELOCITY]),
                    vertical_rate_ms=_f(s[_S_VERT_RATE]),
                    on_ground=bool(s[_S_ON_GROUND]),
                )
            )
        return flights

    def close(self) -> None:
        self._session.close()
