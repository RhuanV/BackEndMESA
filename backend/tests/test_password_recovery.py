"""Password-recovery-by-code service logic, using in-memory fakes (no DB)."""

import pytest

from geoavia_backend.services.password_reset import (
    MAX_CODE_ATTEMPTS,
    PasswordRecoveryService,
)


class FakeUsers:
    def __init__(self):
        alice = {"id": 1, "username": "alice", "hash": "x", "role": "operador"}
        admin = {"id": 2, "username": "admin", "hash": "y", "role": "desenvolvedor"}
        self._by_id = {1: alice, 2: admin}
        self._by_name = {"alice": alice, "admin": admin}
        self.updated = {}

    def obtain_user_from_id(self, uid):
        return self._by_id.get(uid)

    def obtain_user_from_username(self, name):
        return self._by_name.get(name)

    def update_password_hash(self, uid, new_hash):
        self.updated[uid] = new_hash
        return True


class FakeCodes:
    def __init__(self):
        self.rows = []
        self._id = 0

    def invalidate_active_for_user(self, user_id):
        for r in self.rows:
            if r["user_id"] == user_id and r["used_at"] is None:
                r["used_at"] = "used"

    def create_code(self, user_id, code_hash, expires_at, created_by):
        self._id += 1
        self.rows.append(
            {
                "id": self._id,
                "user_id": user_id,
                "code_hash": code_hash,
                "attempts": 0,
                "expires_at": expires_at,
                "used_at": None,
            }
        )
        return self._id

    def get_active_for_user(self, user_id):
        return [dict(r) for r in self.rows if r["user_id"] == user_id and r["used_at"] is None]

    def mark_used(self, code_id):
        for r in self.rows:
            if r["id"] == code_id:
                r["used_at"] = "used"

    def increment_attempts(self, code_id):
        for r in self.rows:
            if r["id"] == code_id:
                r["attempts"] += 1
                return r["attempts"]


def make_service():
    return PasswordRecoveryService(users=FakeUsers(), codes=FakeCodes())


def test_issue_then_reset_happy_path():
    svc = make_service()
    code = svc.issue_code(1, issued_by_id=2)["code"]
    assert svc.reset_with_code("alice", code, "NewPass@12") is True
    assert 1 in svc.users.updated


def test_issuing_a_code_returns_expiry_and_invalidates_previous():
    svc = make_service()
    first = svc.issue_code(1, 2)
    assert "expires_at" in first and len(first["code"]) == 20
    svc.issue_code(1, 2)  # second issue invalidates the first
    active = svc.codes.get_active_for_user(1)
    assert len(active) == 1


def test_wrong_code_is_generic_and_counts_attempt():
    svc = make_service()
    svc.issue_code(1, 2)
    with pytest.raises(ValueError):
        svc.reset_with_code("alice", "WRONGCOD", "NewPass@12")
    assert svc.codes.get_active_for_user(1)[0]["attempts"] == 1


def test_code_is_single_use():
    svc = make_service()
    code = svc.issue_code(1, 2)["code"]
    assert svc.reset_with_code("alice", code, "NewPass@12") is True
    with pytest.raises(ValueError):
        svc.reset_with_code("alice", code, "Another@12")


def test_unknown_username_is_generic():
    svc = make_service()
    with pytest.raises(ValueError):
        svc.reset_with_code("ghost", "ABCDEFGH", "NewPass@12")


def test_short_password_is_rejected():
    svc = make_service()
    code = svc.issue_code(1, 2)["code"]
    with pytest.raises(ValueError):
        svc.reset_with_code("alice", code, "short")


def test_weak_password_is_rejected():
    # Long enough, but missing uppercase and a special character.
    svc = make_service()
    code = svc.issue_code(1, 2)["code"]
    with pytest.raises(ValueError):
        svc.reset_with_code("alice", code, "lowercase123")


def test_protected_dev_user_cannot_get_a_code():
    svc = make_service()
    with pytest.raises(ValueError):
        svc.issue_code(2, 2)  # user 'admin' is the protected DEV_USER


def test_code_is_burned_after_max_attempts():
    svc = make_service()
    svc.issue_code(1, 2)
    # MAX_CODE_ATTEMPTS wrong tries reach the cap; one more burns the code.
    for _ in range(MAX_CODE_ATTEMPTS + 1):
        with pytest.raises(ValueError):
            svc.reset_with_code("alice", "WRONGCOD", "NewPass@12")
    assert svc.codes.get_active_for_user(1) == []
