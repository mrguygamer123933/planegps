from planegps.config import load_config
from planegps.displays import create_display
from planegps.displays.multi import MultiDisplay
from planegps.led_render import render_led_frame, render_led_preview
from planegps.models import DetectionState, Flight


def _state_with_plane():
    f = Flight(
        icao24="abc123",
        callsign="BAW123",
        aircraft_type="A320",
        origin="LHR",
        destination="JFK",
        altitude_m=1500.0,
        distance_m=800.0,
        bearing_deg=270.0,
        elevation_deg=62.0,
    )
    return DetectionState(
        location_name="Home",
        latitude=51.47,
        longitude=-0.45,
        radius_m=3000,
        overhead=[f],
        nearby=[f],
    )


def test_led_frame_dimensions():
    img = render_led_frame(_state_with_plane(), rows=32, cols=64)
    assert img.size == (64, 32)


def test_led_frame_has_lit_pixels():
    img = render_led_frame(_state_with_plane(), rows=32, cols=64)
    colors = {c for _, c in img.getcolors(maxcolors=100000)}
    # More than just the background colour should be present.
    assert len(colors) > 1


def test_led_preview_is_upscaled_panel():
    preview = render_led_preview(_state_with_plane(), rows=32, cols=64)
    w, h = preview.size
    assert w > 64 and h > 32  # scaled up into a board sketch


def test_led_preview_no_planes():
    state = DetectionState(
        location_name="Home", latitude=51.47, longitude=-0.45, radius_m=3000
    )
    preview = render_led_preview(state, rows=32, cols=64)
    assert preview.size[0] > 64


def test_create_multi_display():
    cfg = load_config()
    cfg.display.backend = "console,led"
    disp = create_display(cfg)
    assert isinstance(disp, MultiDisplay)
    assert disp.name == "console+led"


def test_create_single_display():
    cfg = load_config()
    cfg.display.backend = "console"
    disp = create_display(cfg)
    assert disp.name == "console"
