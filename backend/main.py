from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.service import UsuarioService

app = FastAPI(title="GeoAvia - Teste Inicial")
service = UsuarioService()


class UpdateUsernameRequest(BaseModel):
    username: str


@app.get("/usuarios")
def get_usuarios():
    """Retorna a lista de usuários passando pelas camadas de serviço e repositório."""
    return service.listar_usuarios()


@app.post("/usuarios/signup")
def create_usuario(
    username: str,
    password: str,
    role: str = "analista",
):
    """Cria um usuário através da camada intermediária."""
    try:
        new_id = service.cadastrar_usuario(username, password, role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": new_id, "message": "Usuário criado com sucesso"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Autentica o usuário e retorna um token JWT de acesso."""
    user = service.autenticar_usuario(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario ou senha invalidos")

    try:
        access_token = service.security.create_access_token(
            {
                "sub": str(user["id"]),
                "username": user["username"],
                "role": user["role"],
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"access_token": access_token, "token_type": "bearer"}


@app.put("/usuarios/{user_id}/username")
def update_usuario_username(
    user_id: int,
    payload: UpdateUsernameRequest,
):
    """Atualiza o username de um usuário a partir do ID."""
    try:
        updated = service.alterar_nome_usuario(user_id, payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"message": "Nome de usuário atualizado com sucesso"}


@app.delete("/usuarios/{user_id}")
def delete_usuario(user_id: int):
    """Remove um usuário do banco de dados a partir do ID."""
    deleted = service.excluir_usuario(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"message": "Usuário deletado com sucesso"}

# Para rodar: uvicorn backend.main:app --reload