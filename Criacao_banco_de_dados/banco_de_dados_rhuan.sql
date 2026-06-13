-- Habilitar extensões do PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Criar o esquema MESA-A
CREATE SCHEMA IF NOT EXISTS mesa_a;


-- Tabela de controle de metadados da MESA-A
CREATE TABLE mesa_a.controle_metadados (
    id SERIAL PRIMARY KEY,
    "TEMA" VARCHAR(255),
    "PLANO DE INFORMAÇÃO" VARCHAR(255),
    "DATA DA ÚLTIMA ATUALIZAÇÃO NA FONTE DE DADOS" VARCHAR(100),
    "PERIODICIDADE DE ATUALIZAÇÃO DA INFORMAÇÃO" VARCHAR(100),
    "FONTE" VARCHAR(100),
    "SEGREGAÇÃO DOS DADOS" VARCHAR(100), -- Específico Vetorial
    "LICENCIAMENTO" VARCHAR(100), -- Específico Matricial
    "NECESSIDADE DE LOGIN PARA ACESSO" CHAR(1), -- Específico Matricial
    "FORMA DE ACESSO" VARCHAR(100), -- Específico Matricial
    "SISTEMA DE REFERÊNCIA/ DATUM" VARCHAR(100),
    "EPSG" VARCHAR(20),
    "FORMATO DO ARQUIVO" VARCHAR(50),
    "GEOMETRIA DO DADO" VARCHAR(50), -- Específico Vetorial
    "TIPO DE SENSOR" VARCHAR(150), -- Específico Matricial
    "NÚMERO DE BANDAS" VARCHAR(50), -- Específico Matricial
    "DESCRIÇÃO ESPECTRAL DAS BANDAS" TEXT, -- Específico Matricial
    "RESOLUÇÃO ESPACIAL" VARCHAR(50), -- Específico Matricial
    "RESOLUÇÃO TEMPORAL" VARCHAR(50), -- Específico Matricial
    "RESOLUÇÃO RADIOMÉTRICA" VARCHAR(50), -- Específico Matricial
    "COBERTURA TEMPORAL" VARCHAR(100), -- Específico Matricial
    "OBSERVAÇÕES" TEXT,
    "ENDEREÇO" TEXT,
    data_carga_airflow TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tema: Unidades territoriais

-- Tabela para o Plano de Informação: Estado
CREATE TABLE mesa_a.vetor_estado (
    gid SERIAL PRIMARY KEY,
    nome_estado VARCHAR(100),
    sigla_uf CHAR(2),
    codigo_ibge VARCHAR(2),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_estado_geom ON mesa_a.vetor_estado USING GIST(geom);


-- Tabela para o Plano de Informação: Município
CREATE TABLE mesa_a.vetor_municipio (
    gid SERIAL PRIMARY KEY,
    nome_municipio VARCHAR(150),
    codigo_ibge VARCHAR(7),
    sigla_uf CHAR(2),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_municipio_geom ON mesa_a.vetor_municipio USING GIST(geom);


-- Tabela para o Plano de Informação: Setores Censitários
CREATE TABLE mesa_a.vetor_setores_censitarios (
    gid SERIAL PRIMARY KEY,
    cd_setor VARCHAR(20),
    nm_municipio VARCHAR(150),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_setores_geom ON mesa_a.vetor_setores_censitarios USING GIST(geom);


-- Tabelas para o Plano de Informação: Área do Imóvel (SICAR e INCRA)
CREATE TABLE mesa_a.vetor_area_do_imovel_sicar (
    gid SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(100),
    num_certificado VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);

CREATE TABLE mesa_a.vetor_area_do_imovel_incra (
    gid SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);

-- Tabelas para as áreas de proteção ambiental (APA) e unidades de conservação (UC)

-- Tabela para o Plano de Informação: UC - Todas
CREATE TABLE mesa_a.vetor_uc_todas (
    gid SERIAL PRIMARY KEY,
    nome_uc VARCHAR(255),
    categoria VARCHAR(100),
    esfera VARCHAR(50), -- Federal, Estadual, Municipal
    ano_criacao INTEGER,
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_uc_todas_geom ON mesa_a.vetor_uc_todas USING GIST(geom);

-- Tabela para o Plano de Informação: Área de Preservação Permanente (APP)
CREATE TABLE mesa_a.vetor_app (
    gid SERIAL PRIMARY KEY,
    geom GEOMETRY(MultiPolygon, 4674)
);

-- Tabela para o Plano de Informação: Reserva Legal
CREATE TABLE mesa_a.vetor_reserva_legal (
    gid SERIAL PRIMARY KEY,
    geom GEOMETRY(MultiPolygon, 4674)
);

-- Tabela para o Plano de Informação: Terra Indígena (FUNAI)
CREATE TABLE mesa_a.vetor_terra_indigena (
    gid SERIAL PRIMARY KEY,
    nome_ti VARCHAR(200),
    etnia VARCHAR(200),
    geom GEOMETRY(MultiPolygon, 4674)
);

-- Tabela para o Plano de Informação: Terras Quilombolas (INCRA)
CREATE TABLE mesa_a.vetor_terra_quilombola (
    gid SERIAL PRIMARY KEY,
    nome_comunidade VARCHAR(255),
    processo_incra VARCHAR(100),
    fase_processo VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_terra_quilombola_geom ON mesa_a.vetor_terra_quilombola USING GIST(geom);


-- Tabela para o Plano de Informação: Assentamentos
CREATE TABLE mesa_a.vetor_assentamentos (
    gid SERIAL PRIMARY KEY,
    nome_projeto VARCHAR(255),
    codigo_incra VARCHAR(50),
    data_criacao DATE,
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_assentamentos_geom ON mesa_a.vetor_assentamentos USING GIST(geom);

-- Tabela para o Plano de Informação: Florestas Públicas
CREATE TABLE mesa_a.vetor_florestas_publicas (
    gid SERIAL PRIMARY KEY,
    nome_floresta VARCHAR(255),
    tipo_floresta VARCHAR(100), -- Federal, Estadual, Municipal
    status VARCHAR(50),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_florestas_publicas_geom ON mesa_a.vetor_florestas_publicas USING GIST(geom);

-- Tabela para o Plano de Informação: Cavernas
CREATE TABLE mesa_a.vetor_cavernas (
    gid SERIAL PRIMARY KEY,
    nome_caverna VARCHAR(255),
    municipio VARCHAR(150),
    classificacao VARCHAR(100),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_cavernas_geom ON mesa_a.vetor_cavernas USING GIST(geom);


----------------------------------------------------------------------------------------------
-- Tema: Hidrografia, fauna e flora
-- Tabela para o Plano de Informação: Rios (SICAR)
CREATE TABLE mesa_a.vetor_rios_sicar (
    gid SERIAL PRIMARY KEY,
    nm_rio VARCHAR(255),
    origem VARCHAR(50) DEFAULT 'SICAR',
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_rios_sicar_geom ON mesa_a.vetor_rios_sicar USING GIST(geom);

-- Tabela para o Plano de Informação: Rios (ANA)
CREATE TABLE mesa_a.vetor_rios_ana (
    gid SERIAL PRIMARY KEY,
    nome_rio VARCHAR(255),
    cocurso VARCHAR(50),
    origem VARCHAR(50) DEFAULT 'ANA',
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_rios_ana_geom ON mesa_a.vetor_rios_ana USING GIST(geom);

-- Tabela para o Plano de Informação: Banhados
CREATE TABLE mesa_a.vetor_banhados (
    gid SERIAL PRIMARY KEY,
    tipo_zona_umida VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_banhados_geom ON mesa_a.vetor_banhados USING GIST(geom);

-- Tabela para o Plano de Informação: Vegetação Nativa
CREATE TABLE mesa_a.vetor_vegetacao_nativa (
    gid SERIAL PRIMARY KEY,
    tipo_formacao VARCHAR(150),
    estagio_regeneracao VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_veg_nativa_geom ON mesa_a.vetor_vegetacao_nativa USING GIST(geom);

-- Tabela para o Plano de Informação: Área de Pousio
CREATE TABLE mesa_a.vetor_area_pousio (
    gid SERIAL PRIMARY KEY,
    data_identificacao DATE,
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_pousio_geom ON mesa_a.vetor_area_pousio USING GIST(geom);

-- Tabela para o Plano de Informação: Aves (Focos de Atratividade / ASA)
CREATE TABLE mesa_a.vetor_aves (
    gid SERIAL PRIMARY KEY,
    descricao_foco VARCHAR(255), -- Ex: Lixão, Abatedouro, Área de nidificação
    raio_influencia_km DOUBLE PRECISION,
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_aves_geom ON mesa_a.vetor_aves USING GIST(geom);

-- Tabela para o Plano de Informação: Lagos
CREATE TABLE mesa_a.vetor_lagos (
    gid SERIAL PRIMARY KEY,
    nome_corpo_agua VARCHAR(255),
    tipo_corpo_agua VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_lagos_geom ON mesa_a.vetor_lagos USING GIST(geom);

-- Tabela para o Plano de Informação: Nascentes
CREATE TABLE mesa_a.vetor_nascentes (
    gid SERIAL PRIMARY KEY,
    status_nascente VARCHAR(100),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_nascentes_geom ON mesa_a.vetor_nascentes USING GIST(geom);


-- =============================================================================
-- Tema: Infraestrutura
-- =============================================================================

-- Tabela para o Plano de Informação: Aeroportos (Ministério da Infraestrutura)
CREATE TABLE mesa_a.vetor_aeroportos (
    gid SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    municipio VARCHAR(150),
    uf CHAR(2),
    codigo_iata VARCHAR(10),
    codigo_icao VARCHAR(10),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_aeroportos_geom ON mesa_a.vetor_aeroportos USING GIST(geom);

-- Tabela para o Plano de Informação: Aeroportos (OpenStreetMap)
-- Observação: Definido como MultiPolygon para abranger áreas de sítios aeroportuários
CREATE TABLE mesa_a.vetor_aeroportos_osm (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT,
    name VARCHAR(255),
    type VARCHAR(50),
    geom GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_aeroportos_osm_geom ON mesa_a.vetor_aeroportos_osm USING GIST(geom);

-- Tabela para o Plano de Informação: Aeródromos (ANA)
CREATE TABLE mesa_a.vetor_aerodromos (
    gid SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    situacao VARCHAR(100),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_aerodromos_geom ON mesa_a.vetor_aerodromos USING GIST(geom);

-- Tabela para o Plano de Informação: Rodovias Federais (Ministério da Infraestrutura / BIT)
CREATE TABLE mesa_a.vetor_rodovias_federais (
    gid SERIAL PRIMARY KEY,
    vl_br VARCHAR(10),
    ds_superv VARCHAR(100),
    ds_tipo_adm VARCHAR(50),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_rodovias_federais_geom ON mesa_a.vetor_rodovias_federais USING GIST(geom);

-- Tabela para o Plano de Informação: Rodovias Federais e Estaduais (OpenStreetMap)
CREATE TABLE mesa_a.vetor_rodovias_osm (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT,
    name VARCHAR(255),
    highway VARCHAR(50),
    ref VARCHAR(20),
    geom GEOMETRY(MultiLineString, 4326)
);
CREATE INDEX idx_rodovias_osm_geom ON mesa_a.vetor_rodovias_osm USING GIST(geom);

-- Tabela para o Plano de Informação: Ferrovias (Ministério da Infraestrutura)
CREATE TABLE mesa_a.vetor_ferrovias (
    gid SERIAL PRIMARY KEY,
    extensao_km DECIMAL(10,2),
    concessionaria VARCHAR(150),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_ferrovias_geom ON mesa_a.vetor_ferrovias USING GIST(geom);

-- Tabela para o Plano de Informação: Ferrovias (OpenStreetMap)
CREATE TABLE mesa_a.vetor_ferrovias_osm (
    gid SERIAL PRIMARY KEY,
    extensao_km DECIMAL(10,2),
    concessionaria VARCHAR(150),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_ferrovias_osm_geom ON mesa_a.vetor_ferrovias_osm USING GIST(geom);



-- Tabela para o Plano de Informação: Hidrovias (Ministério da Infraestrutura)
CREATE TABLE mesa_a.vetor_hidrovias (
    gid SERIAL PRIMARY KEY,
    nome_rio VARCHAR(255),
    status_navegabilidade VARCHAR(100),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_hidrovias_geom ON mesa_a.vetor_hidrovias USING GIST(geom);


-- Tabela para o Plano de Informação: Hidrovias (OpenStreetMap)
CREATE TABLE mesa_a.vetor_hidrovias_osm (
    gid SERIAL PRIMARY KEY,
    nome_rio VARCHAR(255),
    status_navegabilidade VARCHAR(100),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_hidrovias_osm_geom ON mesa_a.vetor_hidrovias_osm USING GIST(geom);


-- Tabela para o Plano de Informação: Dutos (OpenStreetMap)
CREATE TABLE mesa_a.vetor_dutos (
    gid SERIAL PRIMARY KEY,
    osm_id BIGINT,
    substance VARCHAR(50),
    operator VARCHAR(150),
    geom GEOMETRY(MultiLineString, 4326)
);
CREATE INDEX idx_dutos_geom ON mesa_a.vetor_dutos USING GIST(geom);

-- Tabela para o Plano de Informação: Portos (Ministério da Infraestrutura)
CREATE TABLE mesa_a.vetor_portos (
    gid SERIAL PRIMARY KEY,
    nome_porto VARCHAR(255),
    tipo_porto VARCHAR(100),
    uf CHAR(2),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_portos_geom ON mesa_a.vetor_portos USING GIST(geom);

-- Tabela para o Plano de Informação: Portos (OpenStreetMap)
CREATE TABLE mesa_a.vetor_portos_osm (
    gid SERIAL PRIMARY KEY,
    nome_porto VARCHAR(255),
    tipo_porto VARCHAR(100),
    uf CHAR(2),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_portos_osm_geom ON mesa_a.vetor_portos_osm USING GIST(geom);


-- =============================================================================
-- Tabelas adicionais de dados vetoriais da CSV da metodologia MESA
-- =============================================================================

-- Tabela para o Plano de Informação: Geodiversidade
CREATE TABLE mesa_a.vetor_geodiversidade (
    gid SERIAL PRIMARY KEY,
    descricao VARCHAR(255),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_geodiversidade_geom ON mesa_a.vetor_geodiversidade USING GIST(geom);

-- Tabela para o Plano de Informação: Biomas
CREATE TABLE mesa_a.vetor_biomas (
    gid SERIAL PRIMARY KEY,
    nome_bioma VARCHAR(255),
    descricao VARCHAR(255),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_biomas_geom ON mesa_a.vetor_biomas USING GIST(geom);

-- Tabela para o Plano de Informação: Linhas de Transmissão
CREATE TABLE mesa_a.vetor_linhas_transmissao (
    gid SERIAL PRIMARY KEY,
    nome_linha VARCHAR(255),
    operador VARCHAR(150),
    geom GEOMETRY(MultiLineString)
);
CREATE INDEX idx_linhas_transmissao_geom ON mesa_a.vetor_linhas_transmissao USING GIST(geom);

-- Tabela para o Plano de Informação: Linhas de Transmissão (OpenStreetMap)
CREATE TABLE mesa_a.vetor_linhas_transmissao_osm (
    gid SERIAL PRIMARY KEY,
    nome_linha VARCHAR(255),
    operador VARCHAR(150),
    geom GEOMETRY(MultiLineString)
);
CREATE INDEX idx_linhas_transmissao_osm_geom ON mesa_a.vetor_linhas_transmissao_osm USING GIST(geom);

-- Tabela para o Plano de Informação: Dados Anemométricos
CREATE TABLE mesa_a.vetor_dados_anemometricos (
    gid SERIAL PRIMARY KEY,
    descricao VARCHAR(255),
    geom GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_dados_anemometricos_geom ON mesa_a.vetor_dados_anemometricos USING GIST(geom);


-- =============================================================================
-- Tabelas adicionais para DAGs Airflow (prefixo vetor_gov_)
-- =============================================================================

-- Tema: Unidades Territoriais
-- Tabela para o Plano de Informação: Terra Indígena (FUNAI) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_terra_indigena (
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
CREATE INDEX idx_gov_terra_indigena_geom ON mesa_a.vetor_gov_terra_indigena USING GIST(geom);

-- Tema: Unidades Territoriais
-- Tabela para o Plano de Informação: Cavernas (ICMBio) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_cavernas (
    gid SERIAL PRIMARY KEY,
    nome_caverna VARCHAR(255),
    municipio VARCHAR(255),
    uf VARCHAR(100),
    litologia VARCHAR(255),
    grau_potencial VARCHAR(255),
    geom GEOMETRY(MultiPolygon, 4674)
);
CREATE INDEX idx_gov_cavernas_geom ON mesa_a.vetor_gov_cavernas USING GIST(geom);

-- Tema: Hidrografia, Fauna e Flora
-- Tabela para o Plano de Informação: Rios ANA (Base Hidrográfica Ottocodificada) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_rios_ana (
    gid SERIAL PRIMARY KEY,
    nome_rio VARCHAR(255),
    cocurso VARCHAR(50),
    corio VARCHAR(50),
    nucompam VARCHAR(50),
    nuareaam DOUBLE PRECISION,
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_gov_rios_ana_geom ON mesa_a.vetor_gov_rios_ana USING GIST(geom);

-- Tema: Infraestrutura
-- Tabela para o Plano de Informação: Aeroportos (Ministério da Infraestrutura) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_aeroportos (
    gid SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    municipio VARCHAR(255),
    uf VARCHAR(100),
    codigo_iata VARCHAR(10),
    codigo_icao VARCHAR(10),
    tipo VARCHAR(255),
    geom GEOMETRY(Point, 4674)
);
CREATE INDEX idx_gov_aeroportos_geom ON mesa_a.vetor_gov_aeroportos USING GIST(geom);

-- Tema: Infraestrutura
-- Tabela para o Plano de Informação: Aeródromos (ANA) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_aerodromos (
    gid SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    municipio VARCHAR(255),
    uf VARCHAR(100),
    situacao VARCHAR(255),
    geom GEOMETRY(MultiPoint, 4674)
);
CREATE INDEX idx_gov_aerodromos_geom ON mesa_a.vetor_gov_aerodromos USING GIST(geom);

-- Tema: Geração de Energia
-- Tabela para o Plano de Informação: Linhas de Transmissão (MMA/ANEEL) — DAG Airflow
CREATE TABLE mesa_a.vetor_gov_linhas_transmissao (
    gid SERIAL PRIMARY KEY,
    nome_linha VARCHAR(255),
    operador VARCHAR(255),
    tensao VARCHAR(100),
    situacao VARCHAR(255),
    geom GEOMETRY(MultiLineString, 4674)
);
CREATE INDEX idx_gov_linhas_transmissao_geom ON mesa_a.vetor_gov_linhas_transmissao USING GIST(geom);
