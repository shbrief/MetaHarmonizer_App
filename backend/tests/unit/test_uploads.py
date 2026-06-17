"""Boundary-limit helper tests (spec §6.4)."""

from __future__ import annotations

import pytest

from app.core.errors import ValidationError
from app.core.uploads import (
    PayloadTooLargeError,
    check_table_shape,
    check_upload_size,
)


def test_upload_size_within_limit_ok():
    check_upload_size(5 * 1024 * 1024, max_mb=50)  # no raise


def test_upload_size_over_limit_raises_413():
    with pytest.raises(PayloadTooLargeError) as ei:
        check_upload_size(60 * 1024 * 1024, max_mb=50)
    assert ei.value.status_code == 413
    assert ei.value.details["limit_bytes"] == 50 * 1024 * 1024


def test_table_shape_within_limits_ok():
    check_table_shape(n_rows=1000, n_cols=80, max_rows=100_000, max_cols=500)


def test_too_many_columns_raises_422():
    with pytest.raises(ValidationError) as ei:
        check_table_shape(n_rows=10, n_cols=999, max_rows=100_000, max_cols=500)
    assert ei.value.status_code == 422
    assert ei.value.details["columns"] == 999


def test_too_many_rows_raises_422():
    with pytest.raises(ValidationError) as ei:
        check_table_shape(n_rows=200_000, n_cols=10, max_rows=100_000, max_cols=500)
    assert ei.value.status_code == 422
    assert ei.value.details["rows"] == 200_000
