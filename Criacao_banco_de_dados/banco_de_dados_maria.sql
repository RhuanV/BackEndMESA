-- Habilitar extensões do PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Criar esquema de catalogo
CREATE SCHEMA IF NOT EXISTS catalogo;

-- tabela de temas (unidades territoriais, hidrografia, etc)
CREATE TABLE catalogo.tema (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL UNIQUE,
    descricao TEXT
);
INSERT INTO catalogo.tema (nome, descricao)
VALUES
('Unidades Territoriais', 'Limites administrativos e fundiários'),
('Áreas Protegidas', 'Unidades de conservação e áreas protegidas'),
('Hidrografia Fauna Flora', 'Recursos hídricos e biodiversidade'),
('Infraestrutura', 'Infraestrutura logística e energética'),
('Meio Físico', 'Geologia, geodiversidade e biomas'),
('Energia', 'Infraestrutura energética'),
('Meteorologia', 'Dados climáticos e anemométricos');
-- tabela de fonte de dados (ibge, funai, etc)
CREATE TABLE catalogo.fonte_dados (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    sigla VARCHAR(50),
    url TEXT,
    licenca VARCHAR(200),
    esfera VARCHAR(50),
    observacoes TEXT
);
INSERT INTO catalogo.fonte_dados (
    nome,
    sigla,
    esfera
)
VALUES
('IBGE','IBGE','Federal'),
('SICAR','SICAR','Federal'),
('INCRA','INCRA','Federal'),
('FUNAI','FUNAI','Federal'),
('ICMBIO','ICMBIO','Federal'),
('ANA','ANA','Federal'),
('Ministério da Infraestrutura','MINFRA','Federal'),
('OpenStreetMap','OSM','Global');


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
INSERT INTO catalogo.plano_informacao(
    tema_id,
    fonte_id,
    nome,
    tabela_fisica,
    tipo_dado
)
VALUES (
    1,
    1,
    'Rodovias Federais',
    'mesa_a.vetor_rodovias_federais',
    'VETOR'
);

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

