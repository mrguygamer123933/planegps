"""Shared rendering for the RGB LED board.

``render_led_frame`` produces a 1-pixel-per-LED image (what actually gets
pushed to a physical panel). ``render_led_preview`` upscales that into a
dot-matrix "sketch" that looks like a real LED board, for the web dashboard
and the on-disk preview.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from .geo import bearing_to_compass
from .models import DetectionState

_BG = (5, 7, 13)
_ACCENT = (52, 211, 153)
_TEXT = (230, 237, 247)
_MUTED = (124, 138, 165)
_WARN = (245, 158, 11)


def render_led_frame(state: DetectionState, rows: int, cols: int) -> Image.Image:
    """Render the LED content at native resolution (one pixel per LED)."""
    img = Image.new("RGB", (cols, rows), _BG)
    d = ImageDraw.Draw(img)
    if state.error:
        d.text((1, 1), "ERR", fill=_WARN)
        return img
    if not state.overhead:
        d.text((1, 1), "NO PLANES", fill=_MUTED)
        d.text((1, max(9, rows // 2)), (state.location_name or "")[:10], fill=_MUTED)
        return img

    f = state.overhead[0]
    # Three lines fit cleanly on a 32px-tall panel with the default font.
    d.text((1, 0), (f.callsign or f.icao24)[:10], fill=_ACCENT)
    route = f"{f.origin or '?'}>{f.destination or '?'}"
    d.text((1, 10), route[:12], fill=_TEXT)
    direction = bearing_to_compass(f.bearing_deg) if f.bearing_deg is not None else "?"
    # Where to look. Keep it ASCII: the default bitmap font lacks arrow/degree.
    if f.elevation_deg is not None and f.elevation_deg >= 80:
        look = "UP"
    elif f.elevation_deg is not None:
        look = f"{direction}{f.elevation_deg:.0f}"
    else:
        look = direction
    dist = f"{f.distance_m:.0f}m" if f.distance_m is not None else "?"
    d.text((1, 21), f"{look} {dist}", fill=_MUTED)
    return img


def _dim(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def render_led_preview(
    state: DetectionState,
    rows: int,
    cols: int,
    led: int = 11,
    gap: int = 2,
    margin: int = 12,
) -> Image.Image:
    """Render an LED-board "sketch": round LEDs on a dark bezel.

    Lit LEDs glow in their colour; unlit LEDs show as faint dark dots, so the
    result reads clearly as a physical RGB matrix panel.
    """
    frame = render_led_frame(state, rows, cols)
    px = frame.load()
    step = led + gap
    width = margin * 2 + cols * step - gap
    height = margin * 2 + rows * step - gap

    panel = Image.new("RGB", (width, height), (10, 12, 18))
    d = ImageDraw.Draw(panel)
    # Subtle bezel.
    d.rectangle([0, 0, width - 1, height - 1], outline=(30, 36, 50), width=2)

    off = (18, 22, 30)
    for y in range(rows):
        for x in range(cols):
            r, g, b = px[x, y]
            cx = margin + x * step
            cy = margin + y * step
            box = [cx, cy, cx + led - 1, cy + led - 1]
            if (r, g, b) == _BG:
                d.ellipse(box, fill=off)
            else:
                # A dim halo behind the lit LED for a glow effect.
                halo = [box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1]
                d.ellipse(halo, fill=_dim((r, g, b), 0.35))
                d.ellipse(box, fill=(r, g, b))
    return panel
