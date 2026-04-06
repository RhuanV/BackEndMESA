from jose import JWTError, jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.database import ALGORITHM, SECRET_KEY
from backend.service import UserService

app = FastAPI(title="GeoAvia - Initial Test")
service = UserService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class UpdateUsernameRequest(BaseModel):
    username: str


async def obtain_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validates the JWT token and returns the basic data of the authenticated user."""
    unauthorized_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY not found in .env")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        if not sub or not username or not role:
            raise unauthorized_exception
    except JWTError as exc:
        raise unauthorized_exception from exc

    return {"sub": sub, "username": username, "role": role}


@app.get("/users")
def get_users(current_user: dict = Depends(obtain_current_user)):
    """Returns the list of users through the service and repository layers."""
    return service.list_users()


@app.post("/users/signup")
def create_user(
    username: str,
    password: str,
    role: str = "analyst",
):
    """Creates a user through the intermediate service layer."""
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

# To run the server: uvicorn backend.main:app --reload