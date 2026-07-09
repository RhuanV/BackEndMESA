"""Shared builder for GeoJSON FeatureCollection queries.

Assembles the FeatureCollection envelope in SQL (json_build_object +
ST_AsGeoJSON) so geometries are never (de)serialized in Python. Callers pass the
geometry/properties SQL expressions and the inner SELECT; %s placeholders bind
positionally in text order (geometry expression first, then the inner SELECT).
"""
from __future__ import annotations

from geoavia_backend.core.db import cursor

_EMPTY: dict = {"type": "FeatureCollection", "features": []}


def fetch_feature_collection(
    geometry_sql: str,
    properties_sql: str,
    inner_sql: str,
    params: tuple,
) -> dict:
    query = f"""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', {geometry_sql}::json,
                    'properties', {properties_sql}
                )
            ), '[]'::json)
        ) AS geojson
        FROM ( {inner_sql} ) sub;
    """
    with cursor(dict_rows=True) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return row["geojson"] if row else _EMPTY
