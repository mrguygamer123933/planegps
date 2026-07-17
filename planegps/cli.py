"""Command-line entry point for planegps."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from . import __version__
from .app import App
from .config import Config, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="planegps",
        description="Detect aircraft flying over your location and show them "
        "on a monitor or LED board.",
    )
    parser.add_argument("--version", action="version", version=f"planegps {__version__}")
    parser.add_argument("-c", "--config", help="Path to a YAML config file.")
    parser.add_argument("--lat", type=float, help="Latitude of the device.")
    parser.add_argument("--lon", type=float, help="Longitude of the device.")
    parser.add_argument("--radius", type=float, help="Detection radius in meters.")
    parser.add_argument(
        "--provider",
        choices=["mock", "opensky", "flightradar24"],
        help="Flight data source.",
    )
    parser.add_argument(
        "--display",
        choices=["web", "console", "led"],
        help="Output backend.",
    )
    parser.add_argument("--port", type=int, help="Port for the web display.")
    parser.add_argument(
        "--theme",
        choices=["dark", "light", "auto"],
        help="Default web dashboard theme.",
    )
    parser.add_argument("--interval", type=float, help="Poll interval in seconds.")
    parser.add_argument("--name", help="Human-friendly location name.")
    return parser


def apply_overrides(cfg: Config, args: argparse.Namespace) -> Config:
    location = cfg.location
    if args.lat is not None:
        location = replace(location, latitude=args.lat)
    if args.lon is not None:
        location = replace(location, longitude=args.lon)
    if args.name is not None:
        location = replace(location, name=args.name)

    detection = cfg.detection
    if args.radius is not None:
        detection = replace(detection, radius_m=args.radius)

    data_source = cfg.data_source
    if args.provider is not None:
        data_source = replace(data_source, provider=args.provider)
    if args.interval is not None:
        data_source = replace(data_source, poll_interval_s=args.interval)

    display = cfg.display
    if args.display is not None:
        display = replace(display, backend=args.display)
    if args.port is not None:
        display = replace(display, web=replace(display.web, port=args.port))
    if args.theme is not None:
        display = replace(display, web=replace(display.web, theme=args.theme))

    return replace(
        cfg,
        location=location,
        detection=detection,
        data_source=data_source,
        display=display,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config)
    cfg = apply_overrides(cfg, args)
    App(cfg).run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
