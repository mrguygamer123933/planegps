# planegps

Local app that detects aircraft within a customizable radius of a location and shows them on a monitor (web dashboard), console, or Raspberry Pi RGB LED matrix. Pure Python.

## Cursor Cloud specific instructions

- **Python venv**: use `.venv` at the repo root. Activate with `source .venv/bin/activate`. The update script (re)creates it and installs the package editable with dev extras. Creating a venv requires the `python3.12-venv` system package (already present on the snapshot); if a fresh VM lacks it, `sudo apt-get install -y python3.12-venv`.
- **Standard commands** (see `pyproject.toml` / `README.md`): lint `ruff check .`, tests `pytest`, run `planegps ...` (module form `python -m planegps`).
- **Live data sources need network egress**: the OpenSky (`opensky-network.org`) and FlightRadar24 endpoints are **not reachable** from the Cloud VM (blocked egress), so `--provider opensky` / `flightradar24` will surface a data-source error in the UI. Always develop/test/demo with `--provider mock`, which is fully offline and populates a realistic, moving sky.
- **Web display is long-running**: `planegps --display web` starts a Flask server (default port 8080) in a background thread and then loops forever polling the data source. Start it in a tmux/background session; it does not exit on its own. The browser polls `/api/state` every second; `/healthz` returns `{"ok": true}`.
- **Mock sky reliably has overhead traffic**: `MockSource` spawns planes at a uniform distance in `[0, 2*radius]`, so ~half start inside the detection circle regardless of `radius_m`. Good for screenshots/tests without waiting.
- **LED backend without hardware**: `--display led` detects no `rgbmatrix` library on non-Pi hosts and writes `led_preview.png` (12× upscaled) instead of driving a panel — that PNG is the artifact to inspect. `led_preview.png` and `config.yaml` are git-ignored.
