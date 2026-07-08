from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from geoavia_backend.airflow_trigger_service import (
    AirflowTriggerError,
    AirflowTriggerService,
    UnknownDagError,
)
from geoavia_backend.auth_dep import obtain_current_user
from geoavia_backend.database import FRONTEND_PORT
from geoavia_backend.layers_service import LayersService
from geoavia_backend.mesa_router import router as mesa_router
from geoavia_backend.screening_service import LayersNotReadyError, ScreeningService
from geoavia_backend.service import UserService

app = FastAPI(title="GeoAvia - Initial Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{FRONTEND_PORT}",
        f"http://127.0.0.1:{FRONTEND_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = UserService()
layers_service = LayersService()
screening_service = ScreeningService()
airflow_trigger_service = AirflowTriggerService()


@app.get("/health")
def health():
    """Lightweight liveness probe for start.sh and the dev /health page."""
    return {"status": "ok"}


class UpdateUsernameRequest(BaseModel):
    username: str


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=6)


@app.get("/users")
def get_users(current_user: dict = Depends(obtain_current_user)):
    """Returns the list of users through the service and repository layers."""
    return service.list_users()


USER_CREATION_ROLES = {"coordenador", "supervisor", "desenvolvedor"}


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
    current_user: dict = Depends(obtain_current_user),
):
    """Updates a user's username based on their ID."""
    if current_user["role"] not in USER_CREATION_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Apenas coordenador e supervisor podem alterar o nome de usuários",
        )

    try:
        updated = service.change_username(user_id, payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Username was successfully changed"}


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(obtain_current_user),
):
    """Removes a user from the database based on their ID."""
    if current_user["role"] not in USER_CREATION_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Apenas coordenador e supervisor podem excluir usuários",
        )

    deleted = service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User was successfully deleted"}


@app.put("/users/{user_id}/password")
def change_password(
    user_id: int,
    payload: PasswordResetRequest,
    current_user: dict = Depends(obtain_current_user),
):
    """Resets the password for a user. Available only to DEV_USER."""
    from geoavia_backend.database import DEV_USER
    if current_user["username"] != DEV_USER:
        raise HTTPException(
            status_code=403,
            detail="Apenas o desenvolvedor principal pode redefinir senhas através desta rota.",
        )

    try:
        updated = service.change_password(user_id, payload.new_password)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Password was successfully changed"}


@app.get("/layers/{layer_name}")
def get_layer(
    layer_name: str,
    zoom: str | None = None,
    bbox: str | None = None,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the requested layer as GeoJSON, simplified per zoom level.

    See LAYER_REGISTRY in layers_service for the allowed layer names.
    """
    try:
        return layers_service.fetch(layer_name, zoom, bbox)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


SCREENING_ROLES = {"coordenador", "gestor", "operador", "desenvolvedor"}


class ScreeningRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    target_municipality_ibge_code: str = Field(min_length=7, max_length=7, pattern=r"^[0-9]{7}$")


@app.post("/screening")
def screen_site(
    payload: ScreeningRequest,
    current_user: dict = Depends(obtain_current_user),
):
    """Spatial screening (Sprint 4 HU-29) — classifies a point as viavel/restrito
    based on containment in the target municipality and intersection with
    restrictive infrastructure layers. Requires coordenador, gestor or operador.
    """
    if current_user["role"] not in SCREENING_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Apenas coordenador, gestor e operador podem rodar a triagem",
        )

    try:
        return screening_service.screen(
            payload.latitude,
            payload.longitude,
            payload.target_municipality_ibge_code,
        )
    except LayersNotReadyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"message": str(exc), "missing_layers": exc.missing_layers},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


DAG_TRIGGER_ROLES = {
    "coordenador",
    "gestor",
    "supervisor",
    "operador",
    "administrador",
    "desenvolvedor",
}


@app.post("/airflow/trigger/{dag_id}")
def trigger_airflow_dag(
    dag_id: str,
    current_user: dict = Depends(obtain_current_user),
):
    """Triggers a whitelisted Airflow DAG and audits who did it (HU-23).

    Available DAGs: see ALLOWED_DAGS in airflow_trigger_service.
    """
    if current_user["role"] not in DAG_TRIGGER_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Permission denied for DAG trigger",
        )

    try:
        return airflow_trigger_service.trigger(
            dag_id=dag_id,
            user_id=int(current_user["sub"]) if current_user.get("sub") else None,
            username=current_user["username"],
            user_role=current_user["role"],
        )
    except UnknownDagError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AirflowTriggerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/airflow/triggers")
def list_airflow_triggers(
    limit: int = 100,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the most recent manual DAG triggers (audit log). Same role gate
    as the trigger endpoint — any authenticated operator-or-above can audit.
    """
    if current_user["role"] not in DAG_TRIGGER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {
        "allowed_dags": airflow_trigger_service.list_allowed_dags(),
        "recent": airflow_trigger_service.list_recent_logs(limit=limit),
    }


app.include_router(mesa_router)

# To run the server: uvicorn backend.main:app --reload