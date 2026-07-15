"""Load the metadata spreadsheet into mesa_a.layer_catalog (RF01).

Idempotent: re-running upserts by ``layer_key`` and never duplicates rows.

Usage:
    python -m geoavia_backend.scripts.load_catalog [path/to/metadados_vetoriais.csv]

The CSV path may also be given via the LAYER_CATALOG_CSV environment variable.
When neither is set, the spreadsheet shipped under docs/ is used.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from geoavia_backend.services.layer_catalog import LayerCatalogService

logger = logging.getLogger("geoavia.load_catalog")

_RELATIVE_CSV = "docs/database/modelagem/metadados_vetoriais.csv"
# Candidate locations, in order: a source checkout (repo root is 4 levels up
# from this file) and the read-only docs mount inside the backend container.
_CANDIDATES = [
    Path(__file__).resolve().parents[4] / _RELATIVE_CSV,
    Path("/app/docs/database/modelagem/metadados_vetoriais.csv"),
]


def _resolve_csv_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    env_path = os.environ.get("LAYER_CATALOG_CSV")
    if env_path:
        return Path(env_path)
    for candidate in _CANDIDATES:
        if candidate.exists():
            return candidate
    return _CANDIDATES[0]


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    csv_path = _resolve_csv_path(argv if argv is not None else sys.argv)
    if not csv_path.exists():
        logger.error("Catalog CSV not found: %s", csv_path)
        return 1

    logger.info("Loading metadata catalog from %s", csv_path)
    count = LayerCatalogService().load_from_file(str(csv_path))
    logger.info("Upserted %d catalog entries into mesa_a.layer_catalog", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
