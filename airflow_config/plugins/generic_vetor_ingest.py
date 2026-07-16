"""Generic shapefile-ZIP ingestion into a mesa_a.vetor_* table (Fase 4).

Downloads a shapefile ZIP (TLS-verified via secure_http), reprojects to SIRGAS
2000 (EPSG:4674) and loads each feature as (properties JSONB, geom) — storing
all attributes generically instead of hardcoding per-source field names, so the
same code robustly ingests any of the remaining BDG sources.

`table` is always one of a fixed, internal whitelist passed by the DAGs, so the
f-string table interpolation is not user input.
"""

import json
import logging
import os
import shutil
import zipfile

import geopandas as gpd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import Json, execute_batch

from secure_http import government_get


def _find_shapefile(root: str) -> str | None:
    for dirpath, _, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".shp"):
                return os.path.join(dirpath, name)
    return None


def _json_safe(value) -> dict:
    """Coerces a feature's attributes to a JSON-serializable dict (dates→str)."""
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))


def ingest_zip_to_table(url: str, table: str, run_id: str) -> int:
    """Full extract→transform→load for one source. Returns the row count."""
    run_id = run_id.replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_{table}_{run_id}"
    extract_dir = os.path.join(work_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    zip_path = os.path.join(work_dir, "data.zip")

    try:
        logging.info("Downloading %s from %s", table, url)
        resp = government_get(url, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        shp = _find_shapefile(extract_dir)
        if not shp:
            raise FileNotFoundError(f"No .shp found in the ZIP for {table}")

        gdf = gpd.read_file(shp)
        if gdf.crs and gdf.crs.to_epsg() != 4674:
            logging.info("Reprojecting %s from %s to EPSG:4674", table, gdf.crs)
            gdf = gdf.to_crs(4674)

        rows = []
        for _, row in gdf.iterrows():
            geom = row.get("geometry")
            if geom is None or geom.is_empty:
                continue
            props = _json_safe(row.drop(labels="geometry").to_dict())
            rows.append((Json(props), geom.wkt))

        if not rows:
            logging.warning("No valid features for %s; skipping load.", table)
            return 0

        hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
        conn = hook.get_conn()
        cur = conn.cursor()
        cur.execute(f"TRUNCATE TABLE mesa_a.{table} RESTART IDENTITY;")
        execute_batch(
            cur,
            f"""
            INSERT INTO mesa_a.{table} (properties, geom)
            VALUES (%s, ST_SetSRID(ST_GeomFromText(%s), 4674));
            """,
            rows,
        )
        conn.commit()
        logging.info("Loaded %d features into mesa_a.%s", len(rows), table)

        # Refresh the layer's resolution views so the /layers API (which reads
        # {prefix}_z1/z2/z3) serves the freshly-loaded geometry on the map. Done
        # after the data commit and best-effort (a view may not exist for every
        # table), each in its own transaction so a failure never drops the load.
        prefix = table[len("vetor_") :] if table.startswith("vetor_") else table
        for zoom in ("z1", "z2", "z3"):
            try:
                cur.execute(f"REFRESH MATERIALIZED VIEW {prefix}_{zoom};")
                conn.commit()
            except Exception as exc:  # noqa: BLE001 — view may not exist for every table
                conn.rollback()
                logging.warning("Could not refresh %s_%s: %s", prefix, zoom, exc)
        cur.close()
        conn.close()
        return len(rows)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
