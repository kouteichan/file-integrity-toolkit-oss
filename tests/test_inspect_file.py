"""Inspection and composition tests for inspect_file() and wrappers."""

from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path

import pytest

from file_integrity_toolkit import (
    calculate_sha256,
    compare_sha256,
    core,
    get_file_size,
    inspect_file,
)
from tests.helpers import ScriptedIOProvider, fake_stat

EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

_FORBIDDEN = {"PASS", "FAIL", "UNKNOWN"}


def _assert_measurement_shape(result: dict) -> None:
    assert set(result.keys()) == {"status", "code", "data"}
    assert isinstance(result["data"], dict)
    assert result["status"] in {"OK", "ERROR"}
    assert result["status"] not in _FORBIDDEN
    assert result["code"] not in _FORBIDDEN


def _assert_error(result: dict, code: str) -> None:
    _assert_measurement_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == code
    assert "sha256" not in result["data"]


def _assert_ok_measurement(result: dict, *, sha256: str, size: int) -> None:
    _assert_measurement_shape(result)
    assert result["status"] == "OK"
    assert result["code"] == "INSPECTION_COMPLETE"
    data = result["data"]
    assert data["sha256"] == sha256
    assert data["size_bytes"] == size
    assert data["stat_size_before"] == size
    assert data["stat_size_after"] == size
    assert data["stability_signals_checked"] == [
        "size_before",
        "bytes_read",
        "size_after",
    ]
    assert len(data["sha256"]) == 64
    assert data["sha256"] == data["sha256"].lower()


def test_known_regular_file(tmp_path: Path):
    path = tmp_path / "known.bin"
    path.write_bytes(b"abc")
    result = inspect_file(str(path))
    _assert_ok_measurement(result, sha256=ABC, size=3)
    assert result["data"]["input_path"] == str(path)
    assert result["data"]["resolved_path"] == os.path.realpath(str(path))


def test_known_sha256_matches_stdlib_oracle(tmp_path: Path):
    payload = b"The quick brown fox jumps over the lazy dog"
    path = tmp_path / "fox.bin"
    path.write_bytes(payload)
    result = inspect_file(str(path))
    expected = hashlib.sha256(payload).hexdigest()
    _assert_ok_measurement(result, sha256=expected, size=len(payload))


def test_one_byte_mutation_changes_digest(tmp_path: Path):
    path = tmp_path / "mut.bin"
    path.write_bytes(b"abc")
    before = inspect_file(str(path))
    path.write_bytes(b"abd")
    after = inspect_file(str(path))
    assert before["data"]["sha256"] != after["data"]["sha256"]
    assert before["data"]["size_bytes"] == after["data"]["size_bytes"] == 3
    compared = compare_sha256(before["data"]["sha256"], after["data"]["sha256"])
    assert compared["status"] == "MISMATCH"
    assert compared["code"] == "HASH_MISMATCH"


def test_same_size_different_content(tmp_path: Path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"xyz")
    b.write_bytes(b"xyZ")
    ra = inspect_file(str(a))
    rb = inspect_file(str(b))
    assert ra["data"]["size_bytes"] == rb["data"]["size_bytes"] == 3
    assert ra["data"]["sha256"] != rb["data"]["sha256"]


