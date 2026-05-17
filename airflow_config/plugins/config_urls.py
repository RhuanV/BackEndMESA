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

# Ministério de Transportes URL for downloading railway geometries in Brazil
RAILWAY_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseFerro.zip"

# Ministério de Transportes URL for downloading federal highway geometries in Brazil
FEDERAL_HIGHWAYS_BRAZIL_URL = "https://servicos.dnit.gov.br/dnitcloud/index.php/s/oTpPRmYs5AAdiNr/download?path=%2FSNV%20Bases%20Geom%C3%A9tricas%20(2013-Atual)%20(SHP)&files=202604A.zip"

# Ministério de Transportes URL for downloading waterway geometries in Brazil
WATERWAYS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroHidrovias.zip"

# Ministério de Transportes URL for downloading port geometries in Brazil
PORTS_BRAZIL_URL = "https://www.gov.br/transportes/pt-br/assuntos/dados-de-transportes/bit/Base-GEO/BaseHidroPortos.zip"