"""Upload byte-size guard tests (spec §6.4). No row/column ceilings exist."""

from __future__ import annotations

import pytest

from app.core.uploads import PayloadTooLargeError, check_upload_size


def test_upload_size_within_limit_ok():
    check_upload_size(5 * 1024 * 1024, max_mb=50)  # no raise


def test_upload_size_over_limit_raises_413():
    with pytest.raises(PayloadTooLargeError) as ei:
        check_upload_size(60 * 1024 * 1024, max_mb=50)
    assert ei.value.status_code == 413
    assert ei.value.details["limit_bytes"] == 50 * 1024 * 1024
