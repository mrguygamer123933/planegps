"""Web dashboard display for a monitor / browser.

Runs a small Flask server in a background thread. The main app loop calls
:meth:`render` each cycle to cache the latest state, which the browser polls
via ``/api/state``.
"""

from __future__ import annotations

import logging
import os
import threading

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from ..config import Config
from ..models import DetectionState
from ..photos import PhotoService
from .base import Display

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "web_assets")


class WebDisplay(Display):
    name = "web"

    def __init__(self, cfg: Config) -> None:
        super().__init__(cfg)
        self._latest: dict = DetectionState(
            location_name=cfg.location.name,
            latitude=cfg.location.latitude,
            longitude=cfg.location.longitude,
            radius_m=cfg.detection.radius_m,
        ).to_dict()
        self._lock = threading.Lock()
        self._photos = (
            PhotoService(user_agent=cfg.display.web.photo_user_agent)
            if cfg.display.web.photos
            else None
        )
        self._app = self._build_app()
        self._server = None
        self._thread: threading.Thread | None = None

    def _build_app(self) -> Flask:
        app = Flask(__name__, static_folder=None)
        # Quiet the werkzeug request log so the console display stays readable.
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

        @app.route("/")
        def index():
            return send_from_directory(_ASSETS_DIR, "index.html")

        @app.route("/app.js")
        def appjs():
            return send_from_directory(_ASSETS_DIR, "app.js")

        @app.route("/api/state")
        def state():
            with self._lock:
                return jsonify(self._latest)

        @app.route("/api/photo/<icao24>")
        def photo(icao24):
            if self._photos is None:
                return jsonify({"available": False, "disabled": True})
            data = self._photos.lookup(icao24, request.args.get("reg"))
            if not data:
                return jsonify({"available": False})
            return jsonify({"available": True, **data})

        @app.route("/healthz")
        def healthz():
            return jsonify({"ok": True})

        return app

    def start(self) -> None:
        host = self.cfg.display.web.host
        port = self.cfg.display.web.port
        self._server = make_server(host, port, self._app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        shown_host = "localhost" if host in ("0.0.0.0", "") else host
        print(f"[planegps] Web dashboard on http://{shown_host}:{port}")

    def render(self, state: DetectionState) -> None:
        with self._lock:
            self._latest = state.to_dict()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
