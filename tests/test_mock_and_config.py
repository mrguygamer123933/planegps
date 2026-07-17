
from planegps.config import load_config
from planegps.detector import Detector
from planegps.sources import create_source
from planegps.sources.mock import MockSource


def test_mock_source_produces_flights():
    cfg = load_config()
    cfg.data_source.mock_seed = 42
    src = MockSource(cfg)
    flights = src.fetch()
    assert len(flights) == cfg.data_source.mock_num_planes
    for f in flights:
        assert f.latitude is not None and f.longitude is not None
        assert f.callsign


def test_mock_end_to_end_detects_overhead():
    cfg = load_config()
    cfg.data_source.mock_seed = 7
    cfg.detection.radius_m = 50_000  # wide so we reliably catch something
    det = Detector(cfg, MockSource(cfg))
    state = det.detect()
    assert state.source == "mock"
    assert len(state.nearby) >= 1
    assert state.overhead  # at least one within 50km


def test_config_env_override(monkeypatch):
    monkeypatch.setenv("PLANEGPS_LAT", "40.0")
    monkeypatch.setenv("PLANEGPS_LON", "-70.0")
    monkeypatch.setenv("PLANEGPS_RADIUS_M", "1234")
    monkeypatch.setenv("PLANEGPS_PROVIDER", "mock")
    cfg = load_config()
    assert cfg.location.latitude == 40.0
    assert cfg.location.longitude == -70.0
    assert cfg.detection.radius_m == 1234.0
    assert cfg.data_source.provider == "mock"


def test_create_source_factory():
    cfg = load_config()
    assert create_source(cfg).name == "mock"


def test_default_theme_is_dark():
    cfg = load_config()
    assert cfg.display.web.theme == "dark"