-- Relacionar temas com planos de informação
CREATE TABLE catalogo.plano_informacao (
    id SERIAL PRIMARY KEY,

    tema_id INTEGER NOT NULL
        REFERENCES catalogo.tema(id),

    fonte_id INTEGER
        REFERENCES catalogo.fonte_dados(id),

    nome VARCHAR(255) NOT NULL,

    descricao TEXT,

    tabela_fisica VARCHAR(255) NOT NULL,

    tipo_dado VARCHAR(20) NOT NULL
        CHECK(tipo_dado IN ('VETOR','RASTER')),

    ativo BOOLEAN DEFAULT TRUE,

    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(1,'Estado',
'mesa_a.vetor_estado',
'VETOR'),

(1,'Município',
'mesa_a.vetor_municipio',
'VETOR'),

(1,'Setor Censitário',
'mesa_a.vetor_setores_censitarios',
'VETOR'),

(1,'Área do Imóvel SICAR',
'mesa_a.vetor_area_do_imovel_sicar',
'VETOR'),

(1,'Área do Imóvel INCRA',
'mesa_a.vetor_area_do_imovel_incra',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(2,'Unidades de Conservação',
'mesa_a.vetor_uc_todas',
'VETOR'),

(2,'Área de Preservação Permanente',
'mesa_a.vetor_app',
'VETOR'),

(2,'Reserva Legal',
'mesa_a.vetor_reserva_legal',
'VETOR'),

(2,'Terra Indígena',
'mesa_a.vetor_terra_indigena',
'VETOR'),

(2,'Terra Quilombola',
'mesa_a.vetor_terra_quilombola',
'VETOR'),

(2,'Assentamentos',
'mesa_a.vetor_assentamentos',
'VETOR'),

(2,'Florestas Públicas',
'mesa_a.vetor_florestas_publicas',
'VETOR'),

(2,'Cavernas',
'mesa_a.vetor_cavernas',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(3,'Rios SICAR',
'mesa_a.vetor_rios_sicar',
'VETOR'),

(3,'Rios ANA',
'mesa_a.vetor_rios_ana',
'VETOR'),

(3,'Banhados',
'mesa_a.vetor_banhados',
'VETOR'),

(3,'Vegetação Nativa',
'mesa_a.vetor_vegetacao_nativa',
'VETOR'),

(3,'Área de Pousio',
'mesa_a.vetor_area_pousio',
'VETOR'),

(3,'Áreas de Atratividade de Aves',
'mesa_a.vetor_aves',
'VETOR'),

(3,'Lagos',
'mesa_a.vetor_lagos',
'VETOR'),

(3,'Nascentes',
'mesa_a.vetor_nascentes',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(4,'Aeroportos',
'mesa_a.vetor_aeroportos',
'VETOR'),

(4,'Aeroportos OSM',
'mesa_a.vetor_aeroportos_osm',
'VETOR'),

(4,'Aeródromos',
'mesa_a.vetor_aerodromos',
'VETOR'),

(4,'Rodovias Federais',
'mesa_a.vetor_rodovias_federais',
'VETOR'),

(4,'Rodovias OSM',
'mesa_a.vetor_rodovias_osm',
'VETOR'),

(4,'Ferrovias',
'mesa_a.vetor_ferrovias',
'VETOR'),

(4,'Ferrovias OSM',
'mesa_a.vetor_ferrovias_osm',
'VETOR'),

(4,'Hidrovias',
'mesa_a.vetor_hidrovias',
'VETOR'),

(4,'Hidrovias OSM',
'mesa_a.vetor_hidrovias_osm',
'VETOR'),

(4,'Dutos',
'mesa_a.vetor_dutos',
'VETOR'),

(4,'Portos',
'mesa_a.vetor_portos',
'VETOR'),

(4,'Portos OSM',
'mesa_a.vetor_portos_osm',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(5,'Geodiversidade',
'mesa_a.vetor_geodiversidade',
'VETOR'),

(5,'Biomas',
'mesa_a.vetor_biomas',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(6,'Linhas de Transmissão',
'mesa_a.vetor_linhas_transmissao',
'VETOR'),

(6,'Linhas de Transmissão OSM',
'mesa_a.vetor_linhas_transmissao_osm',
'VETOR');
INSERT INTO catalogo.plano_informacao
(tema_id,nome,tabela_fisica,tipo_dado)
VALUES

(7,'Dados Anemométricos',
'mesa_a.vetor_dados_anemometricos',
'VETOR');
-- Metadados especiais
CREATE TABLE catalogo.metadado_espacial (
    id SERIAL PRIMARY KEY,

    plano_id INTEGER NOT NULL
        REFERENCES catalogo.plano_informacao(id),

    epsg INTEGER,

    datum VARCHAR(100),

    formato_arquivo VARCHAR(50),

    geometria VARCHAR(50),

    resolucao_espacial VARCHAR(100),

    resolucao_temporal VARCHAR(100),

    periodicidade VARCHAR(100),

    data_ultima_atualizacao DATE,

    url_download TEXT,

    url_metadado TEXT
);
-- Criar esquema de análise
CREATE SCHEMA IF NOT EXISTS analise;

-- Tabela de critérios (distancia minima, dentro de plano, etc)
CREATE TABLE analise.criterio (
    id SERIAL PRIMARY KEY,

    nome VARCHAR(255) NOT NULL,

    descricao TEXT,

    operador VARCHAR(50) NOT NULL,

    valor_limite NUMERIC,

    unidade VARCHAR(50),

    peso NUMERIC(10,2) DEFAULT 1,

    obrigatorio BOOLEAN DEFAULT TRUE
);

-- Tabela associativa de criterio e plano
CREATE TABLE analise.criterio_plano (
    id SERIAL PRIMARY KEY,

    criterio_id INTEGER NOT NULL
        REFERENCES analise.criterio(id),

    plano_id INTEGER NOT NULL
        REFERENCES catalogo.plano_informacao(id),

    funcao_espacial VARCHAR(100) NOT NULL
);

-- Tabela de territórios em analise
CREATE TABLE analise.territorio_analise (
    id SERIAL PRIMARY KEY,

    nome VARCHAR(255),

    descricao TEXT,

    area_ha NUMERIC(18,4),

    geom GEOMETRY(MultiPolygon,4674)
);
CREATE INDEX idx_territorio_geom
ON analise.territorio_analise
USING GIST(geom);

-- Tabela de execução de análise
CREATE TABLE analise.execucao_analise (
    id SERIAL PRIMARY KEY,

    territorio_id INTEGER NOT NULL
        REFERENCES analise.territorio_analise(id),

    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    tipo_projeto VARCHAR(100),

    score NUMERIC(10,2),

    apto BOOLEAN,

    observacoes TEXT
);

-- Tabela de resultado por critério
CREATE TABLE analise.resultado_criterio (
    id SERIAL PRIMARY KEY,

    execucao_id INTEGER NOT NULL
        REFERENCES analise.execucao_analise(id),

    criterio_id INTEGER NOT NULL
        REFERENCES analise.criterio(id),

    aprovado BOOLEAN,

    valor_encontrado NUMERIC,

    observacao TEXT
);
-- Pra governança, tabela de versionamento dos planos
CREATE TABLE catalogo.versao_plano (
    id SERIAL PRIMARY KEY,

    plano_id INTEGER NOT NULL
        REFERENCES catalogo.plano_informacao(id),

    versao VARCHAR(50),

    data_inicio DATE,

    data_fim DATE,

    observacoes TEXT
);

-- tabela de controle de qualidade
CREATE TABLE catalogo.qualidade_dado (
    id SERIAL PRIMARY KEY,

    plano_id INTEGER NOT NULL
        REFERENCES catalogo.plano_informacao(id),

    completude NUMERIC(5,2),

    consistencia NUMERIC(5,2),

    precisao_posicional NUMERIC(10,2),

    observacoes TEXT
);
