"""Secure HTTP helpers for the Airflow data-ingestion DAGs.

Several government geoservers ship incomplete TLS certificate chains (missing
intermediate CAs) or require legacy ciphers. The historical workaround in this
project was to sprinkle ``verify=False`` across the DAGs, which silently
disables certificate validation and exposes every download to man-in-the-middle
tampering of the ingested geodata (RNF03).

This module keeps certificate verification **on by default** and gives
operators an explicit, auditable way to deal with genuinely broken sources:

* Set ``GEOAVIA_CA_BUNDLE`` to a PEM bundle path (e.g. one that adds a missing
  government intermediate CA). This is the preferred fix — verification stays
  enabled against the extended trust store.
* As a last resort, list hostnames in ``GEOAVIA_TLS_INSECURE_HOSTS``
  (comma-separated). Verification is skipped **only** for those hosts, and every
  such request logs a loud security warning documenting the exception.

Both switches live in ops configuration, not in the DAG code, so the default
posture is secure and any exception is explicit and reviewable.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit

import requests

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"
DEFAULT_TIMEOUT = 180


def _insecure_hosts() -> set[str]:
    raw = os.environ.get("GEOAVIA_TLS_INSECURE_HOSTS", "")
    return {host.strip().lower() for host in raw.split(",") if host.strip()}


def resolve_verify(url: str) -> str | bool:
    """Returns the value to pass to ``requests``' ``verify`` for ``url``.

    Order of precedence: an explicit per-host insecure exception (returns
    ``False`` and warns), then a custom CA bundle path, then the default trust
    store (``True``). Verification is therefore enabled unless an operator has
    opted a specific host out on purpose.
    """
    host = (urlsplit(url).hostname or "").lower()
    if host in _insecure_hosts():
        logger.warning(
            "TLS verification DISABLED for host %s via GEOAVIA_TLS_INSECURE_HOSTS. "
            "This is an explicit, documented exception and exposes this download to "
            "man-in-the-middle tampering. Prefer supplying GEOAVIA_CA_BUNDLE instead.",
            host,
        )
        return False
    bundle = os.environ.get("GEOAVIA_CA_BUNDLE")
    if bundle:
        return bundle
    return True


def government_get(url: str, **kwargs) -> requests.Response:
    """``requests.get`` with secure-by-default TLS verification for gov sources.

    Applies a default User-Agent and timeout and resolves ``verify`` via
    :func:`resolve_verify`. Any caller-supplied ``verify`` is ignored so that
    verification cannot be silently disabled from DAG code — use the
    ``GEOAVIA_TLS_INSECURE_HOSTS`` allowlist for documented exceptions.
    """
    kwargs.pop("verify", None)
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    headers.update(kwargs.pop("headers", None) or {})
    return requests.get(url, verify=resolve_verify(url), headers=headers, **kwargs)
