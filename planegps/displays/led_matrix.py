"""RGB LED matrix display (Raspberry Pi) with an on-disk preview fallback.

On a Raspberry Pi with the ``rgbmatrix`` Python bindings installed
(https://github.com/hzeller/rpi-rgb-led-matrix), frames are pushed to the
panel. Everywhere else (dev machines, CI, this container) the same frame is
rendered with Pillow and written to a preview PNG so the output can be
inspected without hardware.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from ..config import Config
from ..geo import bearing_to_compass
from ..models import DetectionState
from .base import Display

_BG = (5, 7, 13)
_ACCENT = (52, 211, 153)
_TEXT = (230, 237, 247)
_MUTED = (124, 138, 165)


class LedMatrixDisplay(Display):
    name = "led"

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        self.rows = cfg.display.led.rows
        self.cols = cfg.display.led.cols
        self._matrix = None
        self._canvas = None
        self._init_hardware()

    def _init_hardware(self) -> None:
        try:  # pragma: no cover - only runs on a Pi with the library
            from rgbmatrix import RGBMatrix, RGBMatrixOptions

            options = RGBMatrixOptions()
            options.rows = self.rows
            options.cols = self.cols
            options.brightness = self.cfg.display.led.brightness
            self._matrix = RGBMatrix(options=options)
            self._canvas = self._matrix.CreateFrameCanvas()
            print("[planegps] LED matrix hardware initialised.")
        except Exception:
            print(
                "[planegps] LED hardware not available; writing preview to "
                f"{self.cfg.display.led.preview_path}"
            )

    def _draw(self, state: DetectionState) -> Image.Image:
        img = Image.new("RGB", (self.cols, self.rows), _BG)
        d = ImageDraw.Draw(img)
        if state.error:
            d.text((1, 1), "ERR", fill=(245, 158, 11))
            return img
        if not state.overhead:
            d.text((1, 1), "NO PLANES", fill=_MUTED)
            d.text((1, self.rows // 2), state.location_name[:10], fill=_MUTED)
            return img
        f = state.overhead[0]
        # Three lines fit cleanly on a 32px-tall panel with the default font.
        d.text((1, 0), (f.callsign or f.icao24)[:10], fill=_ACCENT)
        d.text((1, 10), f.route[:12], fill=_TEXT)
        direction = bearing_to_compass(f.bearing_deg) if f.bearing_deg is not None else "?"
        dist = f"{f.distance_m:.0f}m" if f.distance_m is not None else "?"
        d.text((1, 21), f"{(f.aircraft_type or '?')[:4]} {direction} {dist}", fill=_MUTED)
        return img

    def render(self, state: DetectionState) -> None:
        img = self._draw(state)
        if self._matrix is not None:  # pragma: no cover - hardware path
            self._canvas.SetImage(img.convert("RGB"))
            self._canvas = self._matrix.SwapOnVSync(self._canvas)
        else:
            # Upscale so the preview is easy to see, keeping crisp pixels.
            scale = 12
            preview = img.resize((self.cols * scale, self.rows * scale), Image.NEAREST)
            preview.save(self.cfg.display.led.preview_path)
