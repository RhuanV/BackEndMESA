# Roadmap de Adequação — MESA-A

**Documento de planejamento** · Versão 1.0 · 2026-07-14

Este documento descreve o plano completo para adequar a plataforma **Geoavia/MESA-A**
aos documentos de referência do projeto (Documento de Requisitos MESA-A, Planilha de
Controle de Metadados, Documento de Perfis de Usuário e Documento de Arquitetura/UML).
Ele consolida a avaliação do estado atual, as decisões arquiteturais tomadas e o
detalhamento das **5 fases** de trabalho (mais uma frente transversal de segurança).

> Forma de trabalho: cada mudança significativa entra por uma **branch + Pull Request**
> própria, com CI verde (lint, testes, build, migrações) antes do merge, seguindo
> Conventional Commits e o GitHub Flow já adotados no projeto. Prioriza-se **código
> limpo, auditável e seguro**.

---

## 1. Sumário executivo

### 1.1 O que já está implementado (real)
- **Autenticação e RBAC** (3 papéis: operador, administrador, desenvolvedor), com JWT
  (access em memória + refresh httpOnly), rate limiting e sandbox do papel desenvolvedor.
- **Auditoria** append-only (`audit_log`) e **logs de processamento** (`processing_log`).
- **Mapa interativo** MapLibre em SIRGAS 2000, painel de camadas, seletor de base map
  (OSM/Satélite Google Hybrid), tema claro/escuro.
- **RF02 — Seleção hierárquica** Brasil › Estado › Município (real).
- **RF04 — Variáveis vetoriais**: Triagem Espacial real (PostGIS `ST_Within`/`ST_Intersects`/
  `ST_DWithin`), classificando o ponto em viável/intermediário/restrito com buffers.
- **RNF01 (parcial)**: export **Shapefile** e **CSV** reais.
- **Ingestão (parcial)**: ~22 DAGs do Airflow cobrindo grande parte das camadas vetoriais
  da planilha (IBGE, SICAR imóveis, FUNAI, ICMBio, ANA, DNIT, ANEEL, OSM…).
- **Portal de upload** de shapefiles do usuário (reprojeção para EPSG:4674).

### 1.2 Principais lacunas frente aos documentos
| # | Lacuna | Requisito | Situação |
|---|--------|-----------|----------|
| 1 | Ingestão automática de metadados (planilha como fonte da verdade) | RF01 | Metadados *hardcoded* em 2 lugares + CSV de documentação |
| 2 | Processamento de variáveis matriciais (declividade/ANADEM, uso do solo/MapBiomas) | RF03 | Inexistente (sem GDAL/raster; camadas `available:false`) |
| 3 | MCDA real (pesos → adequabilidade a partir de dados espaciais) | RF05 | Mock determinístico; eliminatório e classificatório desconectados |
| 4 | Export GeoTIFF | RNF01 | Retorna 501 (depende do pipeline raster) |
| 5 | Conceito de Caso/Projeto (UML: Projeto → CandidateSites → SearchRegion → SiteLayout) | Arquitetura/UML | Inexistente (assessments isolados) |
| 6 | Perfis de usuário (5 sugeridos + customizados) e edição de role | Perfis | 3 papéis fixos; sem alterar role existente |
| 7 | ~45% das fontes da planilha sem DAG | RF01/BDG | INCRA, SICAR extras, MMA, CPRM, IBGE biomas/setores, GHSL, INPE… |
| 8 | TLS das DAGs gov (`verify=False`) e cofre de segredos | RNF03 | Risco de MITM; segredos só em `.env` |

### 1.3 Decisões arquiteturais (aprovadas)
1. **Papéis:** manter as **3 roles-base** e adicionar **perfis/grupos customizados** com
   permissões configuráveis (+ edição de role de usuário existente).
2. **Caso/Projeto:** **criar** a entidade de domínio que agrupa sítios candidatos, com
   município-alvo, coordenador e **ciclo de vida** (iniciado → em análise → campo → concluído).
3. **Ordem:** iniciar pela **Fase 1 (RF01 — catálogo de metadados)**.
4. **Raster (RF03):** processamento/armazenamento **local** (GDAL/rasterio + PostGIS raster).

---

## 2. Princípios e forma de trabalho
- **Branch + PR por mudança significativa** (`feat/*`, `fix/*`, `docs/*`); merge só com
  **CI 8/8 verde**. Ajustes de estilo de front pequenos podem ser agrupados numa branch
  de trabalho e entrar num PR único.
