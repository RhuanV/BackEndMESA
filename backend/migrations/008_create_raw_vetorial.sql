-- =============================================================================
-- Tabelas adicionais de dados governamentais e do OpenStreetMap (OSM)
-- Segue o padrão de nomenclatura do esquema mesa_a
-- =============================================================================

-- Criar o esquema MESA-A
CREATE SCHEMA IF NOT EXISTS mesa_a;


-- =============================================================================
-- Tema: Unidades territoriais
-- =============================================================================


-- Tabela para os limites estaduais (IBGE)
CREATE TABLE mesa_a.vetor_limites_estaduais (
    gid SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(10),
    nome_estado VARCHAR(100),
    sigla_estado VARCHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4674) NOT NULL
);
CREATE INDEX idx_limites_estaduais_geom ON mesa_a.vetor_limites_estaduais USING GIST(geom);

-- Tabela para os limites municipais (IBGE)
CREATE TABLE mesa_a.vetor_limites_municipais (
    gid SERIAL PRIMARY KEY,
    codigo_ibge VARCHAR(10),
    nome_municipio VARCHAR(150),
    sigla_estado VARCHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4674)
);
CREATE INDEX idx_limites_municipais_geom ON mesa_a.vetor_limites_municipais USING GIST(geom);



-- =============================================================================
-- Tema: Hidrografia, fauna e flora
-- =============================================================================




-- =============================================================================
-- Tema: Infraestrutura
-- =============================================================================

-- Tabela para armazenar polígonos e linhas de aeroportos extraídos do OpenStreetMap (OSM).
-- Criado via Airflow DAG (load_osm_airports).
CREATE TABLE mesa_a.vetor_osm_aeroportos (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    icao VARCHAR(10),
    iata VARCHAR(10),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_aeroportos_geom ON mesa_a.vetor_osm_aeroportos USING GIST(geom);

-- Tabela para Rodovias Federais (Ministério dos Transportes)
CREATE TABLE mesa_a.vetor_gov_rodovias_federais (
    gid SERIAL PRIMARY KEY,
    uf VARCHAR(50),
    br VARCHAR(50),
    codigo VARCHAR(50),
    superficie VARCHAR(255),
    extensao DOUBLE PRECISION,
    jurisdicao VARCHAR(255),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_gov_rodovias_federais_geom ON mesa_a.vetor_gov_rodovias_federais USING GIST(geom);

-- Tabela para Ferrovias (Ministério dos Transportes)
CREATE TABLE mesa_a.vetor_gov_ferrovias (
    gid SERIAL PRIMARY KEY,
    uf VARCHAR(50),
    nome TEXT,
    sigla VARCHAR(50),
    bitola VARCHAR(100),
    extensao DOUBLE PRECISION,
    municipio VARCHAR(255),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_gov_ferrovias_geom ON mesa_a.vetor_gov_ferrovias USING GIST(geom);

-- Tabela para Hidrovias (Ministério dos Transportes)
CREATE TABLE mesa_a.vetor_gov_hidrovias (
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
CREATE INDEX idx_gov_hidrovias_geom ON mesa_a.vetor_gov_hidrovias USING GIST(geom);

-- Tabela para Portos (Ministério dos Transportes)
CREATE TABLE mesa_a.vetor_gov_portos (
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
CREATE INDEX idx_gov_portos_geom ON mesa_a.vetor_gov_portos USING GIST(geom);

-- Tabela para Rodovias Federais (OpenStreetMap)
CREATE TABLE mesa_a.vetor_osm_rodovias_federais (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    referencia VARCHAR(50),
    tipo_rodovia VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_rodovias_federais_geom ON mesa_a.vetor_osm_rodovias_federais USING GIST(geom);

-- Tabela para Rodovias Estaduais (OpenStreetMap)
CREATE TABLE mesa_a.vetor_osm_rodovias_estaduais (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    referencia VARCHAR(50),
    tipo_rodovia VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_rodovias_estaduais_geom ON mesa_a.vetor_osm_rodovias_estaduais USING GIST(geom);

-- Tabela para Ferrovias (OpenStreetMap)
CREATE TABLE mesa_a.vetor_osm_ferrovias (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    tipo_ferrovia VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_ferrovias_geom ON mesa_a.vetor_osm_ferrovias USING GIST(geom);

-- Tabela para Hidrovias (OpenStreetMap)
CREATE TABLE mesa_a.vetor_osm_hidrovias (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    tipo_hidrovia VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_hidrovias_geom ON mesa_a.vetor_osm_hidrovias USING GIST(geom);

-- Tabela para Linhas de Transmissão (OpenStreetMap)
CREATE TABLE mesa_a.vetor_osm_linhas_transmissao (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE NOT NULL,
    nome VARCHAR(255),
    tipo_energia VARCHAR(50),
    geom GEOMETRY(GEOMETRY, 4674)
);
CREATE INDEX idx_osm_linhas_transmissao_geom ON mesa_a.vetor_osm_linhas_transmissao USING GIST(geom);
