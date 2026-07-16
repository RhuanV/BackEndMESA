"""Generate the committed demo-município seed (vector + raster).

Produces the deterministic, offline demo fixtures loaded by the seed migrations
so a fresh `git clone` + `docker compose up` shows Phases 4/5 working without any
government download (see docs/adr/0007):

    backend/seed/demo_<ibge>_vetor.sql.gz    -- município + 5 vector layers
    backend/seed/demo_<ibge>_slope.tif       -- slope (percent) raster
    backend/seed/demo_<ibge>_landuse.tif     -- MapBiomas-coded land-use raster

Run once (checked-in output is what deploys use):

    python -m geoavia_backend.scripts.make_demo_seed          # both
    python -m geoavia_backend.scripts.make_demo_seed vetor    # only vector
    python -m geoavia_backend.scripts.make_demo_seed raster   # only raster

The demo município is a synthetic, clearly-labelled polygon placed over the real
São Paulo state basemap; it is a demonstration fixture, not official data. Real
ingestion is via the Airflow DAGs. Provenance: backend/seed/PROVENANCE.md.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

# Deterministic demo município (synthetic). 7-digit code that is obviously not a
# real IBGE municipality, placed in the interior of São Paulo state.
DEMO_IBGE = "9999999"
DEMO_NOME = "Município Demonstração (MESA-A)"
DEMO_UF = "SP"
# Bounding box (lon/lat, EPSG:4674) — ~0.4° square (~44 km).
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = -48.80, -22.50, -48.40, -22.10

_SEED_DIR = Path(__file__).resolve().parents[3] / "seed"


def _poly_wkt(lon0: float, lat0: float, lon1: float, lat1: float) -> str:
    """Axis-aligned rectangle as POLYGON WKT (lon lat, closed ring)."""
    return (
        f"POLYGON(({lon0} {lat0}, {lon1} {lat0}, {lon1} {lat1}, " f"{lon0} {lat1}, {lon0} {lat0}))"
    )


def build_vetor_sql() -> str:
    """Builds the idempotent SQL for the município + 5 demo vector layers."""
    muni = _poly_wkt(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)
    # Sub-polygons within the município for each layer.
    biomas = _poly_wkt(LON_MIN + 0.02, LAT_MIN + 0.02, LON_MAX - 0.02, LAT_MAX - 0.02)
    quilombola = _poly_wkt(LON_MIN + 0.05, LAT_MIN + 0.05, LON_MIN + 0.12, LAT_MIN + 0.12)
    assentamento = _poly_wkt(LON_MAX - 0.14, LAT_MIN + 0.05, LON_MAX - 0.05, LAT_MIN + 0.13)
    floresta = _poly_wkt(LON_MIN + 0.05, LAT_MAX - 0.14, LON_MIN + 0.15, LAT_MAX - 0.04)
    geodiv = _poly_wkt(LON_MIN + 0.16, LAT_MIN + 0.16, LON_MAX - 0.16, LAT_MAX - 0.16)

    def layer_insert(table: str, wkt: str, props: str) -> str:
        # Idempotent: only insert the demo row once (guarded on the seed marker).
        return (
            f"INSERT INTO mesa_a.{table} (properties, geom)\n"
            f"SELECT '{props}'::jsonb, ST_SetSRID(ST_GeomFromText('{wkt}'), 4674)\n"
            f"WHERE NOT EXISTS (SELECT 1 FROM mesa_a.{table} "
            f"WHERE properties->>'seed' = 'demo');"
        )

    statements = [
        "-- Demo município (synthetic MESA-A fixture; see PROVENANCE.md)",
        (
            "INSERT INTO mesa_a.vetor_limites_municipais "
            "(codigo_ibge, nome_municipio, sigla_estado, geom)\n"
            f"SELECT '{DEMO_IBGE}', '{DEMO_NOME}', '{DEMO_UF}', "
            f"ST_Multi(ST_SetSRID(ST_GeomFromText('{muni}'), 4674))\n"
            "WHERE NOT EXISTS (SELECT 1 FROM mesa_a.vetor_limites_municipais "
            f"WHERE codigo_ibge = '{DEMO_IBGE}');"
        ),
        layer_insert("vetor_ibge_biomas", biomas, '{"bioma": "Mata Atlântica", "seed": "demo"}'),
        layer_insert(
            "vetor_incra_quilombolas", quilombola, '{"nome": "Quilombo Demo", "seed": "demo"}'
        ),
        layer_insert(
            "vetor_incra_assentamentos",
            assentamento,
            '{"nome": "Assentamento Demo", "seed": "demo"}',
        ),
        layer_insert(
            "vetor_mma_florestas_publicas", floresta, '{"nome": "Floresta Demo", "seed": "demo"}'
        ),
        layer_insert("vetor_cprm_geodiversidade", geodiv, '{"classe": "Geo Demo", "seed": "demo"}'),
    ]
    return "\n\n".join(statements) + "\n"


def write_vetor_seed() -> Path:
    _SEED_DIR.mkdir(parents=True, exist_ok=True)
    out = _SEED_DIR / f"demo_{DEMO_IBGE}_vetor.sql.gz"
    out.write_bytes(gzip.compress(build_vetor_sql().encode("utf-8")))
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return out


def write_raster_seed() -> None:
    """Generates demo slope + land-use GeoTIFFs over the município bbox.

    Deterministic synthetic rasters at ~30 m: a slope gradient (0–8%) and a
    land-use raster of MapBiomas class codes. Real rasters are produced on the
    server by the Airflow DAGs (see PROVENANCE.md).
    """
    import numpy as np  # noqa: PLC0415 — heavy, optional (only for raster seed)
    import rasterio  # noqa: PLC0415
    from rasterio.transform import from_bounds  # noqa: PLC0415

    _SEED_DIR.mkdir(parents=True, exist_ok=True)
    # ~30 m at this latitude ≈ 0.00027°; 0.4° / 0.00027 ≈ 1480 px. Keep it small.
    width = height = 512
    transform = from_bounds(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX, width, height)

    ys = np.linspace(0.0, 1.0, height).reshape(-1, 1)
    xs = np.linspace(0.0, 1.0, width).reshape(1, -1)
    # Slope 0–8% with a smooth diagonal ramp + a steep ridge (excluded later).
    slope = (2.0 + 6.0 * (xs + ys) / 2.0).astype("float32")
    slope[height // 2 - 8 : height // 2 + 8, :] = 18.0  # a steep band

    # Land use: pasture(15) dominant, agriculture(18) block, forest(3) block,
    # urban(24) patch, water(33) stripe — plausible MapBiomas codes.
    landuse = np.full((height, width), 15, dtype="int16")
    landuse[: height // 3, : width // 2] = 18
    landuse[2 * height // 3 :, width // 2 :] = 3
    landuse[height // 2 - 20 : height // 2 + 20, width // 2 - 20 : width // 2 + 20] = 24
    landuse[:, width - 24 : width] = 33

    common = dict(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        crs="EPSG:4674",
        transform=transform,
        compress="deflate",
        tiled=True,
    )
    slope_path = _SEED_DIR / f"demo_{DEMO_IBGE}_slope.tif"
    with rasterio.open(slope_path, "w", dtype="float32", nodata=-9999.0, **common) as dst:
        dst.write(slope, 1)
    landuse_path = _SEED_DIR / f"demo_{DEMO_IBGE}_landuse.tif"
    with rasterio.open(landuse_path, "w", dtype="int16", nodata=0, **common) as dst:
        dst.write(landuse, 1)
    print(f"wrote {slope_path} and {landuse_path}")


def main(argv: list[str] | None = None) -> int:
    args = (argv if argv is not None else sys.argv)[1:]
    what = args[0] if args else "all"
    if what in ("vetor", "all"):
        write_vetor_seed()
    if what in ("raster", "all"):
        write_raster_seed()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
