"""Geospatial helpers (great-circle distance, bearing, bounding boxes)."""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial compass bearing from point 1 to point 2, in degrees [0, 360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def bearing_to_compass(bearing: float) -> str:
    """Convert a bearing in degrees to an 8-point compass label."""
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((bearing + 22.5) % 360 // 45)
    return points[idx]


def bounding_box(lat: float, lon: float, radius_m: float) -> tuple[float, float, float, float]:
    """Return (lamin, lomin, lamax, lomax) covering a radius around a point.

    Used to request a small window of the sky from remote APIs.
    """
    dlat = math.degrees(radius_m / EARTH_RADIUS_M)
    # Guard against division by zero near the poles.
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    dlon = math.degrees(radius_m / (EARTH_RADIUS_M * cos_lat))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)
