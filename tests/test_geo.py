from planegps.geo import (
    bearing_deg,
    bearing_to_compass,
    bounding_box,
    elevation_deg,
    haversine_m,
)


def test_haversine_zero():
    assert haversine_m(51.0, -0.1, 51.0, -0.1) == 0.0


def test_haversine_known_distance():
    # London to Paris is roughly 340 km.
    d = haversine_m(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330_000 < d < 350_000


def test_bearing_cardinuals():
    # Due north
    assert abs(bearing_deg(0.0, 0.0, 1.0, 0.0) - 0.0) < 1e-6
    # Due east
    assert abs(bearing_deg(0.0, 0.0, 0.0, 1.0) - 90.0) < 1e-6


def test_bearing_to_compass():
    assert bearing_to_compass(0) == "N"
    assert bearing_to_compass(90) == "E"
    assert bearing_to_compass(180) == "S"
    assert bearing_to_compass(270) == "W"
    assert bearing_to_compass(359) == "N"


def test_elevation_overhead_is_90():
    # Directly overhead (zero ground distance) -> straight up.
    assert abs(elevation_deg(0.0, 10000.0) - 90.0) < 1e-6


def test_elevation_45_degrees():
    # Equal altitude and ground distance -> 45 degrees above the horizon.
    assert abs(elevation_deg(5000.0, 5000.0) - 45.0) < 1e-6


def test_elevation_low_on_horizon():
    # Far away, low altitude -> small elevation angle.
    assert elevation_deg(50000.0, 1000.0) < 5.0


def test_bounding_box_contains_center():
    lat, lon = 51.47, -0.45
    lamin, lomin, lamax, lomax = bounding_box(lat, lon, 3000)
    assert lamin < lat < lamax
    assert lomin < lon < lomax
