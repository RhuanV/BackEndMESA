"""Password-strength policy (core.passwords)."""
import pytest

from geoavia_backend.core.passwords import validate_password_strength


def test_strong_password_passes():
    # No exception means it is accepted.
    validate_password_strength("Str0ng@Pass")


@pytest.mark.parametrize(
    "password",
    [
        "Ab1@567",        # too short (7 chars)
        "lowercase1@",    # no uppercase
        "UPPERCASE1@",    # no lowercase
        "NoDigits@Abc",   # no digit
        "NoSpecial123A",  # no special character
    ],
)
def test_weak_passwords_are_rejected(password):
    with pytest.raises(ValueError):
        validate_password_strength(password)
