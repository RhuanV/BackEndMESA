import os

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
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
from geoavia_backend.regions_router import router as regions_router
from geoavia_backend.screening_service import LayersNotReadyError, ScreeningService
from geoavia_backend.service import UserService
from geoavia_backend.shapefiles_service import ShapefileError, ShapefilesService

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
shapefiles_service = ShapefilesService()


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


LAYER_SOURCE_ROLES = {"coordenador", "administrador"}


@app.get("/layers/{layer_name}/source")
def get_layer_source(
    layer_name: str,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the upload configured as fallback data source for this layer."""
    try:
        return layers_service.get_source(layer_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/layers/{layer_name}/source")
def set_layer_source(
    layer_name: str,
    upload_id: int | None = None,
    current_user: dict = Depends(obtain_current_user),
):
    """Sets (or clears) the upload that feeds this layer when Airflow data is absent."""
    if current_user["role"] not in LAYER_SOURCE_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        layers_service.set_source(layer_name, upload_id)
        return {"ok": True, "layer_name": layer_name, "upload_id": upload_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


SCREENING_ROLES = {"coordenador", "gestor", "operador", "administrador", "desenvolvedor"}

class ScreeningRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    target_municipality_ibge_code: str = Field(min_length=7, max_length=7, pattern=r"^[0-9]{7}$")


@app.post("/screening")
def screen_site(
    payload: ScreeningRequest,
    current_user: dict = Depends(obtain_current_user),
):
    """Spatial screening (HU-29 + HU-26) — classifies a point as
    viavel / intermediario / restrito based on (a) containment in the target
    municipality, (b) intersection with restrictive infrastructure layers, and
    (c) proximity within layer-specific protective buffers (HU-26).
    Requires coordenador, gestor or operador.
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


SHAPEFILE_UPLOAD_ROLES = {
    "coordenador",
    "operador",
    "administrador",
}
_MAX_MB = int(os.getenv("SHAPEFILE_MAX_UPLOAD_MB", "500"))
SHAPEFILE_MAX_UPLOAD_BYTES = _MAX_MB * 1024 * 1024


@app.post("/shapefiles/upload")
async def upload_shapefile(
    file: UploadFile = File(...),
    layer_name: str = Form(..., min_length=1, max_length=150),
    description: str | None = Form(default=None, max_length=1000),
    current_user: dict = Depends(obtain_current_user),
):
    """Receives a zipped shapefile and ingests it into the mesa_a schema (HU-31).

    The ZIP must contain a single shapefile set (.shp + .dbf + .shx [+ .prj]).
    Geometries are reprojected to SIRGAS 2000 (EPSG:4674).
    """
    if current_user["role"] not in SHAPEFILE_UPLOAD_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip archive")

    zip_bytes = await file.read()
    if len(zip_bytes) > SHAPEFILE_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {SHAPEFILE_MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    try:
        return shapefiles_service.import_zip(
            layer_name=layer_name,
            description=description,
            original_filename=file.filename,
            zip_bytes=zip_bytes,
            user_id=int(current_user["sub"]) if current_user.get("sub") else None,
            username=current_user["username"],
            user_role=current_user["role"],
        )
    except ShapefileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shapefiles")
def list_shapefiles(
    limit: int = 100,
    current_user: dict = Depends(obtain_current_user),
):
    """Lists all uploaded shapefiles (audit view)."""
    if current_user["role"] not in SHAPEFILE_UPLOAD_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"uploads": shapefiles_service.list_layers(limit=limit)}


@app.get("/shapefiles/{upload_id}/features")
def get_shapefile_features(
    upload_id: int,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the upload's features as GeoJSON (for rendering on the map)."""
    if current_user["role"] not in SHAPEFILE_UPLOAD_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        return shapefiles_service.fetch_features(upload_id)
    except ShapefileError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


app.include_router(mesa_router)
app.include_router(regions_router)

# To run the server: uvicorn backend.main:app --reload