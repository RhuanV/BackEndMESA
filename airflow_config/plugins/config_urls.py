"""
Centralized configuration file for external URLs.
Used by Airflow DAGs to download geographic data.
"""

# IBGE URL for acessing 2025 state boundaries
IBGE_STATES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_UF_2025.zip"

# IBGE URL for acessing 2025 municipality boundaries
IBGE_MUNICIPALITIES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip"

# Geofabrik URL for Brazil OSM PBF
GEOFABRIK_BRAZIL_URL = "https://download.geofabrik.de/south-america/brazil-latest.osm.pbf"
GEODIFF_URL = "https://download.geofabrik.de/south-america/brazil-updates"

# Ministério de Transportes URL for downloading railway geometries in Brazil
RAILWAY_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseFerro.zip"

# Ministério de Transportes URL for downloading federal highway geometries in Brazil
FEDERAL_HIGHWAYS_BRAZIL_URL = "https://servicos.dnit.gov.br/dnitcloud/index.php/s/oTpPRmYs5AAdiNr/download?path=%2FSNV%20Bases%20Geom%C3%A9tricas%20(2013-Atual)%20(SHP)&files=202604A.zip"

# Ministério de Transportes URL for downloading waterway geometries in Brazil
WATERWAYS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroHidrovias.zip"

# Ministério de Transportes URL for downloading port geometries in Brazil
PORTS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroPortos.zip"

# FUNAI GeoServer WFS - Terra Indígena (Indigenous Lands) polygons
TERRA_INDIGENA_URL = "https://geoserver.funai.gov.br/geoserver/Funai/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=Funai:tis_poligonais&maxFeatures=10000&outputFormat=SHAPE-ZIP"

# ICMBio - Mapa de Potencialidades de Ocorrência de Cavernas
CAVERNAS_URL = "https://www.gov.br/icmbio/pt-br/assuntos/centros-de-pesquisa/cavernas/publicacoes/mapa-de-potencialidades-de-ocorrencia-de-cavernas-no-brasil/dados-mapa-de-potencialidades-de-ocorrencia-de-cavermas-no-brasil.zip"

# ANA/SNIRH - Rios (Base Hidrográfica Ottocodificada - BHO)
RIOS_ANA_URL = "https://metadados.snirh.gov.br/geonetwork/srv/api/records/a01764d3-4742-4f7d-b867-01bf544dde6d/attachments/GEOFT_BHO_REF_RIO.zip"

# ANAC - Lista de Aeródromos Públicos (CSV with coordinates)
AEROPORTOS_GOV_URL = "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/AerodromosPublicos.csv"

# ANA/SNIRH - Aeródromos (airfields)
AERODROMOS_ANA_URL = "https://metadados.snirh.gov.br/geonetwork/srv/api/records/ce6bb0fe-ccfc-4cbf-9ff6-929ba80b47db/attachments/GEOFT_AERODROMO.zip"

# ANEEL SIGEL ArcGIS REST API - Linhas de Transmissão (query endpoint)
LINHAS_TRANSMISSAO_GOV_URL = "https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmiss%C3%A3o/MapServer/1/query"