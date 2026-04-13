"""
Centralized configuration file for external URLs.
Used by Airflow DAGs to download geographic data.
"""

# IBGE URL for acessing 2025 state boundaries
IBGE_STATES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_UF_2025.zip"

# IBGE URL for acessing 2025 municipality boundaries
IBGE_MUNICIPALITIES_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip"
