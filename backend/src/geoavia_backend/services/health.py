"""Dependency health checks for the detailed health endpoint.

Each check returns a small dict {name, status, latency_ms?, detail}. The database
is the only *critical* dependency: if it fails the aggregate status is `error`.
Airflow and system metrics are non-critical → a failure degrades to `degraded`.

Security: error details are truncated and generic — never expose the DSN,
credentials or internal stack traces to the client.
"""

from __future__ import annotations

import shutil
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime

from geoavia_backend.core.db import cursor
from geoavia_backend.services.airflow import AIRFLOW_BASE_URL

_OK = "ok"
_ERROR = "error"
_UNKNOWN = "unknown"
_TIMEOUT_SECONDS = 5
_MAX_DETAIL = 200


def _truncate(text: str) -> str:
    return text[:_MAX_DETAIL]


def check_database() -> dict:
    """Verifies PostgreSQL/PostGIS connectivity and reports the PostGIS version."""
    start = time.perf_counter()
    try:
        with cursor() as cur:
            cur.execute("SELECT postgis_version();")
            version = cur.fetchone()[0]
        latency_ms = round((time.perf_counter() - start) * 1000)
        return {
            "name": "PostgreSQL/PostGIS",
            "status": _OK,
            "latency_ms": latency_ms,
            "detail": f"PostGIS {version}",
        }
    except Exception as exc:  # noqa: BLE001 — surface a generic, safe message
        return {
            "name": "PostgreSQL/PostGIS",
            "status": _ERROR,
            "latency_ms": round((time.perf_counter() - start) * 1000),
            "detail": _truncate(f"Database unreachable: {type(exc).__name__}"),
        }


def check_airflow() -> dict:
    """Pings Airflow's public /health endpoint (non-critical dependency)."""
    start = time.perf_counter()
    try:
        req = urllib.request.Request(f"{AIRFLOW_BASE_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            ok = resp.status == 200
        latency_ms = round((time.perf_counter() - start) * 1000)
        return {
            "name": "Airflow",
            "status": _OK if ok else _ERROR,
            "latency_ms": latency_ms,
            "detail": "healthy" if ok else f"HTTP {resp.status}",
        }
    except (urllib.error.URLError, OSError) as exc:
        return {
            "name": "Airflow",
            "status": _ERROR,
            "latency_ms": round((time.perf_counter() - start) * 1000),
            "detail": _truncate(f"Airflow unreachable: {type(exc).__name__}"),
        }


def check_disk() -> dict:
    """Reports root filesystem usage via shutil (cross-platform, stdlib)."""
    try:
        usage = shutil.disk_usage("/")
        pct = round(usage.used / usage.total * 100)
        gb = 1024**3
        status = _OK if pct < 90 else _ERROR
        return {
            "name": "Disco",
            "status": status,
            "detail": f"{pct}% usado ({usage.used // gb}/{usage.total // gb} GB)",
        }
    except OSError:
        return {"name": "Disco", "status": _UNKNOWN, "detail": "indisponível"}


def check_memory() -> dict:
    """Reports memory usage from /proc/meminfo (Linux/Docker); unknown elsewhere."""
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                key, _, rest = line.partition(":")
                info[key] = int(rest.strip().split()[0])  # value in kB
        total = info.get("MemTotal")
        available = info.get("MemAvailable")
        if not total or available is None:
            return {"name": "Memória", "status": _UNKNOWN, "detail": "indisponível"}
        pct = round((total - available) / total * 100)
        status = _OK if pct < 90 else _ERROR
        return {"name": "Memória", "status": status, "detail": f"{pct}% usada"}
    except (OSError, ValueError):
        return {"name": "Memória", "status": _UNKNOWN, "detail": "indisponível"}


# The database is the only check that makes the whole system unhealthy.
_CRITICAL = {"PostgreSQL/PostGIS"}


def aggregate_status(checks: list[dict]) -> str:
    """error if a critical check failed, degraded if a non-critical one failed."""
    for check in checks:
        if check["status"] == _ERROR and check["name"] in _CRITICAL:
            return _ERROR
    if any(check["status"] != _OK for check in checks):
        return "degraded"
    return _OK


def collect() -> dict:
    """Runs every dependency check and returns the aggregated report."""
    checks = [check_database(), check_airflow(), check_disk(), check_memory()]
    return {
        "status": aggregate_status(checks),
        "checked_at": datetime.now(UTC).isoformat(),
        "checks": checks,
    }
