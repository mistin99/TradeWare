"""Configuration validation tests."""

import pytest

from trade_ware.core.config import Settings


def test_production_rejects_empty_jwt_secret():
    """Require a real signing secret outside development."""
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(
            _env_file=None,
            app_environment="production",
            jwt_secret_key="",
        )


def test_production_accepts_a_random_length_secret():
    """Allow a sufficiently long production signing secret."""
    settings = Settings(
        _env_file=None,
        app_environment="production",
        jwt_secret_key="a" * 32,
    )

    assert settings.jwt_secret_key == "a" * 32
