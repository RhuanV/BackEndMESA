# Contexto do Projeto: GeoAvia (MESA-Auto)

## Visão Geral
Este projeto é uma parceria SAC/ANAC/ITA para automatizar a prospecção de sítios aeroportuários usando a metodologia MESA.

## Stack Técnica
- **Backend:** FastAPI (Python 3.12)
- **Banco de Dados:** PostgreSQL (futuro PostGIS) via Docker.
- **Arquitetura:** Camadas (Main/API -> Service -> Repository).

## Regras de Implementação
1. **Repository:** Apenas SQL puro usando `psycopg2-binary`. Não usar ORM por enquanto para manter performance geográfica.
2. **Service:** Local exclusivo para regras de negócio da MESA (Critérios Eliminatórios e Classificatórios).
3. **Ambiente:** Tudo deve ser compatível com Docker Compose. As credenciais devem vir sempre do `.env`.

## Padrões de Código
- Use tipos do Python (Type Hints) em todas as funções.
- Docstrings em português para explicar a lógica aeronáutica.