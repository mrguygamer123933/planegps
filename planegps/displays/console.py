"""Plain-text console display (works anywhere, no GUI needed)."""

from __future__ import annotations

import datetime as _dt

from ..geo import bearing_to_compass
from ..models import DetectionState, Flight
from .base import Display


def _fmt_alt(f: Flight) -> str:
    return f"{f.altitude_m:,.0f} m" if f.altitude_m is not None else "?"


def _fmt_dist(f: Flight) -> str:
    return f"{f.distance_m:,.0f} m" if f.distance_m is not None else "?"


def _fmt_dir(f: Flight) -> str:
    if f.bearing_deg is None:
        return "?"
    return f"{bearing_to_compass(f.bearing_deg)} ({f.bearing_deg:.0f}\u00b0)"


def _look_up(f: Flight) -> str:
    """A human instruction for where to look in the sky to spot the plane."""
    if f.bearing_deg is None or f.elevation_deg is None:
        return ""
    if f.elevation_deg >= 80:
        return "look straight up \u2191 (almost directly overhead)"
    compass = bearing_to_compass(f.bearing_deg)
    return f"look {compass} \u2191 {f.elevation_deg:.0f}\u00b0 above the horizon"


class ConsoleDisplay(Display):
    name = "console"

    def render(self, state: DetectionState) -> None:
        ts = _dt.datetime.fromtimestamp(state.updated_at).strftime("%H:%M:%S")
        print("\n" + "=" * 64)
        print(
            f"[{ts}] {state.location_name} "
            f"({state.latitude:.4f}, {state.longitude:.4f}) "
            f"r={state.radius_m:,.0f}m  src={state.source}"
        )
        print("=" * 64)
        if state.error:
            print(f"  ! data source error: {state.error}")
            return
        if not state.overhead:
            print("  No aircraft overhead right now.")
        for f in state.overhead:
            print(f"  \u2708 {f.label:<8} {f.airline or f.origin_country or '':<18} {f.route}")
            print(
                f"      type={f.aircraft_type or '?':<6} "
                f"alt={_fmt_alt(f):<10} dist={_fmt_dist(f):<10} dir={_fmt_dir(f)}"
            )
            hint = _look_up(f)
            if hint:
                print(f"      \U0001f440 {hint}")
        print(f"  ({len(state.nearby)} aircraft in the wider area)")
