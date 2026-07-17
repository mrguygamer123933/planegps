from planegps.config import Config, DetectionConfig, LocationConfig
from planegps.detector import Detector
from planegps.models import Flight
from planegps.sources.base import FlightDataSource


class _StaticSource(FlightDataSource):
    name = "static"

    def __init__(self, cfg, flights):
        super().__init__(cfg)
        self._flights = flights

    def fetch(self):
        return self._flights


def _cfg(radius_m=3000.0, max_alt=None):
    return Config(
        location=LocationConfig(latitude=51.47, longitude=-0.45, name="Test"),
        detection=DetectionConfig(radius_m=radius_m, max_altitude_m=max_alt),
    )


def test_overhead_filtering_by_radius():
    cfg = _cfg(radius_m=3000)
    close = Flight(icao24="a", latitude=51.471, longitude=-0.45, altitude_m=1000)
    far = Flight(icao24="b", latitude=52.0, longitude=-0.45, altitude_m=1000)
    det = Detector(cfg, _StaticSource(cfg, [close, far]))
    state = det.detect()
    ids = [f.icao24 for f in state.overhead]
    assert ids == ["a"]
    assert len(state.nearby) == 2  # both visible in the wider area


def test_on_ground_excluded():
    cfg = _cfg()
    grounded = Flight(icao24="g", latitude=51.47, longitude=-0.45, on_ground=True)
    det = Detector(cfg, _StaticSource(cfg, [grounded]))
    state = det.detect()
    assert state.overhead == []


def test_altitude_ceiling():
    cfg = _cfg(radius_m=5000, max_alt=5000)
    high = Flight(icao24="h", latitude=51.471, longitude=-0.45, altitude_m=11000)
    low = Flight(icao24="l", latitude=51.471, longitude=-0.45, altitude_m=1000)
    det = Detector(cfg, _StaticSource(cfg, [high, low]))
    state = det.detect()
    assert [f.icao24 for f in state.overhead] == ["l"]


def test_distance_and_bearing_annotated():
    cfg = _cfg()
    north = Flight(icao24="n", latitude=51.48, longitude=-0.45, altitude_m=1000)
    det = Detector(cfg, _StaticSource(cfg, [north]))
    state = det.detect()
    f = state.overhead[0]
    assert f.distance_m is not None and f.distance_m > 0
    assert f.bearing_deg is not None
    assert f.bearing_deg < 10 or f.bearing_deg > 350  # roughly north


def test_source_error_captured():
    cfg = _cfg()

    class _Boom(FlightDataSource):
        name = "boom"

        def fetch(self):
            raise RuntimeError("network down")

    det = Detector(cfg, _Boom(cfg))
    state = det.detect()
    assert state.error is not None
    assert "network down" in state.error
    assert state.overhead == []