- **Segurança por padrão (RNF03):** SQL sempre parametrizado; gates por role/permissão no
  backend (`require_roles`) e defesa em profundidade no front; segredos fora do repositório;
  nada de credenciais/PII em logs.
- **Qualidade:** back valida com `ruff check` **e** `ruff format --check` + `pytest`; front
  com `npm run lint` + `tsc --noEmit` + `npm run test`; migrações Alembic idempotentes.
- **Rastreabilidade:** Conventional Commits, PRs descritivos, este roadmap como referência.

---

## 3. Visão geral do roadmap

| Fase | Tema | Requisitos atendidos | Branch(es) | Porte |
|------|------|----------------------|-----------|-------|
| 1 | Catálogo de metadados dirigido pela planilha | RF01, GUI (visualizador) | `feat/metadata-catalog` | Médio |
| 2 | Perfis/grupos customizados + edição de role | Perfis | `feat/custom-permission-profiles` | Médio |
| 3 | Domínio Caso/Projeto + ciclo de vida (UML) | Arquitetura, RF02+ | `feat/case-project` (+sub-PRs) | Grande |
| 4 | Completar fontes de dados (DAGs faltantes) | RF01/BDG | `feat/dag-<fonte>` (incrementais) | Baixo (por fonte) |
| 5 | Raster local + MCDA real + GeoTIFF | RF03, RF05, RNF01, RNF02 | `feat/raster-*` (+sub-PRs) | Grande |
| T | Segurança das DAGs (TLS) e segredos | RNF03 | `fix/dag-tls-verification` | Baixo |

**Dependências:** a Fase 5 (MCDA real) se beneficia da Fase 3 (Caso) e da Fase 4 (mais
camadas). A frente transversal de segurança (T) pode ser feita cedo e isolada. As Fases 1,
2 e 4 são majoritariamente independentes.

---

## 4. Fase 1 — RF01: Catálogo de metadados dirigido pela planilha
**Branch:** `feat/metadata-catalog` · **Objetivo:** tornar a **planilha de metadados** a
**fonte única da verdade** dos metadados de camada, eliminando a duplicação atual
(`services/layers.py` + `frontend/.../layerMetadata.ts` + CSV), e alimentar o Visualizador
de Metadados exigido na GUI.

### 4.1 Backend
- **Migração** cria `mesa_a.layer_catalog`, espelhando a planilha
  (`docs/database/modelagem/metadados_vetoriais.csv`):
  - Campos da planilha: `tema`, `plano_informacao`, `fonte`, `fonte_principal` (bool),
    `data_atualizacao_fonte`, `periodicidade`, `segregacao`, `datum`, `epsg`, `formato`,
    `geometria`, `observacoes`, `endereco`.
  - Campos operacionais: `layer_key` (único, ex.: `vetor_gov_rodovias_federais`),
    `backend_table`/`view`, `grupo` (base/analysis/exclusion), `data_type` (vector/raster),
    `available` (bool).
- **Ingestão idempotente (RF01):** serviço/rotina que **lê o CSV** e faz *upsert* em
  `layer_catalog` (chave `layer_key`/plano+fonte). Exposto como comando
  (`python -m geoavia_backend.scripts.load_catalog`) e como **DAG** `load_metadata_catalog`
  para automação. Parsing com `csv` stdlib; sem credenciais; tolerante a colunas multi-linha.
- **API** (autenticada): `GET /catalog/layers` (lista, com filtros por tema/grupo) e
  `GET /catalog/layers/{layer_key}` (detalhe). Repositório com SQL parametrizado.

### 4.2 Frontend
- `catalogApi.ts` + hook `useCatalog`; o **MetadataModal** passa a exibir os campos do
  catálogo (fonte, data da última atualização, EPSG, periodicidade, observações, endereço)
  vindos da API — não mais do registry estático. A **configuração visual** (paint/cores/
  ordem) permanece no front; apenas os **metadados** migram para o catálogo.
- (Opcional) página read-only **"Catálogo de Dados"** listando a planilha, com filtros por
  tema/fonte (útil para auditar procedência e recência das fontes).

### 4.3 Testes e verificação
- Unit puro do parser do CSV; smoke das rotas `/catalog/*`; back `ruff`+`pytest`; front
  `lint`+`tsc`+`test`; `alembic upgrade head` cria a tabela e a ingestão popula.
