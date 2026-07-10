"""Centralized password-strength policy — the single source of truth on the backend.

Every place that sets a NEW password (user registration, admin password change,
recovery-code reset) validates through here. Login is intentionally NOT revalidated
against this policy so pre-existing accounts keep working.
"""
from __future__ import annotations

import re

MIN_PASSWORD_LENGTH = 8

_UPPERCASE = re.compile(r"[A-Z]")
_LOWERCASE = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def validate_password_strength(password: str) -> None:
    """Raises ValueError if `password` does not meet the strength policy.

    Requirements: at least MIN_PASSWORD_LENGTH characters, with at least one
    uppercase letter, one lowercase letter, one digit and one special character.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        )
    if not _UPPERCASE.search(password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not _LOWERCASE.search(password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not _DIGIT.search(password):
        raise ValueError("Password must contain at least one digit")
    if not _SPECIAL.search(password):
        raise ValueError("Password must contain at least one special character")
