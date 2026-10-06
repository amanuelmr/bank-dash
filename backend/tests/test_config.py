"""Config validation - the settings that decide whether cookies work at all.

These guard a failure mode that is otherwise invisible until production: the
app starts cleanly, login "works" locally, and the deployed domain silently
fails because the browser rejects the cookie.
"""

import pytest
from pydantic import ValidationError

from app.core.config import DEV_SECRET_KEY, Settings


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


def test_access_token_default_is_short_lived():
    """An access token cannot be revoked before it expires, so its lifetime is
    exactly how long a leak stays usable - through a log line, a proxy, a shared
    machine. 24 hours was a placeholder predating refresh-on-401, and nothing
    should quietly restore it.

    Asserted against the *default*, so it stays deterministic regardless of what
    any local .env happens to set.
    """
    assert _settings().access_token_expire_minutes <= 60


def test_refresh_window_is_longer_than_the_access_token():
    """The sliding window only works if the refresh token outlives the access
    token by a wide margin - otherwise a session would expire mid-use."""
    settings = _settings()

    assert (
        settings.refresh_token_expire_days * 24 * 60
        > settings.access_token_expire_minutes
    )


def test_refresh_cookie_is_scoped_to_the_auth_routes():
    assert _settings(api_v1_prefix="/api/v1").auth_cookie_path == "/api/v1/auth"
    # Derived, not hardcoded, so moving the API prefix cannot silently break it.
    assert _settings(api_v1_prefix="/bank/v2").auth_cookie_path == "/bank/v2/auth"


def test_access_cookie_outlives_the_jwt_it_carries():
    """The invariant that keeps a renewable session reachable.

    The refresh cookie is scoped to the API's auth routes, so the frontend's
    route gate can only ever see the access cookie. If the cookie died at the
    same moment the JWT did, a user with a live refresh token would be bounced
    to sign-in and the client's refresh-and-replay would never get to run.
    """
    settings = _settings()

    assert settings.access_cookie_max_age > settings.access_token_expire_minutes * 60


def test_access_cookie_lifetime_tracks_the_refresh_token():
    """Both cookies are reissued together on every refresh, so tying the access
    cookie to the refresh window is what makes the session a sliding one."""
    settings = _settings(refresh_token_expire_days=7)

    assert settings.access_cookie_max_age == 7 * 86400


def test_shortening_the_refresh_window_shortens_both_cookies():
    """Guards the reverse mistake: shrinking the refresh lifetime must not leave
    the access cookie alive long after there is anything left to refresh with."""
    long_window = _settings(refresh_token_expire_days=30)
    short_window = _settings(refresh_token_expire_days=1)

    assert short_window.access_cookie_max_age < long_window.access_cookie_max_age


def test_production_refuses_the_development_signing_key():
    """The dev key is published in this repository.

    Signing with it means anyone who has read the source can mint an access token
    for any user id, so this is worth failing startup over rather than warning.
    """
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        _settings(environment="production")


def test_production_accepts_a_real_signing_key():
    settings = _settings(environment="production", secret_key="k" * 64)

    assert settings.environment == "production"


def test_development_still_boots_on_the_dev_key():
    """A fresh clone has to run before anyone has configured a secret."""
    assert _settings().environment == "development"
    assert _settings().secret_key == DEV_SECRET_KEY