- Manual: abrir uma camada no mapa → o modal mostra metadados do catálogo; rodar a
  ingestão novamente não duplica linhas.

### 4.4 Casos de uso / valor
- "Automatizar download de metadados" (+4) e "Listar fontes de dados" (brainstorm).
- Visualizador de Metadados (GUI). Base para adicionar camadas sem editar código em 2 lugares.

### 4.5 Critérios de aceitação
- Catálogo populado a partir do CSV; API retorna metadados corretos; visualizador dinâmico;
  ingestão idempotente; CI verde.

---

## 5. Fase 2 — Perfis/grupos customizados + edição de role
**Branch:** `feat/custom-permission-profiles` · **Objetivo:** manter as 3 roles-base e
permitir **perfis customizados** com permissões configuráveis, além de **alterar a role/
perfil** de um usuário existente (hoje só criar/excluir).

### 5.1 Backend
- Tabela `permission_profiles` (nome, descrição, conjunto de permissões) + associação
  usuário → perfil (além da role-base). Permissões como catálogo estável
  (ex.: `map:view`, `analysis:run`, `admin:users`, `catalog:read`…).
- Checagem por **permissão** (não só role) nos endpoints sensíveis, resolvendo as permissões
  efetivas = base da role + perfil atribuído. Migração cria/seed dos perfis padrão espelhando
  as 3 roles atuais (retrocompatível).
- **Endpoint para alterar role/perfil** de usuário (`PATCH /users/{id}/role` /
  `.../profile`), gate admin, **auditado** (`USER_ROLE_CHANGE`). Regras: só desenvolvedor
  concede desenvolvedor; proteção do bootstrap.

### 5.2 Frontend
- Gestão de Usuários: editar role/perfil de um usuário; CRUD de perfis customizados (admin);
  a UI continua sendo defesa em profundidade (o backend é a fronteira real).

### 5.3 Aceitação
- Criar um perfil "Executor" com permissões próprias e atribuí-lo a um usuário; alteração de
  role auditada; permissões efetivas aplicadas back e front; CI verde.

---

## 6. Fase 3 — Domínio Caso/Projeto + ciclo de vida
**Branch:** `feat/case-project` (provavelmente vários sub-PRs) · **Objetivo:** modelar o
**Caso/Projeto** conforme o UML e a arquitetura, dando estrutura de ponta a ponta ao fluxo
MESA de 8 fases.

### 6.1 Modelo de domínio (UML)
- `projeto` (id, nome, descrição, coordenador_id, município/estado alvo, `status`:
  iniciado → em_análise → campo → concluído, timestamps).
- `search_region` (CRS, centróide, raio) e `candidate_site`/`site_layout` (dimensões,
  distâncias, `avoidance_violation`, status, observação) vinculados ao projeto — reaproveitando
  e estendendo os `assessments` atuais.
- `avoidance_area`/`exclusion_area` como classificação das camadas (tolerância/buffer).

### 6.2 Backend/Frontend
- CRUD de projetos (gate por papel: Gestor inicia caso e define Coordenador; Coordenador
  gerencia; Operador executa) — mapeado sobre roles-base + perfis (Fase 2).
- Telas de **lista/detalhe de caso**, transições de status e vínculo dos sítios candidatos ao
  caso; auditoria das transições.
- Integração com o fluxo MESA: eliminatório (Fase 3 de critérios) → candidatos → ranking →
  campo (download/ajuste/upload do caso) → consolidação.

### 6.3 Aceitação
- Criar um caso para um município, adicionar sítios candidatos, transitar o status e visualizar
  o caso; permissões coerentes com os perfis; CI verde.

---

## 7. Fase 4 — Completar fontes de dados (DAGs faltantes)
**Branches:** `feat/dag-<fonte>` incrementais (baixo risco, um por fonte/plano de informação),
alinhados à planilha. Cada DAG segue o padrão existente (extract → transform → load em
`mesa_a.vetor_*`, reprojeção para EPSG:4674, views de resolução quando aplicável) e é
registrado no **catálogo** (Fase 1).

| Fonte | Planos de informação faltantes |
|-------|--------------------------------|
| INCRA | Terras quilombolas, Assentamentos |
| SICAR | APP, Reserva Legal, Rios, Nascentes, Vegetação nativa, Lagos, Banhados, Área de pousio |
| MMA | Florestas públicas |
| CPRM | Geodiversidade |
| IBGE | Biomas, Setores censitários |
| GHSL/HDX | Densidade populacional (raster → ver Fase 5) |
| INPE | Dados anemométricos (raster → ver Fase 5) |

