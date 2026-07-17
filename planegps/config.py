"""Configuration loading and defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from typing import Any

import yaml

from .photos import DEFAULT_USER_AGENT


@dataclass
class LocationConfig:
    latitude: float = 51.4700  # near London Heathrow by default (busy sky for demos)
    longitude: float = -0.4543
    name: str = "Home"


@dataclass
class DetectionConfig:
    # Horizontal radius around the location. The user asked for a small,
    # customizable circle; default kept modest but override freely.
    radius_m: float = 3000.0
    min_altitude_m: float = 0.0
    max_altitude_m: float | None = None


@dataclass
class DataSourceConfig:
    provider: str = "mock"  # mock | opensky | flightradar24
    poll_interval_s: float = 5.0
    opensky_username: str | None = None
    opensky_password: str | None = None
    mock_num_planes: int = 7
    mock_seed: int | None = None


@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    # Show a photo of the aircraft (via planespotters.net) on the dashboard.
    photos: bool = True
    photo_user_agent: str = DEFAULT_USER_AGENT


@dataclass
class LedConfig:
    rows: int = 32
    cols: int = 64
    preview_path: str = "led_preview.png"
    brightness: int = 80


@dataclass
class DisplayConfig:
    backend: str = "web"  # web | console | led
    web: WebConfig = field(default_factory=WebConfig)
    led: LedConfig = field(default_factory=LedConfig)


@dataclass
class Config:
    location: LocationConfig = field(default_factory=LocationConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)


def _merge(base: Any, data: dict | None) -> Any:
    """Return a copy of a dataclass with values overridden by ``data``."""
    if not data:
        return base
    updates: dict[str, Any] = {}
    for key, value in data.items():
        if not hasattr(base, key):
            raise ValueError(f"Unknown config key: {key!r}")
        current = getattr(base, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            updates[key] = _merge(current, value)
        else:
            updates[key] = value
    return replace(base, **updates)


def load_config(path: str | None = None) -> Config:
    """Load configuration from a YAML file, falling back to defaults.

    Environment variables (prefixed ``PLANEGPS_``) override a few common
    fields so the app is easy to drive in containers / demos.
    """
    cfg = Config()
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        cfg = _merge(cfg, raw)

    cfg = _apply_env_overrides(cfg)
    return cfg


def _apply_env_overrides(cfg: Config) -> Config:
    env = os.environ

    def fnum(key: str, default: float) -> float:
        return float(env[key]) if key in env else default

    location = replace(
        cfg.location,
        latitude=fnum("PLANEGPS_LAT", cfg.location.latitude),
        longitude=fnum("PLANEGPS_LON", cfg.location.longitude),
        name=env.get("PLANEGPS_LOCATION_NAME", cfg.location.name),
    )
    detection = replace(
        cfg.detection,
        radius_m=fnum("PLANEGPS_RADIUS_M", cfg.detection.radius_m),
    )
    data_source = replace(
        cfg.data_source,
        provider=env.get("PLANEGPS_PROVIDER", cfg.data_source.provider),
        opensky_username=env.get("PLANEGPS_OPENSKY_USER", cfg.data_source.opensky_username),
        opensky_password=env.get("PLANEGPS_OPENSKY_PASS", cfg.data_source.opensky_password),
    )
    web = replace(
        cfg.display.web,
        port=int(env["PLANEGPS_PORT"]) if "PLANEGPS_PORT" in env else cfg.display.web.port,
    )
    display = replace(
        cfg.display,
        backend=env.get("PLANEGPS_DISPLAY", cfg.display.backend),
        web=web,
    )
    return replace(
        cfg,
        location=location,
        detection=detection,
        data_source=data_source,
        display=display,
    )
