"""Pytest fixtures for the public local deterministic core."""

from __future__ import annotations

import pytest

from file_integrity_toolkit import core


@pytest.fixture(autouse=True)
def _restore_internal_seams():
    core._reset_internal_seams()
    yield
    core._reset_internal_seams()
