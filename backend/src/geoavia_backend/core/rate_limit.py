"""Shared rate limiter (slowapi) for abuse-sensitive endpoints.

Kept in its own module so routers can import the limiter without importing the
app assembly (avoids a circular import with main.py).
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by client IP. In-memory storage is fine for a single-process deployment;
# point it at Redis via `storage_uri` if the API is horizontally scaled.
limiter = Limiter(key_func=get_remote_address)
