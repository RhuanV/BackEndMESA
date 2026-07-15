"""
Centralized configuration file for external URLs.
Used by Airflow DAGs to download geographic data.
"""

import os

# IBGE URL for acessing 2025 state boundaries
IBGE_STATES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_UF_2025.zip"

# IBGE URL for acessing 2025 municipality boundaries
IBGE_MUNICIPALITIES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip"

# Geofabrik URL for Brazil OSM PBF
GEOFABRIK_BRAZIL_URL = "https://download.geofabrik.de/south-america/brazil-latest.osm.pbf"
GEODIFF_URL = "https://download.geofabrik.de/south-america/brazil-updates"

# Ministry of Transport URL for downloading railway geometries in Brazil
RAILWAY_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseFerro.zip"

# Ministry of Transport URL for downloading federal highway geometries in Brazil
FEDERAL_HIGHWAYS_BRAZIL_URL = "https://servicos.dnit.gov.br/dnitcloud/index.php/s/oTpPRmYs5AAdiNr/download?path=%2FSNV%20Bases%20Geom%C3%A9tricas%20(2013-Atual)%20(SHP)&files=202604A.zip"

# Ministry of Transport URL for downloading waterway geometries in Brazil
WATERWAYS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroHidrovias.zip"

# Ministry of Transport URL for downloading port geometries in Brazil
PORTS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroPortos.zip"

# ICMBio URL for downloading Federal Conservation Units geometries in Brazil
FEDERAL_UCS_BRAZIL_URL = "https://www.gov.br/icmbio/pt-br/dados-icmbio/dados_geoespaciais/mapa-tematico-e-dados-geoestatisticos-das-unidades-de-conservacao-federais/limite_ucs_federais_052026_a.zip"

# SICAR URL template for downloading properties boundaries by state (AC, AL, etc.)
SICAR_STATE_URL_TEMPLATE = "https://geoserver.car.gov.br/geoserver/sicar/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=sicar%3Asicar_imoveis_{state}&outputFormat=SHAPE-ZIP"
# FUNAI GeoServer WFS - Indigenous Lands (Terra Indígena) polygons
TERRA_INDIGENA_URL = "https://geoserver.funai.gov.br/geoserver/Funai/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=Funai:tis_poligonais&maxFeatures=10000&outputFormat=SHAPE-ZIP"

# ICMBio - Cave Occurrence Potential Map (Mapa de Potencialidades de Ocorrência de Cavernas)
CAVERNAS_URL = "https://www.gov.br/icmbio/pt-br/assuntos/centros-de-pesquisa/cavernas/publicacoes/mapa-de-potencialidades-de-ocorrencia-de-cavernas-no-brasil/dados-mapa-de-potencialidades-de-ocorrencia-de-cavermas-no-brasil.zip"

# ANA/SNIRH - Rivers (Base Hidrográfica Ottocodificada - BHO)
RIOS_ANA_URL = "https://metadados.snirh.gov.br/geonetwork/srv/api/records/a01764d3-4742-4f7d-b867-01bf544dde6d/attachments/GEOFT_BHO_REF_RIO.zip"

# ANAC - Public Airfields List (Lista de Aeródromos Públicos, CSV with coordinates)
AEROPORTOS_GOV_URL = "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/AerodromosPublicos.csv"

# ANA/SNIRH - Airfields (Aeródromos)
AERODROMOS_ANA_URL = "https://metadados.snirh.gov.br/geonetwork/srv/api/records/ce6bb0fe-ccfc-4cbf-9ff6-929ba80b47db/attachments/GEOFT_AERODROMO.zip"

# ANEEL SIGEL ArcGIS REST API - Transmission Lines (query endpoint)
LINHAS_TRANSMISSAO_GOV_URL = "https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/1/query"

# --- Raster sources (Fase 5) ---
# ANADEM — Modelo Digital de Terreno (MDT) 30 m, UFRGS/HGE. Override with the
# concrete release/tile URL in the environment before running the DAG.
ANADEM_MDT_URL = os.environ.get(
    "ANADEM_MDT_URL",
    "https://www.ufrgs.br/hge/wp-content/uploads/anadem/ANADEM.tif",
)
# MapBiomas — annual land use/cover GeoTIFF (Coleção Brasil). Set the concrete
# collection/year asset URL via the environment before running the DAG.
MAPBIOMAS_LANDUSE_URL = os.environ.get("MAPBIOMAS_LANDUSE_URL", "")