### 7.1 Aceitação
- DAG roda, popula a tabela, aparece no catálogo e no mapa; documentação da fonte no catálogo;
  CI verde.

---

## 8. Fase 5 — Raster local + MCDA real + GeoTIFF
**Branches:** `feat/raster-*` (sub-PRs) · **Objetivo:** implementar o núcleo analítico real,
substituindo o mock e atendendo RF03/RF05/RNF01/RNF02.

### 8.1 Pipeline raster (RF03) — local
- Ingestão/armazenamento de matriciais com **GDAL/rasterio + PostGIS raster** no servidor
  LESSONIA: **declividade** derivada do MDT **ANADEM** (30 m) e **uso do solo** **MapBiomas** (10 m).
- Recorte por área de estudo (município/região) e reprojeção/consistência SIRGAS 2000.

### 8.2 MCDA real (RF05)
- **Mapa de adequabilidade** conectando o **eliminatório** (máscara de exclusão da Triagem
  Espacial) com o **classificatório** (pesos por critério: declividade, uso do solo,
  distâncias/buffers, custo) — substitui o `_score` determinístico atual.
- Painel de pesos já existente passa a alimentar o cálculo real; resultados persistidos e
  ranqueados por caso (Fase 3).

### 8.3 Export GeoTIFF (RNF01) e desempenho (RNF02)
- Export do mapa de adequabilidade em **GeoTIFF** (hoje 501). Otimizações para manter o
  processamento de uma área municipal **≤ 30 s** (RNF02): pré-recorte, resolução adequada,
  cache/materialização quando possível.

### 8.4 Aceitação
- Para um município: gerar declividade e uso do solo, calcular adequabilidade respeitando
  exclusões, visualizar no mapa, exportar GeoTIFF; tempo dentro do alvo; CI verde.

---

## 9. Frente transversal — Segurança (RNF03)
**Branch:** `fix/dag-tls-verification` (cedo e isolado).
- Remover `verify=False` das DAGs gov (validação de certificado adequada: CA/*bundle* ou
  *pinning*), mitigando MITM; documentar exceções inevitáveis.
- Revisar tratamento de segredos (fora do repositório; `.gitignore`; sem credenciais em logs);
  padronizar acesso a APIs externas (ex.: MapBiomas) por variáveis seguras.

---

## 10. Matriz de rastreabilidade (requisito → fase)
| Requisito | Descrição | Fase |
|-----------|-----------|------|
| RF01 | Ingestão automática de metadados | 1 (+4 alimenta o catálogo) |
| RF02 | Seleção de área hierárquica | ✅ já atendido |
| RF03 | Variáveis matriciais (declividade, uso do solo) | 5 |
| RF04 | Variáveis vetoriais (buffers, exclusão) | ✅ já atendido (refino na 5) |
| RF05 | Motor de pesos (MCDA) | 5 |
| GUI | Painel de camadas / mapa / config análise | ✅ (visualizador dinâmico na 1) |
| RNF01 | Export Shapefile e GeoTIFF | ✅ SHP / GeoTIFF na 5 |
| RNF02 | Desempenho raster ≤ 30 s | 5 |
| RNF03 | Segurança (chaves/TLS) | T |
| Perfis | 5 perfis/customizados + edição de role | 2 (aplicados na 3) |
| UML/Arquitetura | Caso/Projeto, ciclo de vida | 3 |

---

## 11. Riscos e mitigações
- **Escopo grande (Fases 3 e 5):** quebrar em sub-PRs pequenos e revisáveis; validar por caso de uso.
- **Desempenho raster (RNF02):** recorte por área, resolução alvo, materialização/cache; medir.
- **Fontes gov instáveis / TLS:** tratar TLS corretamente (frente T); tolerância a falha nas DAGs
  e reprocessamento (Airflow).
- **Compatibilidade:** migrações idempotentes e mudanças retrocompatíveis (ex.: catálogo e perfis
  seedados espelhando o estado atual).
- **Segurança de dados do usuário:** manter gates por permissão e auditoria em toda ação sensível.

---

## 12. Controle de versão do documento
| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 2026-07-14 | Versão inicial do roadmap das 5 fases (+ frente transversal de segurança). |