def test_true_zero_byte_regular_file(tmp_path: Path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    result = inspect_file(str(path))
    _assert_ok_measurement(result, sha256=EMPTY, size=0)
    compared = compare_sha256(EMPTY, result["data"]["sha256"])
    assert compared["status"] == "MATCH"
    assert compared["code"] == "HASH_MATCH"


def test_directory_not_a_regular_file(tmp_path: Path):
    result = inspect_file(str(tmp_path))
    _assert_error(result, "NOT_A_REGULAR_FILE")


def test_symlink_to_regular_file(tmp_path: Path):
    target = tmp_path / "target.bin"
    target.write_bytes(b"abc")
    link = tmp_path / "link.bin"
    link.symlink_to(target)
    result = inspect_file(str(link))
    _assert_ok_measurement(result, sha256=ABC, size=3)
    assert result["data"]["input_path"] == str(link)
    assert result["data"]["resolved_path"] == os.path.realpath(str(link))
    assert result["data"]["resolved_path"] == os.path.realpath(str(target))


def test_symlink_to_directory_not_a_regular_file(tmp_path: Path):
    link = tmp_path / "dirlink"
    link.symlink_to(tmp_path)
    result = inspect_file(str(link))
    _assert_error(result, "NOT_A_REGULAR_FILE")


def test_broken_symlink_file_not_found(tmp_path: Path):
    link = tmp_path / "broken"
    link.symlink_to(tmp_path / "missing-target")
    result = inspect_file(str(link))
    _assert_error(result, "FILE_NOT_FOUND")


def test_missing_file_not_found(tmp_path: Path):
    result = inspect_file(str(tmp_path / "does-not-exist"))
    _assert_error(result, "FILE_NOT_FOUND")


def test_empty_path_invalid_input():
    result = inspect_file("")
    _assert_error(result, "INVALID_INPUT")
    assert result["data"]["invalid_fields"] == ["file_path"]


def test_none_path_invalid_input():
    result = inspect_file(None)
    _assert_error(result, "INVALID_INPUT")


def test_pathlib_path_accepted(tmp_path: Path):
    path = tmp_path / "p.bin"
    path.write_bytes(b"abc")
    result = inspect_file(path)
    _assert_ok_measurement(result, sha256=ABC, size=3)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="os.mkfifo not available on this platform")
def test_fifo_not_a_regular_file(tmp_path: Path):
    fifo_path = tmp_path / "named.pipe"
    os.mkfifo(fifo_path)
    result = inspect_file(str(fifo_path))
    _assert_error(result, "NOT_A_REGULAR_FILE")


def test_character_device_not_a_regular_file():
    if not os.path.exists("/dev/null"):
        pytest.skip("/dev/null not present")
    result = inspect_file("/dev/null")
    _assert_error(result, "NOT_A_REGULAR_FILE")


def test_chunked_read_of_file_larger_than_chunk(tmp_path: Path):
    payload = b"A" * (64 * 1024 + 17)
    path = tmp_path / "large.bin"
    path.write_bytes(payload)
    result = inspect_file(str(path))
    expected = hashlib.sha256(payload).hexdigest()
    _assert_ok_measurement(result, sha256=expected, size=len(payload))


def test_inspect_file_result_fed_to_compare_sha256(tmp_path: Path):
    path = tmp_path / "roundtrip.bin"
    path.write_bytes(b"abc")
    measured = inspect_file(str(path))
    compared = compare_sha256(ABC, measured["data"]["sha256"])
    assert compared["status"] == "MATCH"
    assert compared["code"] == "HASH_MATCH"


def test_wrappers_delegate_to_inspect_file_without_independent_io(monkeypatch):
    sentinel = {
        "status": "OK",
        "code": "INSPECTION_COMPLETE",
        "data": {"marker": True},
    }
    calls = {"n": 0}

    def fake_inspect(file_path):
        calls["n"] += 1
        return sentinel

    monkeypatch.setattr(core, "inspect_file", fake_inspect)
    assert core.calculate_sha256("any") is sentinel
    assert core.get_file_size("any") is sentinel
    assert calls["n"] == 2


def test_wrappers_return_inspect_file_result(tmp_path: Path):
    path = tmp_path / "w.bin"
    path.write_bytes(b"abc")
    measured = inspect_file(str(path))
    hashed = calculate_sha256(str(path))
    sized = get_file_size(str(path))
    assert hashed["status"] == measured["status"] == "OK"
    assert sized["data"]["sha256"] == hashed["data"]["sha256"] == ABC
    assert sized["data"]["size_bytes"] == 3


def test_simulated_mutation_during_read_file_changed():
    # T-ZERO-02 style: before size > 0, bytes_read = 0.
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(5),
        fstat_before=fake_stat(5),
        fstat_after=fake_stat(5),
        chunks=[b""],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/target")
    _assert_error(result, "FILE_CHANGED_DURING_READ")
    assert result["data"]["stat_size_before"] == 5
    assert result["data"]["bytes_read"] == 0
    assert result["data"]["stat_size_after"] == 5


def test_simulated_stat_read_inconsistency_size_after_differs():
    payload = b"abcd"
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(4),
        fstat_before=fake_stat(4),
        fstat_after=fake_stat(5),
        chunks=[payload, b""],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/target")
    _assert_error(result, "FILE_CHANGED_DURING_READ")
    assert result["data"]["stat_size_before"] == 4
    assert result["data"]["bytes_read"] == 4
    assert result["data"]["stat_size_after"] == 5


