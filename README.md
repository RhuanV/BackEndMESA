# BackEndMESA

## estrutura de pastas
geoavia-server/
├── backend/
│   ├── main.py          # Camada 3: FastAPI (Interface)
│   ├── service.py       # Camada 2: Regras de Negócio (Intermediário)
│   ├── repository.py    # Camada 1: pyLib SQL (Acesso ao BD)
│   └── database.py      # Configuração da conexão
└── .env                 # Variáveis de ambiente (DB_URL)

## 🚀 Setup Rápido

### 1. Ambiente e Dependências
```bash
# Criar venv
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate
# Ativar (Linux/Mac)
source .venv/bin/activate

# Instalar
pip install -r requirements.txt