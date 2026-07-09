"""Pydantic request models for the users endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateUsernameRequest(BaseModel):
    username: str


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=6)
