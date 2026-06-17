"""Settings fail-fast contract (spec §6.5)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def test_short_jwt_secret_rejected_in_jwt_mode():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, auth_mode="jwt", jwt_secret="too-short")


def test_short_jwt_secret_allowed_when_auth_disabled():
    s = Settings(_env_file=None, auth_mode="none", jwt_secret="short")
    assert s.auth_mode == "none"


def test_llm_threshold_out_of_range_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret="x" * 32, llm_threshold=1.5)


def test_cors_and_domain_helpers_parse_csv():
    s = Settings(
        _env_file=None,
        jwt_secret="x" * 32,
        cors_origins="http://a.com, http://b.com",
        allowed_email_domains="@cbioportal.org, Example.COM",
    )
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]
    assert s.allowed_email_domain_list == ["cbioportal.org", "example.com"]
