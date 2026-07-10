"""create mesa_a schema and raw vetorial tables

Revision ID: 0008
Revises: 0006
Create Date: 2026-07-08
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0008"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE SCHEMA IF NOT EXISTS mesa_a;"))

    # --- Unidades territoriais ---
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_limites_estaduais (
            gid SERIAL PRIMARY KEY,
            codigo_ibge VARCHAR(10),
            nome_estado VARCHAR(100),
            sigla_estado VARCHAR(2),
            geom GEOMETRY(MULTIPOLYGON, 4674) NOT NULL
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_limites_estaduais_geom
        ON mesa_a.vetor_limites_estaduais USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_limites_municipais (
            gid SERIAL PRIMARY KEY,
            codigo_ibge VARCHAR(10),
            nome_municipio VARCHAR(150),
            sigla_estado VARCHAR(2),
            geom GEOMETRY(MULTIPOLYGON, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_limites_municipais_geom
        ON mesa_a.vetor_limites_municipais USING GIST (geom);
    """)
    )

    # --- Infraestrutura ---
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_aeroportos (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            icao VARCHAR(10),
            iata VARCHAR(10),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_aeroportos_geom
        ON mesa_a.vetor_osm_aeroportos USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_rodovias_federais (
            gid SERIAL PRIMARY KEY,
            uf VARCHAR(50),
            br VARCHAR(50),
            codigo VARCHAR(50),
            superficie VARCHAR(255),
            extensao DOUBLE PRECISION,
            jurisdicao VARCHAR(255),
            geom GEOMETRY(MultiLineString, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_rodovias_federais_geom
        ON mesa_a.vetor_gov_rodovias_federais USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_ferrovias (
            gid SERIAL PRIMARY KEY,
            uf VARCHAR(50),
            nome TEXT,
            sigla VARCHAR(50),
            bitola VARCHAR(100),
            extensao DOUBLE PRECISION,
            municipio VARCHAR(255),
            geom GEOMETRY(MultiLineString, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_ferrovias_geom
        ON mesa_a.vetor_gov_ferrovias USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_hidrovias (
            gid SERIAL PRIMARY KEY,
            idhidrovia BIGINT,
            nome TEXT,
            tipo VARCHAR(255),
            nome_rio TEXT,
            estudos VARCHAR(255),
            extensao DOUBLE PRECISION,
            classificacao VARCHAR(255),
            est_origem VARCHAR(2),
            est_destino VARCHAR(2),
            geom GEOMETRY(MultiLineString, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_hidrovias_geom
        ON mesa_a.vetor_gov_hidrovias USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_portos (
            gid SERIAL PRIMARY KEY,
            nome TEXT,
            tipo VARCHAR(255),
            fonte VARCHAR(255),
            gestao VARCHAR(255),
            cidade VARCHAR(255),
            estado VARCHAR(2),
            endereco TEXT,
            numero VARCHAR(50),
            bairro VARCHAR(255),
            cep VARCHAR(20),
            cnpj VARCHAR(50),
            idcidade VARCHAR(50),
            geom GEOMETRY(Point, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_portos_geom
        ON mesa_a.vetor_gov_portos USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_portos (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome_porto VARCHAR(255),
            tipo_porto VARCHAR(100),
            uf CHAR(2),
            geom GEOMETRY(Point, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_portos_geom
        ON mesa_a.vetor_osm_portos USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_rodovias_federais (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            referencia VARCHAR(50),
            tipo_rodovia VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_rodovias_federais_geom
        ON mesa_a.vetor_osm_rodovias_federais USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_rodovias_estaduais (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            referencia VARCHAR(50),
            tipo_rodovia VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_rodovias_estaduais_geom
        ON mesa_a.vetor_osm_rodovias_estaduais USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_ferrovias (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            tipo_ferrovia VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_ferrovias_geom
        ON mesa_a.vetor_osm_ferrovias USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_hidrovias (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            tipo_hidrovia VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_hidrovias_geom
        ON mesa_a.vetor_osm_hidrovias USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_linhas_transmissao (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            nome VARCHAR(255),
            tipo_energia VARCHAR(50),
            geom GEOMETRY(GEOMETRY, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_osm_linhas_transmissao_geom
        ON mesa_a.vetor_osm_linhas_transmissao USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_osm_dutos (
            gid SERIAL PRIMARY KEY,
            osm_id BIGINT UNIQUE NOT NULL,
            substancia VARCHAR(50),
            operador VARCHAR(150),
            geom GEOMETRY(MultiLineString, 4326)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_dutos_osm_geom
        ON mesa_a.vetor_osm_dutos USING GIST (geom);
    """)
    )

    # --- Meio ambiente / unidades territoriais ---
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_uc (
            gid SERIAL PRIMARY KEY,
            nome_uc VARCHAR(255),
            categoria VARCHAR(100),
            esfera VARCHAR(50),
            ano_criacao INTEGER,
            geom GEOMETRY(MultiPolygon, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_uc_gov_geom
        ON mesa_a.vetor_gov_uc USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_sicar_imoveis (
            gid SERIAL PRIMARY KEY,
            codigo_imovel VARCHAR(100) UNIQUE NOT NULL,
            status_imovel VARCHAR(10),
            data_criacao TIMESTAMP,
            data_atualizacao TIMESTAMP,
            area_hectares DOUBLE PRECISION,
            condicao_analise VARCHAR(150),
            uf CHAR(2),
            municipio VARCHAR(150),
            codigo_municipio INTEGER,
            modulo_fiscal DOUBLE PRECISION,
            tipo_imovel VARCHAR(50),
            geom GEOMETRY(MultiPolygon, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_sicar_imoveis_geom
        ON mesa_a.vetor_gov_sicar_imoveis USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_terra_indigena (
            gid SERIAL PRIMARY KEY,
            nome_ti VARCHAR(255),
            etnia VARCHAR(255),
            municipio VARCHAR(255),
            uf VARCHAR(100),
            situacao_juridica VARCHAR(255),
            fase VARCHAR(255),
            modalidade VARCHAR(255),
            superficie_ha DOUBLE PRECISION,
            geom GEOMETRY(MultiPolygon, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_terra_indigena_geom
        ON mesa_a.vetor_gov_terra_indigena USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_cavernas (
            gid SERIAL PRIMARY KEY,
            nome_caverna VARCHAR(255),
            municipio VARCHAR(255),
            uf VARCHAR(100),
            litologia VARCHAR(255),
            grau_potencial VARCHAR(255),
            geom GEOMETRY(MultiPolygon, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_cavernas_geom
        ON mesa_a.vetor_gov_cavernas USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_rios_ana (
            gid SERIAL PRIMARY KEY,
            nome_rio VARCHAR(255),
            cocurso VARCHAR(50),
            corio VARCHAR(50),
            nucompam VARCHAR(50),
            nuareaam DOUBLE PRECISION,
            geom GEOMETRY(MultiLineString, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_rios_ana_geom
        ON mesa_a.vetor_gov_rios_ana USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_aeroportos (
            gid SERIAL PRIMARY KEY,
            nome VARCHAR(255),
            municipio VARCHAR(255),
            uf VARCHAR(100),
            codigo_iata VARCHAR(10),
            codigo_icao VARCHAR(10),
            tipo VARCHAR(255),
            geom GEOMETRY(Point, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_aeroportos_geom
        ON mesa_a.vetor_gov_aeroportos USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_aerodromos (
            gid SERIAL PRIMARY KEY,
            nome VARCHAR(255),
            municipio VARCHAR(255),
            uf VARCHAR(100),
            situacao VARCHAR(255),
            geom GEOMETRY(MultiPoint, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_aerodromos_geom
        ON mesa_a.vetor_gov_aerodromos USING GIST (geom);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.vetor_gov_linhas_transmissao (
            gid SERIAL PRIMARY KEY,
            nome_linha VARCHAR(255),
            operador VARCHAR(255),
            tensao VARCHAR(100),
            situacao VARCHAR(255),
            geom GEOMETRY(MultiLineString, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_gov_linhas_transmissao_geom
        ON mesa_a.vetor_gov_linhas_transmissao USING GIST (geom);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP SCHEMA IF EXISTS mesa_a CASCADE;"))
