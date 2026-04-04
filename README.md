# GeoAvia - Backend MESA-Auto

Backend do projeto GeoAvia (parceria SAC/ANAC/ITA) para automação da metodologia MESA na prospecção de sítios aeroportuários.

## Visão geral

Stack atual:

- Python 3.12
- FastAPI
- PostgreSQL (com evolucao prevista para PostGIS)
- Docker e Docker Compose
- SQL puro com psycopg2 (sem ORM)

Estado atual da API:

- Cadastro de usuário com hash de senha
- Login com JWT
- Proteção de rota com Bearer token em GET /usuarios
- Gestão de usuários por ID (update username e delete)

## Arquitetura

Arquitetura em camadas:

- Camada API: backend/main.py
- Camada Service: backend/service.py
- Camada Repository: backend/repository.py
- Configuração de ambiente: backend/database.py

Princípios:

- Regras de negócio no service
- Acesso a dados no repository com SQL explícito
- Variáveis sensíveis via .env

## Estrutura do repositório

```text
BackEndMESA/
|-- backend/
|   |-- main.py
|   |-- service.py
|   |-- repository.py
|   `-- database.py
|-- init-db/
|   |-- 01_create_tables.sql
|   `-- 02_insert_data.sql
|-- .github/
|   `-- copilot-instructions.md
|-- .pre-commit-config.yaml
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Configuração

Crie um arquivo .env na raiz com:

```env
DB_HOST=db
DB_NAME=usuarios_MESA
DB_USER=postgres
DB_PASS=123
DB_PORT=5432
SECRET_KEY=troque_para_uma_chave_forte
ALGORITHM=HS256
```

Observações:

- Em execução local fora do Docker, use DB_HOST=localhost.
- SECRET_KEY deve ser única por ambiente e não deve ser versionada.

## Como executar

### Opção A: Docker (recomendado)

```bash
docker-compose up --build
```

Serviços esperados:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Banco: porta 5433 no host (mapeada para 5432 no container)
- Caso já tenho postgres rodando, talvez seja necessário fazer a conexão com a porta 5433 no dbeaver (ou outro SGBD) para visualizar o banco de dados nos testes.

### Opção B: Local

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instalar dependências e iniciar:

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

## Endpoints atuais

Autenticação:

- POST /usuarios/signup
- POST /login

Usuários:

- GET /usuarios (protegida por token)
- PUT /usuarios/{user_id}/username
- DELETE /usuarios/{user_id}

## Fluxo de autenticação

1. Criar usuário em POST /usuarios/signup
2. Autenticar em POST /login
3. Receber access_token
4. Enviar Authorization: Bearer <token> para GET /usuarios

## Organização para trabalho em conjunto

Sugestões práticas para evoluir o repositório em equipe:

1. Separar módulo de segurança
- Criar backend/security.py para centralizar hashing, emissão e validação de token.
- Manter backend/service.py focado em regra de negócio.

2. Padronizar modelos de request/response
- Criar backend/schemas.py com classes Pydantic para signup, login e respostas.
- Reduzir parâmetros soltos nas rotas.

3. Separar dependências de runtime e desenvolvimento
- Manter runtime em requirements.txt.
- Criar requirements-dev.txt para ferramentas como pre-commit e commitizen.

4. Adicionar testes automatizados
- tests/unit para service.
- tests/integration para rotas e autenticação.

5. Definir convenções de colaboração
- Padrão de branch: feat/, fix/, chore/.
- PR com checklist mínimo (teste local, impacto em API, migração de banco).
- Commits semânticos com commitizen (já suportado por .pre-commit-config.yaml).

6. Versionar decisões arquiteturais
- Criar pasta docs/adr para registrar decisões de segurança, banco e API.

## Segurança

- Senhas nunca devem ser armazenadas em texto puro.
- Não commitar .env com credenciais reais.
- Em produção, rotacionar SECRET_KEY e usar variáveis secretas do ambiente.

## Referências internas

- Diretrizes de implementação: .github/copilot-instructions.md
- Entrada principal da API: backend/main.py