"""Pydantic request models for permission profiles and role/profile changes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=255)
    # Permission strings are validated against the catalog in the service layer.
    permissions: list[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    permissions: list[str] = Field(default_factory=list)


class RoleChangeRequest(BaseModel):
    role: str = Field(min_length=1, max_length=20)


class ProfileAssignRequest(BaseModel):
    # None clears the profile (user falls back to base-role permissions).
    profile_id: int | None = None
