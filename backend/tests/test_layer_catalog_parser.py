"""Pure tests for the metadata-catalog CSV parser (no DB, no network)."""

from geoavia_backend.services.layer_catalog import parse_catalog_csv, slugify

# Minimal CSV mirroring the real spreadsheet layout, including a quoted
# multi-line observation cell and a duplicate (plano, fonte) pair.
_CSV = (
    "TEMA,PLANO DE INFORMAÇÃO,DATA DA ÚLTIMA ATUALIZAÇÃO NA FONTE DE DADOS,"
    "PERIODICIDADE DE ATUALIZAÇÃO DA INFORMAÇÃO,FONTE,SEGREGAÇÃO DOS DADOS,"
    "SISTEMA DE REFERÊNCIA/ DATUM,EPSG,FORMATO DO ARQUIVO,GEOMETRIA DO DADO,"
    "OBSERVAÇÕES,ENDEREÇO\n"
    "Unidades Territoriais,Estado,2024,Anual,IBGE,Estadual,SIRGAS 2000,4674,"
    "Shapefile,Polígono,-,https://ibge.gov.br/estados\n"
    "Unidades Territoriais,Município,2024,Anual,IBGE,Municipal,SIRGAS 2000,4674,"
    'Shapefile,Polígono,"linha 1\n\nlinha 2",https://ibge.gov.br/municipios\n'
    "Hidrografia,Rios,2025,Mensal,SICAR,Estadual,SIRGAS 2000,Personalizado,"
    "Shapefile,Polígono,-,http://car.gov.br\n"
    "Hidrografia,Rios,2012,Não há,ANA,Estadual,SAD69,Personalizado,Shapefile,"
    "Linha,-,https://snirh.gov.br\n"
)


def test_slugify_strips_accents_and_lowercases():
    assert slugify("Município") == "municipio"
    assert slugify("Rios / Nascentes") == "rios_nascentes"


def test_parses_all_rows_and_skips_header():
    entries = parse_catalog_csv(_CSV)
    assert len(entries) == 4


def test_layer_key_derivation_and_dedup():
    entries = parse_catalog_csv(_CSV)
    keys = [e.layer_key for e in entries]
    assert keys[0] == "estado__ibge"
    assert keys[1] == "municipio__ibge"
    # Two different sources for "Rios" -> unique keys.
    assert keys[2] == "rios__sicar"
    assert keys[3] == "rios__ana"


def test_known_layer_gets_operational_overrides():
    entries = {e.layer_key: e for e in parse_catalog_csv(_CSV)}
    estado = entries["estado__ibge"]
    assert estado.grupo == "base"
    assert estado.backend_table == "state_boundaries"
    assert estado.available is True
    # An unmapped layer defaults to unavailable vector with no group.
    rios = entries["rios__sicar"]
    assert rios.available is False
    assert rios.grupo is None
    assert rios.data_type == "vector"


def test_empty_tokens_become_none_and_multiline_preserved():
    entries = {e.layer_key: e for e in parse_catalog_csv(_CSV)}
    assert entries["estado__ibge"].observacoes is None  # "-" -> None
    assert "linha 2" in entries["municipio__ibge"].observacoes


def test_fonte_principal_is_first_source_per_plano():
    entries = {e.layer_key: e for e in parse_catalog_csv(_CSV)}
    assert entries["rios__sicar"].fonte_principal is True
    assert entries["rios__ana"].fonte_principal is False
