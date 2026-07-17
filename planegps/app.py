"""Application wiring: poll the data source and drive the display."""

from __future__ import annotations

import signal
import threading
import time

from .config import Config
from .detector import Detector
from .displays import create_display
from .sources import create_source


class App:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.source = create_source(cfg)
        self.detector = Detector(cfg, self.source)
        self.display = create_display(cfg)
        self._stop = threading.Event()

    def _cycle(self) -> None:
        state = self.detector.detect()
        state.updated_at = time.time()
        self.display.render(state)

    def run(self) -> None:
        """Run the poll/render loop until interrupted."""
        self.display.start()

        def _handle(_signum, _frame):
            self._stop.set()

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)

        interval = max(1.0, self.cfg.data_source.poll_interval_s)
        print(
            f"[planegps] Watching {self.cfg.location.name} "
            f"(r={self.cfg.detection.radius_m:.0f}m) via '{self.source.name}', "
            f"display='{self.display.name}', every {interval:.0f}s."
        )
        try:
            while not self._stop.is_set():
                self._cycle()
                self._stop.wait(interval)
        finally:
            self.display.stop()
            self.source.close()
            print("[planegps] stopped.")
