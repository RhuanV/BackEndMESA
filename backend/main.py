from fastapi import FastAPI
from backend.service import UsuarioService

app = FastAPI(title="GeoAvia - Teste Inicial")
service = UsuarioService()

@app.get("/usuarios")
def get_usuarios():
    """Retorna a lista de usuários passando pelas camadas de serviço e repositório."""
    return service.listar_usuarios()

@app.post("/usuarios/signup")
def create_usuario(username: str, password: str):
    """Cria um usuário através da camada intermediária."""
    new_id = service.cadastrar_usuario(username, password)
    return {"id": new_id, "message": "Usuário criado com sucesso"}

# Para rodar: uvicorn backend.main:app --reload