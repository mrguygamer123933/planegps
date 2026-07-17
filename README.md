# planegps

Detect the aircraft flying over your house and show **what** they are, **where they're from**, and **where they're going** — on a monitor or an RGB LED board. Runs locally on a PC or a Raspberry Pi.

- **Customizable radius** – define a circle of any size around the device (default 3 km, set it to 200 m if you only want planes almost directly overhead).
- **Multiple data sources** – OpenSky Network (free), FlightRadar24 (optional), or a built‑in offline **mock** source for demos/testing.
- **Multiple displays** – a browser **radar dashboard** for a monitor, a **console** view for headless setups, and an **LED matrix** backend for Raspberry Pi (with a PNG preview everywhere else).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Offline demo (synthetic planes) with the web dashboard:
planegps --provider mock --display web --port 8080
# open http://localhost:8080
```

Then point it at your real location and live data:

```bash
planegps --provider opensky --lat 51.47 --lon -0.4543 --radius 3000 --name "Home"
```

## Configuration

Copy `config.example.yaml` to `config.yaml`, edit it, and run `planegps --config config.yaml`.
Anything omitted uses a sensible default. Key settings:

| Setting | Meaning |
| --- | --- |
| `location.latitude/longitude` | Where the device physically sits. |
| `detection.radius_m` | Radius (meters) of the "overhead" circle. Fully customizable. |
| `detection.max_altitude_m` | Optional ceiling to ignore high cruising traffic. |
| `data_source.provider` | `mock`, `opensky`, or `flightradar24`. |
| `data_source.poll_interval_s` | How often to refresh. |
| `display.backend` | `web`, `console`, or `led`. |
| `display.led.rows/cols` | LED panel geometry (default 32×64). |

CLI flags (`--lat`, `--lon`, `--radius`, `--provider`, `--display`, `--port`, `--interval`, `--name`) and `PLANEGPS_*` environment variables override the file.

## Data sources

- **mock** – synthetic planes that drift across the sky. No network or key needed. Ideal for development and demos.
- **opensky** – [OpenSky Network](https://openskynetwork.github.io/opensky-api/) REST API. Free anonymous access (rate‑limited); set `opensky_username`/`opensky_password` for higher limits. Provides live positions and country of origin (not origin/destination airports).
- **flightradar24** – uses the unofficial [`FlightRadarAPI`](https://pypi.org/project/FlightRadarAPI/) client (`pip install "planegps[flightradar24]"`). Richer data (route, aircraft type) but may break if FR24 changes their endpoints.

## Displays

- **web** – dark radar dashboard at `http://<host>:<port>` showing a sweeping radar, plane markers, and a live list with route/type/altitude/distance/direction. Best for a monitor.
- **console** – plain‑text output; great for headless boxes and logs.
- **led** – renders each frame for an RGB LED matrix. On a Raspberry Pi with the [`rpi-rgb-led-matrix`](https://github.com/hzeller/rpi-rgb-led-matrix) Python bindings it drives the panel; elsewhere it writes `led_preview.png` so you can see exactly what the panel would show.

## Development

```bash
pip install -e ".[dev]"
ruff check .     # lint
pytest           # tests
```

## License

MIT
