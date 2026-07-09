"""Pydantic request models for the users endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateUsernameRequest(BaseModel):
    username: str


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=6)


class RecoveryPasswordResetRequest(BaseModel):
    """Public request to reset a password using an admin-issued recovery code."""

    username: str
    code: str
    new_password: str = Field(min_length=8)
