"""Shared helpers for the map endpoints — zoom levels, simplification
tolerances and bbox parsing.

Used by both the static layers endpoint (layers_service) and the user-upload
display endpoint (shapefiles_service) so the two paths validate input and
route zoom levels identically.

Tolerances (degrees, SRID 4674 / SIRGAS 2000) mirror the materialized views in
backend/alembic/versions/0010_create_resolution_views.py:
    z1 = 0.05   (~5.5 km) — zoom out, Brazil-wide
    z2 = 0.01   (~1.1 km) — mid zoom, state view
    z3 = 0.002  (~220 m)  — zoom in, municipal view
"""

from __future__ import annotations

ALLOWED_ZOOMS = ("z1", "z2", "z3")
DEFAULT_ZOOM = "z2"

# Simplification tolerance per zoom level, in degrees (SRID 4674).
ZOOM_TOLERANCES: dict[str, float] = {
    "z1": 0.05,
    "z2": 0.01,
    "z3": 0.002,
}


def normalize_zoom(zoom: str | None) -> str:
    """Returns a validated zoom level, defaulting when None/empty."""
    zoom = zoom or DEFAULT_ZOOM
    if zoom not in ALLOWED_ZOOMS:
        raise ValueError(f"Invalid zoom level: {zoom}. Use z1, z2 or z3.")
    return zoom


def tolerance_for(zoom: str | None) -> float:
    """Returns the simplification tolerance (degrees) for a zoom level."""
    return ZOOM_TOLERANCES[normalize_zoom(zoom)]


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    """Parses 'west,south,east,north' into a 4-float tuple."""
    parts = raw.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must have 4 comma-separated values: west,south,east,north")
    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError("bbox values must be valid numbers") from exc

    if west >= east or south >= north:
        raise ValueError("bbox must satisfy west < east and south < north")

    return (west, south, east, north)
