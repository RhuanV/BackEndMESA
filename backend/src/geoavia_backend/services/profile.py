"""Business logic for custom permission profiles."""

from __future__ import annotations

from geoavia_backend.core.permissions import validate_permissions
from geoavia_backend.repositories.profile import ProfileRepository


class ProfileService:
    def __init__(self, repo: ProfileRepository | None = None) -> None:
        self.repo = repo or ProfileRepository()

    def list_profiles(self) -> list[dict]:
        return self.repo.list()

    def get_profile(self, profile_id: int) -> dict | None:
        return self.repo.get_by_id(profile_id)

    def create_profile(self, name: str, description: str | None, permissions: list[str]) -> int:
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValueError("Profile name must not be empty")
        if self.repo.name_exists(clean_name):
            raise ValueError("A profile with this name already exists")
        perms = validate_permissions(permissions)
        return self.repo.create(clean_name, (description or "").strip() or None, perms)

    def update_profile(
        self, profile_id: int, description: str | None, permissions: list[str]
    ) -> bool:
        profile = self.repo.get_by_id(profile_id)
        if not profile:
            return False
        if profile["is_system"]:
            raise ValueError("System profiles cannot be modified")
        perms = validate_permissions(permissions)
        return self.repo.update(profile_id, (description or "").strip() or None, perms)

    def delete_profile(self, profile_id: int) -> bool:
        profile = self.repo.get_by_id(profile_id)
        if not profile:
            return False
        if profile["is_system"]:
            raise ValueError("System profiles cannot be deleted")
        return self.repo.delete(profile_id)
