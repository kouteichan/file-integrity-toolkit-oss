"""Runtime SHA-256 Known Answer Test coverage."""

from __future__ import annotations

import hashlib

from file_integrity_toolkit import compare_sha256, core, inspect_file

EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


class _WrongDigest:
    def update(self, data: bytes) -> None:
        return None

    def hexdigest(self) -> str:
        return "00" * 32


class _WrongDigestFactory:
    def new_sha256(self) -> _WrongDigest:
        return _WrongDigest()


class _RaisingDigest:
    def update(self, data: bytes) -> None:
        raise RuntimeError("hasher exploded")

    def hexdigest(self) -> str:
        return ABC


class _RaisingDigestFactory:
    def new_sha256(self) -> _RaisingDigest:
        return _RaisingDigest()


def test_kat_vectors_include_empty_and_abc():
    payloads = [item[0] for item in core._KAT_VECTORS]
    expecteds = [item[1] for item in core._KAT_VECTORS]
    assert b"" in payloads
    assert b"abc" in payloads
    assert EMPTY in expecteds
    assert ABC in expecteds


def test_kat_vectors_match_stdlib_sha256():
    for payload, expected in core._KAT_VECTORS:
        assert hashlib.sha256(payload).hexdigest() == expected
        assert expected == expected.lower()
        assert len(expected) == 64


def test_runtime_self_test_passes_with_stdlib_hasher():
    core._reset_runtime_self_test()
    assert core._run_sha256_self_test() is True
    assert core._ensure_sha256_self_test() is True
    # Cached success is reused.
    assert core._ensure_sha256_self_test() is True


def test_inspect_empty_file_matches_kat_empty(tmp_path):
    path = tmp_path / "empty"
    path.write_bytes(b"")
    result = inspect_file(str(path))
    assert result["status"] == "OK"
    assert result["data"]["sha256"] == EMPTY


def test_inspect_abc_file_matches_kat_abc(tmp_path):
    path = tmp_path / "abc"
    path.write_bytes(b"abc")
    result = inspect_file(str(path))
    assert result["status"] == "OK"
    assert result["data"]["sha256"] == ABC


def test_simulated_self_test_failure_blocks_measurement():
    core._set_digest_factory(_WrongDigestFactory())
    core._reset_runtime_self_test()
    result = inspect_file("/does/not/matter")
    assert result["status"] == "ERROR"
    assert result["code"] == "VERIFIER_SELF_TEST_FAILED"
    assert result["data"] == {}
    assert "sha256" not in result["data"]


def test_simulated_self_test_exception_blocks_measurement():
    core._set_digest_factory(_RaisingDigestFactory())
    core._reset_runtime_self_test()
    result = inspect_file("/does/not/matter")
    assert result["status"] == "ERROR"
    assert result["code"] == "VERIFIER_SELF_TEST_FAILED"


def test_compare_sha256_still_works_after_self_test_failure():
    core._set_digest_factory(_WrongDigestFactory())
    core._reset_runtime_self_test()
    failed = inspect_file("/x")
    assert failed["code"] == "VERIFIER_SELF_TEST_FAILED"
    compared = compare_sha256(EMPTY, EMPTY)
    assert compared["status"] == "MATCH"
    assert compared["code"] == "HASH_MATCH"


def test_self_test_failure_is_cached_until_reset():
    core._set_digest_factory(_WrongDigestFactory())
    core._reset_runtime_self_test()
    first = inspect_file("/x")
    # Restore a working hasher but leave the failed cache in place.
    core._set_digest_factory(None)
    second = inspect_file("/x")
    assert first["code"] == "VERIFIER_SELF_TEST_FAILED"
    assert second["code"] == "VERIFIER_SELF_TEST_FAILED"
    core._reset_runtime_self_test()
    # After reset, production hasher may proceed (file still missing).
    recovered = inspect_file("/x")
    assert recovered["code"] == "FILE_NOT_FOUND"
