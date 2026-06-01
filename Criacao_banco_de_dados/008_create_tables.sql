-- Table to store polygons and lines from airports extracted from OpenStreetMap (OSM).
-- Created via Airflow DAG (load_osm_airports).

CREATE TABLE IF NOT EXISTS osm_airports (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    icao VARCHAR(10),
    iata VARCHAR(10),
    geom GEOMETRY(GEOMETRY, 4674)
);

CREATE INDEX IF NOT EXISTS idx_osm_airports_geom ON osm_airports USING GIST (geom);

-- Tabela para Rodovias Federais (Ministério dos Transportes)
CREATE TABLE IF NOT EXISTS gov_federal_highways (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(50),
    br VARCHAR(50),
    codigo VARCHAR(50),
    superficie VARCHAR(255),
    extensao DOUBLE PRECISION,
    jurisdicao VARCHAR(255),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX IF NOT EXISTS idx_gov_highways_geom ON gov_federal_highways USING GIST (geom);

-- Tabela para Ferrovias (Ministério dos Transportes)
CREATE TABLE IF NOT EXISTS gov_railways (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(50),
    nome TEXT,
    sigla VARCHAR(50),
    bitola VARCHAR(100),
    extensao DOUBLE PRECISION,
    municipio VARCHAR(255),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX IF NOT EXISTS idx_gov_railways_geom ON gov_railways USING GIST (geom);

-- Tabela para Hidrovias (Ministério dos Transportes)
CREATE TABLE IF NOT EXISTS gov_waterways (
    id SERIAL PRIMARY KEY,
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
CREATE INDEX IF NOT EXISTS idx_gov_waterways_geom ON gov_waterways USING GIST (geom);

-- Tabela para Portos (Ministério dos Transportes)
CREATE TABLE IF NOT EXISTS gov_ports (
    id SERIAL PRIMARY KEY,
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
CREATE INDEX IF NOT EXISTS idx_gov_ports_geom ON gov_ports USING GIST (geom);

-- Tabela para Rodovias Federais (OpenStreetMap)
CREATE TABLE IF NOT EXISTS osm_federal_highways (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    ref VARCHAR(50),
    highway VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX IF NOT EXISTS idx_osm_federal_highways_geom ON osm_federal_highways USING GIST (geom);

-- Tabela para Rodovias Estaduais (OpenStreetMap)
CREATE TABLE IF NOT EXISTS osm_state_highways (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    ref VARCHAR(50),
    highway VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX IF NOT EXISTS idx_osm_state_highways_geom ON osm_state_highways USING GIST (geom);

-- Tabela para Ferrovias (OpenStreetMap)
CREATE TABLE IF NOT EXISTS osm_railways (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    railway VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);

CREATE INDEX IF NOT EXISTS idx_osm_railways_geom ON osm_railways USING GIST (geom);

-- Tabela para Hidrovias (OpenStreetMap)
CREATE TABLE IF NOT EXISTS osm_waterways (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    waterway VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);

CREATE INDEX IF NOT EXISTS idx_osm_waterways_geom ON osm_waterways USING GIST (geom);

-- Tabela para Linhas de Transmissão (OpenStreetMap)
CREATE TABLE IF NOT EXISTS osm_power_lines (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    power VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);

CREATE INDEX IF NOT EXISTS idx_osm_power_lines_geom ON osm_power_lines USING GIST (geom);
