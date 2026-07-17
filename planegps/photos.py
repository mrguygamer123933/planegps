"""Aircraft photo lookup via the planespotters.net public photo API.

https://www.planespotters.net/photo/api

The API requires a ``User-Agent`` that includes a contact URL or email. Results
(including "no photo found") are cached in memory with a TTL so we don't hammer
the API while the same aircraft is overhead.
"""

from __future__ import annotations

import threading
import time

import requests

_API = "https://api.planespotters.net/pub/photos"

# planespotters requires a contact URL/email in the UA string.
DEFAULT_USER_AGENT = "planegps/0.1 (+https://github.com/mrguygamer123933/planegps)"


class PhotoService:
    """Look up a representative photo for an aircraft by hex code or registration."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        ttl_s: float = 3600.0,
        timeout_s: float = 6.0,
    ) -> None:
        self._ttl = ttl_s
        self._timeout = timeout_s
        self._cache: dict[str, tuple[float, dict | None]] = {}
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": user_agent, "Accept": "application/json"}
        )

    def _get_cached(self, key: str):
        with self._lock:
            item = self._cache.get(key)
            if item and (time.time() - item[0]) < self._ttl:
                return True, item[1]
        return False, None

    def _store(self, key: str, value: dict | None) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)

    def _query(self, kind: str, value: str) -> dict | None:
        try:
            resp = self._session.get(f"{_API}/{kind}/{value}", timeout=self._timeout)
        except requests.RequestException:
            return None
        if resp.status_code != 200:
            return None
        try:
            photos = (resp.json() or {}).get("photos") or []
        except ValueError:
            return None
        if not photos:
            return None
        p = photos[0]
        return {
            "thumbnail": (p.get("thumbnail") or {}).get("src"),
            "large": (p.get("thumbnail_large") or {}).get("src"),
            "link": p.get("link"),
            "photographer": p.get("photographer"),
            "source": "planespotters.net",
        }

    def lookup(
        self, icao24: str | None, registration: str | None = None
    ) -> dict | None:
        """Return photo info for an aircraft, or ``None`` if unavailable.

        Tries the ICAO 24-bit hex first (works with live data sources), then
        falls back to the registration.
        """
        icao24 = (icao24 or "").strip().lower() or None
        registration = (registration or "").strip().upper() or None
        if not icao24 and not registration:
            return None

        key = f"{icao24}|{registration}"
        hit, cached = self._get_cached(key)
        if hit:
            return cached

        result: dict | None = None
        if icao24:
            result = self._query("hex", icao24)
        if result is None and registration:
            result = self._query("reg", registration)
        # Cache negative results too, to avoid repeated slow lookups.
        self._store(key, result)
        return result
