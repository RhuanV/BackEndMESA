# 0006 — Raster analytic core: on-disk COGs + rasterio/NumPy MCDA

**Status:** Accepted

## Context

Phase 5 of the MESA-A roadmap requires a real multi-criteria suitability
analysis (MCDA, RF05) over matricial data: slope derived from the ANADEM MDT
(30 m) and land use from MapBiomas, plus GeoTIFF export (RNF01) and an
eliminatório exclusion mask built from the vector screening layers. The database
is `postgis/postgis` (the `postgis_raster` extension is available), so in-DB
raster algebra via `ST_MapAlgebra` was an option.

## Decision

Rasters are stored as **Cloud-Optimized GeoTIFFs on a shared volume**
(`/data/raster`, the `raster_data` compose volume) and catalogued in
`mesa_a.raster_catalog`. The per-cell computation lives in a **pure NumPy core**
(`services/mcda.py`) with rasterio handling IO and the exclusion-mask
rasterization (`services/raster.py`). `postgis_raster` is enabled for validation
and optional future use, but the analytic path does not depend on in-DB algebra.

Municipal rasters are **pre-clipped per município** (Airflow DAGs, via
`gdalwarp -cutline` reading the national source through GDAL `/vsicurl/` so only
the needed window is fetched) to meet the ≤30 s municipal target (RNF02).

## Consequences

- The numeric core is unit-testable without GDAL/DB (plain NumPy arrays).
- GeoTIFF export and the map overlay are cheap file reads/clips.
- rasterio requires GDAL system libs — already installed in the backend image
  (`libgdal-dev`) and the Airflow image (`gdal-bin`).
- A raster store must be provisioned and kept consistent with the catalog; the
  eliminatório mask reuses the screening whitelist/buffers
  (see [0004](0004-rbac-three-roles-and-sandbox.md) for role gating of the run).
