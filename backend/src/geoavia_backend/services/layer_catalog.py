"""Metadata catalog ingestion (RF01).

Parses the metadata spreadsheet (exported as CSV) into normalized catalog
entries and upserts them into ``mesa_a.layer_catalog`` idempotently, so the
spreadsheet is the single source of truth for layer metadata.

The parsing step (:func:`parse_catalog_csv`) is pure and side-effect free, so it
is unit-testable without a database or network.
"""

from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import asdict, dataclass

from geoavia_backend.repositories.layer_catalog import LayerCatalogRepository

# The vetorial spreadsheet has 12 fixed columns; we map by position because the
# header cells contain multi-line parenthetical notes that are awkward to match
# by text. Order matches docs/database/modelagem/metadados_vetoriais.csv.
_COLUMNS = [
    "tema",
    "plano_informacao",
    "data_atualizacao_fonte",
    "periodicidade",
    "fonte",
    "segregacao",
    "datum",
    "epsg",
    "formato",
    "geometria",
    "observacoes",
    "endereco",
]
_EXPECTED_COLS = len(_COLUMNS)

# Values the spreadsheet uses for "not applicable" / "none".
_EMPTY_TOKENS = {"", "-", "n/a", "não há", "nao ha"}

# Operational overrides for layers that already have a backend table/view and a
# MESA group. Everything else defaults to available=False until a DAG lands
# (Fase 4). Keyed by layer_key (slug(plano_informacao)__slug(fonte)).
_LAYER_OVERRIDES: dict[str, dict] = {
    "estado__ibge": {"grupo": "base", "backend_table": "state_boundaries", "available": True},
    "municipio__ibge": {
        "grupo": "base",
        "backend_table": "municipality_boundaries",
        "available": True,
    },
    # Sources ingested by the Fase 4 DAGs (generic mesa_a.vetor_* tables).
    "terras_quilombolas__incra": {
        "grupo": "exclusion",
        "backend_table": "vetor_incra_quilombolas",
        "available": True,
    },
    "assentamentos__incra": {
        "grupo": "base",
        "backend_table": "vetor_incra_assentamentos",
        "available": True,
    },
    "florestas_publicas__min_meio_ambiente": {
        "grupo": "exclusion",
        "backend_table": "vetor_mma_florestas_publicas",
        "available": True,
    },
    "diverso__cprm": {
        "grupo": "analysis",
        "backend_table": "vetor_cprm_geodiversidade",
        "available": True,
    },
    "diverso__ibge": {
        "grupo": "base",
        "backend_table": "vetor_ibge_biomas",
        "available": True,
    },
}


@dataclass(frozen=True)
class CatalogEntry:
    layer_key: str
    tema: str | None
    plano_informacao: str | None
    fonte: str | None
    fonte_principal: bool
    data_atualizacao_fonte: str | None
    periodicidade: str | None
    segregacao: str | None
    datum: str | None
    epsg: str | None
    formato: str | None
    geometria: str | None
    observacoes: str | None
    endereco: str | None
    grupo: str | None
    data_type: str
    backend_table: str | None
    available: bool


def slugify(value: str) -> str:
    """ASCII, lowercase, underscore-separated slug (accents stripped)."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug_chars = [c if c.isalnum() else "_" for c in ascii_only]
    slug = "".join(slug_chars)
    # Collapse runs of underscores and trim edges.
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped.lower() in _EMPTY_TOKENS:
        return None
    return stripped


def parse_catalog_csv(csv_text: str) -> list[CatalogEntry]:
    """Parses spreadsheet CSV text into catalog entries.

    Handles quoted multi-line cells (via the csv module), derives a unique
    ``layer_key`` per row, and de-duplicates collisions with a numeric suffix.
    The header row is detected and skipped. Rows without a plano/fonte are
    ignored.
    """
    reader = csv.reader(io.StringIO(csv_text))
    entries: list[CatalogEntry] = []
    seen_keys: dict[str, int] = {}
    seen_planos: dict[str, int] = {}

    for index, raw in enumerate(reader):
        if not raw or all(not (c or "").strip() for c in raw):
            continue
        # Skip the header row (first column literally "TEMA").
        if index == 0 and (raw[0] or "").strip().upper() == "TEMA":
            continue
        # Pad/truncate defensively so a malformed row never raises.
        cells = (raw + [None] * _EXPECTED_COLS)[:_EXPECTED_COLS]
        record = {col: _clean(cells[i]) for i, col in enumerate(_COLUMNS)}

        plano = record["plano_informacao"]
        fonte = record["fonte"]
        if not plano and not fonte:
            continue

        # The first source listed for a given plano is the principal one.
        plano_slug = slugify(plano or "sem_plano")
        plano_count = seen_planos.get(plano_slug, 0)
        seen_planos[plano_slug] = plano_count + 1
        fonte_principal = plano_count == 0

        base_key = f"{plano_slug}__{slugify(fonte or 'sem_fonte')}"
        count = seen_keys.get(base_key, 0)
        seen_keys[base_key] = count + 1
        layer_key = base_key if count == 0 else f"{base_key}_{count + 1}"

        overrides = _LAYER_OVERRIDES.get(layer_key, {})
        entries.append(
            CatalogEntry(
                layer_key=layer_key,
                tema=record["tema"],
                plano_informacao=plano,
                fonte=fonte,
                fonte_principal=fonte_principal,
                data_atualizacao_fonte=record["data_atualizacao_fonte"],
                periodicidade=record["periodicidade"],
                segregacao=record["segregacao"],
                datum=record["datum"],
                epsg=record["epsg"],
                formato=record["formato"],
                geometria=record["geometria"],
                observacoes=record["observacoes"],
                endereco=record["endereco"],
                grupo=overrides.get("grupo"),
                data_type=overrides.get("data_type", "vector"),
                backend_table=overrides.get("backend_table"),
                available=overrides.get("available", False),
            )
        )
    return entries


class LayerCatalogService:
    """Reads the spreadsheet CSV and upserts it into the catalog table."""

    def __init__(self, repo: LayerCatalogRepository | None = None) -> None:
        self.repo = repo or LayerCatalogRepository()

    def load_from_text(self, csv_text: str) -> int:
        """Parses and upserts catalog entries, returning the number processed."""
        entries = parse_catalog_csv(csv_text)
        self.repo.upsert_many([asdict(e) for e in entries])
        return len(entries)

    def load_from_file(self, path: str) -> int:
        with open(path, encoding="utf-8") as f:
            return self.load_from_text(f.read())
