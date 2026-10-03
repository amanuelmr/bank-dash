"""Config validation - the settings that decide whether cookies work at all.

These guard a failure mode that is otherwise invisible until production: the
app starts cleanly, login "works" locally, and the deployed domain silently
fails because the browser rejects the cookie.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides) -> Settings:
    # _env_file=None so a developer's local .env cannot change the outcome.
    return Settings(_env_file=None, **overrides)


def test_localhost_defaults_are_valid():
    settings = _settings()

    assert settings.cookie_samesite == "lax"
    assert settings.cookie_secure is False
    assert settings.cookies_are_cross_site is False


def test_samesite_none_without_secure_is_rejected():
    """Browsers drop a cross-site cookie that is not Secure.

    Failing at startup is the point: the alternative is a deploy that boots,
    serves the app, and rejects every login.
    """
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        _settings(cookie_samesite="none", cookie_secure=False)


def test_samesite_none_with_secure_is_allowed():
    settings = _settings(cookie_samesite="none", cookie_secure=True)

    assert settings.cookies_are_cross_site is True


def test_unrecognised_samesite_is_rejected():
    """A typo like "None-ish" is silently treated as invalid by browsers."""
    with pytest.raises(ValidationError, match="COOKIE_SAMESITE"):
        _settings(cookie_samesite="none-ish")


def test_samesite_comparison_ignores_case_and_padding():
    settings = _settings(cookie_samesite=" NONE ", cookie_secure=True)

    assert settings.cookies_are_cross_site is True


def test_refresh_cookie_is_scoped_to_the_auth_routes():
    assert _settings(api_v1_prefix="/api/v1").auth_cookie_path == "/api/v1/auth"
    # Derived, not hardcoded, so moving the API prefix cannot silently break it.
    assert _settings(api_v1_prefix="/bank/v2").auth_cookie_path == "/bank/v2/auth"