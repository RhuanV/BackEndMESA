## raschunho!
Esse documento é um rascunho para descrever o início da construção do banco de dados.
A princípio, o BD é formado com uma tabela para cada plano de informação. Os relacionamentos ainda não foram discutidos
A implmenetação de regras da metodologia ainda não foram implementadas e o estudo das regras pode ajudar na criação dos relacionamentos

## Criar tabelas de zoom:
Siga esse modelo com as tabelas já existentes para criar outras três tabelas de zoom
A criação deve ocorrer na criação do banco de dados


## Modelo para tabela de linhas e polígonos
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z1;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z2;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z3;

CREATE MATERIALIZED VIEW state_boundaries_z1 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE MATERIALIZED VIEW state_boundaries_z2 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE MATERIALIZED VIEW state_boundaries_z3 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE INDEX idx_state_boundaries_z1_geom ON state_boundaries_z1 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z2_geom ON state_boundaries_z2 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z3_geom ON state_boundaries_z3 USING GIST (geom);


## Modelo para tabela de pontos
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z1;
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z2;
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z3;

CREATE MATERIALIZED VIEW aeroportos_z1 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE MATERIALIZED VIEW aeroportos_z2 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE MATERIALIZED VIEW aeroportos_z3 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE INDEX idx_aeroportos_z1_geom ON aeroportos_z1 USING GIST (geom);
CREATE INDEX idx_aeroportos_z2_geom ON aeroportos_z2 USING GIST (geom);
CREATE INDEX idx_aeroportos_z3_geom ON aeroportos_z3 USING GIST (geom);

Use esse doc como prompt para gerar as outras tabelas uma vez que o .sql de criação do banco de dados for aprovado.

## Realacionamento entre as tabelas
Não foram decididos os relacionamentos. Um relacionamento óbvio é Estado - Município, mas a tabela de município já é carregada com a unidade da federação...
Deve-se pensar em relacionamentos que ajudem na visualização dos dados, economizando cálculos do servidor.

## Implementação no backend
É necessário criar as requisições do backend para entregar os dados ao front. A ideia inicialmente é visualizar. Vamos começar com os dados vetoriais apenas e expandir depois.
Uma requisição de visualiação deve vir com um ponto central (local onde o usuário vê) e um zoom (z1, z2, z3, dependendo do grau de detalhe). a requisição deve entregar os planos de informação no retângulo pedido com a resolução selecionada. O cálculo do zoom deve ser feito pelo front

Deve-se discutir se a implementação do backend envia todos os planos de informação ou apenas os requisitados (dentro da área, claro). testar é a melhor forma de avaliar a melhor solução. é necessário verificar como enviar os dados (jason??) para o front, deve ter uma bibioteca pronta que faz isso