def test_simulated_bytes_read_differs_from_stat_size():
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(10),
        fstat_before=fake_stat(10),
        fstat_after=fake_stat(10),
        chunks=[b"partial", b""],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/target")
    _assert_error(result, "FILE_CHANGED_DURING_READ")
    assert result["data"]["bytes_read"] == 7


def test_scripted_stable_read_succeeds():
    payload = b"abc"
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(3),
        fstat_before=fake_stat(3),
        fstat_after=fake_stat(3),
        chunks=[payload, b""],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/target")
    _assert_ok_measurement(result, sha256=ABC, size=3)


def test_scripted_zero_byte_file_succeeds():
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(0),
        fstat_before=fake_stat(0),
        fstat_after=fake_stat(0),
        chunks=[b""],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/empty")
    _assert_ok_measurement(result, sha256=EMPTY, size=0)


def test_read_none_on_zero_size_file_is_read_failure():
    """R-01: None from read() is READ_FAILURE, not EOF.

    Size 0 is required so a missing None-check cannot be masked by the
    later stability mismatch (0 == 0 == 0 would otherwise succeed).
    """
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(0),
        fstat_before=fake_stat(0),
        fstat_after=fake_stat(0),
        chunks=[None],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/none-read")
    _assert_error(result, "READ_FAILURE")
    assert result["status"] != "OK"
    assert result["code"] != "FILE_CHANGED_DURING_READ"
    assert result["code"] != "INSPECTION_COMPLETE"


def test_opened_fd_fifo_reconfirmation_not_a_regular_file():
    """R-02: post-open fstat must reject a non-regular opened object."""
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(3, regular=True),
        fstat_before=fake_stat(0, fifo=True),
        fstat_after=fake_stat(0, fifo=True),
        chunks=[b"abc"],
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/fd-fifo")
    _assert_error(result, "NOT_A_REGULAR_FILE")
    assert provider._fstat_calls == 1


def test_resolve_error_eloop_maps_to_file_not_found():
    provider = ScriptedIOProvider(
        resolve_error=OSError(errno.ELOOP, "too many levels of symbolic links"),
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/loop")
    _assert_error(result, "FILE_NOT_FOUND")
    assert provider._fstat_calls == 0


def test_stat_error_enotdir_maps_to_file_not_found():
    provider = ScriptedIOProvider(
        stat_error=OSError(errno.ENOTDIR, "not a directory"),
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/enotdir")
    _assert_error(result, "FILE_NOT_FOUND")
    assert provider._fstat_calls == 0


def test_read_error_maps_to_read_failure():
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(3),
        fstat_before=fake_stat(3),
        fstat_after=fake_stat(3),
        read_error=OSError(errno.EIO, "input/output error"),
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/read-error")
    _assert_error(result, "READ_FAILURE")
    assert provider._fstat_calls == 1


def test_fstat_after_error_maps_conservatively_to_read_failure():
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(3),
        fstat_before=fake_stat(3),
        fstat_after=fake_stat(3),
        chunks=[b"abc", b""],
        fstat_after_error=OSError(errno.EIO, "input/output error"),
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/fstat-after")
    _assert_error(result, "READ_FAILURE")
    assert provider._fstat_calls == 2


def test_permission_denied_maps_to_read_failure(tmp_path: Path):
    path = tmp_path / "secret.bin"
    path.write_bytes(b"abc")
    path.chmod(0)
    try:
        if os.access(str(path), os.R_OK):
            pytest.skip("process can read mode-000 files (likely running as root)")
        result = inspect_file(str(path))
        _assert_error(result, "READ_FAILURE")
    finally:
        path.chmod(0o644)


def test_open_oserror_maps_conservatively():
    provider = ScriptedIOProvider(
        pre_stat=fake_stat(3),
        fstat_before=fake_stat(3),
        fstat_after=fake_stat(3),
        open_error=OSError(errno.EACCES, "permission denied"),
    )
    core._set_io_provider(provider)
    result = inspect_file("/scripted/denied")
    _assert_error(result, "READ_FAILURE")
