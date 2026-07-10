"""Service that triggers Airflow DAGs and records the audit log.

Uses the stable Airflow REST API (`POST /api/v1/dags/{dag_id}/dagRuns`) with
HTTP basic auth read from the environment (AIRFLOW_USER/AIRFLOW_PASS). Uses
stdlib `urllib.request` to avoid adding `requests` to backend/requirements.txt.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

from geoavia_backend.repositories.airflow import AirflowTriggerRepository

# Whitelisted DAGs that are allowed to be triggered manually via this endpoint.
# Internal/automated DAGs (refresh_*_resolution_views) are not listed because
# they fire via Dataset triggers, not manual operator action.
ALLOWED_DAGS: frozenset[str] = frozenset(
    {
        "load_state_boundaries",
        "load_municipality_boundaries",
        "download_geofabrik_data",
        "update_osm_diffs",
        "load_osm_airports",
        "load_osm_federal_highways",
        "load_osm_state_highways",
        "load_osm_railways",
        "load_osm_waterways",
        "load_osm_power_lines",
        "load_gov_federal_highways",
        "load_gov_railways",
        "load_gov_waterways",
        "load_gov_ports",
    }
)

# Airflow service URL (inside docker network). Override via env if needed.
AIRFLOW_BASE_URL = os.environ.get("AIRFLOW_BASE_URL", "http://airflow:8080")
# Credentials for the Airflow REST API. No insecure hardcoded default: fall back
# to the same vars that provision the Airflow web user (AIRFLOW_USER/PASS), and
# require them to be set (checked at call time) instead of shipping admin/admin.
AIRFLOW_USERNAME = os.environ.get("AIRFLOW_USERNAME") or os.environ.get("AIRFLOW_USER")
AIRFLOW_PASSWORD = os.environ.get("AIRFLOW_PASSWORD") or os.environ.get("AIRFLOW_PASS")
TRIGGER_TIMEOUT_SECONDS = 10


class UnknownDagError(Exception):
    pass


class AirflowTriggerError(Exception):
    """Raised when the Airflow REST API call itself fails."""


class AirflowTriggerService:
    def __init__(self) -> None:
        self.repo = AirflowTriggerRepository()

    def list_allowed_dags(self) -> list[str]:
        return sorted(ALLOWED_DAGS)

    def trigger(
        self,
        dag_id: str,
        user_id: int | None,
        username: str,
        user_role: str,
    ) -> dict:
        if dag_id not in ALLOWED_DAGS:
            raise UnknownDagError(f"DAG not allowed via this endpoint: {dag_id}")

        try:
            dag_run_id = self._call_airflow(dag_id)
        except AirflowTriggerError as exc:
            self.repo.insert_log(
                user_id=user_id,
                username=username,
                user_role=user_role,
                dag_id=dag_id,
                dag_run_id=None,
                status="failed_to_trigger",
                error_message=str(exc),
            )
            raise

        log_id = self.repo.insert_log(
            user_id=user_id,
            username=username,
            user_role=user_role,
            dag_id=dag_id,
            dag_run_id=dag_run_id,
            status="triggered",
        )

        return {
            "log_id": log_id,
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
            "triggered_by": username,
            "user_role": user_role,
        }

    def list_recent_logs(self, limit: int = 100) -> list[dict]:
        return self.repo.list_recent(limit=limit)

    @staticmethod
    def _call_airflow(dag_id: str) -> str:
        """POSTs to /api/v1/dags/{dag_id}/dagRuns and returns the dag_run_id."""
        if not AIRFLOW_USERNAME or not AIRFLOW_PASSWORD:
            raise AirflowTriggerError(
                "Airflow credentials are not configured. Set AIRFLOW_USER/AIRFLOW_PASS "
                "(or AIRFLOW_USERNAME/AIRFLOW_PASSWORD) in the environment."
            )
        url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{dag_id}/dagRuns"
        body = json.dumps({"conf": {}}).encode("utf-8")
        auth = base64.b64encode(
            f"{AIRFLOW_USERNAME}:{AIRFLOW_PASSWORD}".encode("utf-8")
        ).decode("ascii")

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Basic {auth}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TRIGGER_TIMEOUT_SECONDS) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AirflowTriggerError(
                f"Airflow returned HTTP {exc.code}: {detail[:300]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise AirflowTriggerError(f"Failed to reach Airflow: {exc}") from exc

        dag_run_id = payload.get("dag_run_id")
        if not dag_run_id:
            raise AirflowTriggerError(
                f"Airflow response missing dag_run_id: {payload}"
            )
        return dag_run_id
