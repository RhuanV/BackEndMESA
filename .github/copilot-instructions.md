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
- sempre escreva o código em inglês, mas os comentários e docstrings devem ser em português para facilitar a compreensão da equipe local.
- ao criar um novo arquivo, adicione um comentário no topo explicando o propósito do arquivo e como ele se encaixa na arquitetura geral.

## 🔒 Segurança e Autenticação (Login & RBAC)

Ao implementar funcionalidades de usuários, login ou proteção de rotas, siga estas diretrizes obrigatórias:

### 1. Tratamento de Credenciais
- **Proibição de Texto Puro:** Nunca armazene ou compare senhas em texto puro.
- **Hashing:** Utilize obrigatoriamente a biblioteca `passlib` com o algoritmo **bcrypt**
- **Salting:** Garanta que o salt seja gerado automaticamente pela biblioteca de hashing.
- **Camada Repository:** O repositório deve apenas buscar o hash do banco pelo `username`. A comparação lógica deve ocorrer na camada de **Service**.

### 2. Fluxo de Autenticação (JWT)
- **Tokens:** Utilize **JSON Web Tokens (JWT)** para persistência de sessão.
- **Payload:** O token deve conter `sub` (ID do usuário), `username`, `exp` (expiração) e, obrigatoriamente, o campo `role` (perfil).
- **Segurança do Token:** A `SECRET_KEY` para assinatura do JWT deve ser lida estritamente do arquivo `.env` através do `database.py`.

### 3. Autorização e Perfis (RBAC)
O sistema deve suportar três níveis de acesso (Controle de Acesso Baseado em Funções):
- **Analista:** Acesso a consultas de sítios, entrada de dados MESA e visualização de mapas.
- **Administrador:** Gestão de usuários, alteração de pesos de critérios e aprovação de relatórios.
- **Desenvolvedor:** Acesso a logs de sistema, métricas de performance e endpoints de manutenção.

### 4. Implementação no FastAPI
- Utilize `OAuth2PasswordBearer` do FastAPI para extração de tokens.
- Crie **Dependencies** (funções injetáveis) para verificar se o perfil (role) contido no token tem permissão para acessar a rota específica.
- Retorne `401 Unauthorized` para falhas de login e `403 Forbidden` para usuários autenticados tentando acessar rotas acima de seu nível de permissão.

### 5. Camadas de Código
- **backend/repository.py:** Métodos para `get_user_by_username` e `create_user`.
- **backend/service.py:** Lógica de `verify_password`, `get_password_hash`, `authenticate_user` e `create_access_token`.
- **backend/main.py:** Endpoints `/login`, `/signup` e aplicação das dependências de segurança nas rotas protegidas.