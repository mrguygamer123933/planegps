"""RGB LED matrix display (Raspberry Pi) with an on-disk preview fallback.

On a Raspberry Pi with the ``rgbmatrix`` Python bindings installed
(https://github.com/hzeller/rpi-rgb-led-matrix), frames are pushed to the
panel. Everywhere else (dev machines, CI, this container) the same frame is
rendered with Pillow and written to a preview PNG so the output can be
inspected without hardware.
"""

from __future__ import annotations

from ..config import Config
from ..led_render import render_led_frame, render_led_preview
from ..models import DetectionState
from .base import Display


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

    def render(self, state: DetectionState) -> None:
        if self._matrix is not None:  # pragma: no cover - hardware path
            frame = render_led_frame(state, self.rows, self.cols)
            self._canvas.SetImage(frame.convert("RGB"))
            self._canvas = self._matrix.SwapOnVSync(self._canvas)
        else:
            preview = render_led_preview(state, self.rows, self.cols)
            preview.save(self.cfg.display.led.preview_path)
