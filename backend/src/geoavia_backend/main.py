from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from geoavia_backend.auth_dep import obtain_current_user
from geoavia_backend.mesa_router import router as mesa_router
from geoavia_backend.service import UserService

app = FastAPI(title="GeoAvia - Initial Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = UserService()


@app.get("/health")
def health():
    """Lightweight liveness probe for start.sh and the dev /health page."""
    return {"status": "ok"}


class UpdateUsernameRequest(BaseModel):
    username: str


@app.get("/users")
def get_users(current_user: dict = Depends(obtain_current_user)):
    """Returns the list of users through the service and repository layers."""
    return service.list_users()


USER_CREATION_ROLES = {"coordenador", "supervisor"}


@app.post("/users/signup")
def create_user(
    username: str,
    password: str,
    role: str = "operador",
    current_user: dict = Depends(obtain_current_user),
):
    """Creates a user through the intermediate service layer.

    Per Sprint 3 requirement: only coordenador and supervisor can create users.
    """
    if current_user["role"] not in USER_CREATION_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Apenas coordenador e supervisor podem criar usuários",
        )

    try:
        new_id = service.register_user(username, password, role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": new_id, "message": "User was successfully created"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates the user and returns a JWT access token."""
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

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


@app.put("/users/{user_id}/username")
def update_username(
    user_id: int,
    payload: UpdateUsernameRequest,
):
    """Updates a user's username based on their ID."""
    try:
        updated = service.change_username(user_id, payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Username was successfully changed"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Removes a user from the database based on their ID."""
    deleted = service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User was successfully deleted"}


app.include_router(mesa_router)

# To run the server: uvicorn backend.main:app --reload