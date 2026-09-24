"""Stable shared helpers for STEP 1 tests. Not a pytest plugin."""

from __future__ import annotations

import stat
from types import SimpleNamespace
from typing import Any, Optional


def fake_stat(
    size: int,
    *,
    regular: bool = True,
    fifo: bool = False,
    directory: bool = False,
):
    if fifo:
        mode = stat.S_IFIFO | 0o644
    elif directory:
        mode = stat.S_IFDIR | 0o755
    elif regular:
        mode = stat.S_IFREG | 0o644
    else:
        mode = stat.S_IFCHR | 0o666
    return SimpleNamespace(
        st_size=size,
        st_mode=mode,
        st_ino=1,
        st_dev=1,
        st_mtime=0,
        st_ctime=0,
    )


class DummyFile:
    def close(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class ScriptedIOProvider:
    """Deterministic IO provider for otherwise-racy failure paths."""

    def __init__(
        self,
        *,
        resolved_path: str = "/scripted/target",
        pre_stat: Any = None,
        fstat_before: Any = None,
        fstat_after: Any = None,
        chunks: Optional[list] = None,
        resolve_error: Optional[OSError] = None,
        stat_error: Optional[OSError] = None,
        open_error: Optional[OSError] = None,
        read_error: Optional[OSError] = None,
        fstat_after_error: Optional[OSError] = None,
    ) -> None:
        self._resolved_path = resolved_path
        self._pre_stat = pre_stat
        self._fstat_before = fstat_before
        self._fstat_after = fstat_after
        self._chunks = list(chunks or [])
        self._resolve_error = resolve_error
        self._stat_error = stat_error
        self._open_error = open_error
        self._read_error = read_error
        self._fstat_after_error = fstat_after_error
        self._fstat_calls = 0

    def resolve(self, path: str) -> str:
        if self._resolve_error is not None:
            raise self._resolve_error
        return self._resolved_path

    def stat(self, path: str) -> Any:
        if self._stat_error is not None:
            raise self._stat_error
        return self._pre_stat

    def open_binary_read(self, path: str) -> DummyFile:
        if self._open_error is not None:
            raise self._open_error
        return DummyFile()

    def fstat(self, fileobj: Any) -> Any:
        self._fstat_calls += 1
        if self._fstat_calls == 1:
            return self._fstat_before
        if self._fstat_after_error is not None:
            raise self._fstat_after_error
        return self._fstat_after

    def read(self, fileobj: Any, size: int):
        if self._read_error is not None:
            raise self._read_error
        if self._chunks:
            return self._chunks.pop(0)
        return b""
