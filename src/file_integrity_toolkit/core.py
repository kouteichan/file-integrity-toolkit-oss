"""STEP 1 deterministic core: inspect, measure, compare.

Measurement statuses: OK / ERROR
Comparison statuses: MATCH / MISMATCH / ERROR

This module MUST NOT emit PASS / FAIL / UNKNOWN.
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
from typing import Any, BinaryIO, Optional, Protocol

# ---------------------------------------------------------------------------
# Frozen public codes (do not extend without reopening the specification)
# ---------------------------------------------------------------------------

CODE_INSPECTION_COMPLETE = "INSPECTION_COMPLETE"
CODE_HASH_MATCH = "HASH_MATCH"
CODE_HASH_MISMATCH = "HASH_MISMATCH"
CODE_INVALID_INPUT = "INVALID_INPUT"
CODE_FILE_NOT_FOUND = "FILE_NOT_FOUND"
CODE_NOT_A_REGULAR_FILE = "NOT_A_REGULAR_FILE"
CODE_READ_FAILURE = "READ_FAILURE"
CODE_FILE_CHANGED_DURING_READ = "FILE_CHANGED_DURING_READ"
CODE_INVALID_SHA256 = "INVALID_SHA256"
CODE_VERIFIER_SELF_TEST_FAILED = "VERIFIER_SELF_TEST_FAILED"

STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
STATUS_MATCH = "MATCH"
STATUS_MISMATCH = "MISMATCH"

_SHA256_ASCII_RE = re.compile(r"[0-9A-Fa-f]{64}")
_ASCII_WHITESPACE = " \t\r\n\v\f"
_CHUNK_SIZE = 64 * 1024

# FIPS 180-4 SHA-256 known-answer vectors used by the runtime self-test.
_KAT_VECTORS = (
    (
        b"",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),
    (
        b"abc",
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    ),
)

_STABILITY_SIGNALS = ("size_before", "bytes_read", "size_after")


def _result(status: str, code: str, data: Optional[dict] = None) -> dict:
    return {"status": status, "code": code, "data": {} if data is None else data}


# ---------------------------------------------------------------------------
# Internal I/O and digest seams (not part of the public API)
# ---------------------------------------------------------------------------


class _IOProvider(Protocol):
    def resolve(self, path: str) -> str: ...

    def stat(self, path: str) -> os.stat_result: ...

    def open_binary_read(self, path: str) -> BinaryIO: ...

    def fstat(self, fileobj: BinaryIO) -> os.stat_result: ...

    def read(self, fileobj: BinaryIO, size: int) -> bytes: ...


class _DigestFactory(Protocol):
    def new_sha256(self) -> Any: ...


class _StdIOProvider:
    """Production filesystem operations."""

    def resolve(self, path: str) -> str:
        return os.path.realpath(path)

    def stat(self, path: str) -> os.stat_result:
        return os.stat(path)

    def open_binary_read(self, path: str) -> BinaryIO:
        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        # Optional hardening: avoid blocking if a non-regular object appears
        # between the pre-open eligibility check and open(). Not required by
        # the portable STEP 1 contract.
        flags |= getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        try:
            return os.fdopen(fd, "rb")
        except Exception:
            os.close(fd)
            raise

    def fstat(self, fileobj: BinaryIO) -> os.stat_result:
        return os.fstat(fileobj.fileno())

    def read(self, fileobj: BinaryIO, size: int) -> bytes:
        return fileobj.read(size)


class _StdDigestFactory:
    def new_sha256(self) -> Any:
        return hashlib.sha256()


_DEFAULT_IO_PROVIDER: _IOProvider = _StdIOProvider()
_DEFAULT_DIGEST_FACTORY: _DigestFactory = _StdDigestFactory()

_io_provider: _IOProvider = _DEFAULT_IO_PROVIDER
_digest_factory: _DigestFactory = _DEFAULT_DIGEST_FACTORY
# None = not yet run; True = passed (cached); False = failed.
_self_test_ok: Optional[bool] = None


def _set_io_provider(provider: Optional[_IOProvider]) -> None:
    """Internal test seam. Not part of the public API."""
    global _io_provider
    _io_provider = provider if provider is not None else _DEFAULT_IO_PROVIDER


def _set_digest_factory(factory: Optional[_DigestFactory]) -> None:
    """Internal test seam. Not part of the public API."""
    global _digest_factory
    _digest_factory = factory if factory is not None else _DEFAULT_DIGEST_FACTORY


def _reset_runtime_self_test() -> None:
    """Internal test seam. Clears the process-lifetime KAT cache."""
    global _self_test_ok
    _self_test_ok = None


def _reset_internal_seams() -> None:
    """Restore production providers and clear the KAT cache."""
    _set_io_provider(None)
    _set_digest_factory(None)
    _reset_runtime_self_test()


# ---------------------------------------------------------------------------
# Runtime SHA-256 Known Answer Test
# ---------------------------------------------------------------------------


def _run_sha256_self_test() -> bool:
    try:
        for payload, expected in _KAT_VECTORS:
            hasher = _digest_factory.new_sha256()
            hasher.update(payload)
            digest = hasher.hexdigest()
            if not isinstance(digest, str):
                return False
            if _SHA256_ASCII_RE.fullmatch(digest) is None:
                return False
            if digest.lower() != expected:
                return False
        return True
    except Exception:
        return False


def _ensure_sha256_self_test() -> bool:
    """Run the KAT once per process.

    A successful result is cached for the process lifetime. A failed result
    is also remembered so measurement cannot proceed until an internal reset.
    """
    global _self_test_ok
    if _self_test_ok is True:
        return True
    if _self_test_ok is False:
        return False
    ok = _run_sha256_self_test()
    _self_test_ok = ok
    return ok


def _self_test_failed_result() -> dict:
    return _result(STATUS_ERROR, CODE_VERIFIER_SELF_TEST_FAILED, {})


# ---------------------------------------------------------------------------
# Path / OSError mapping
# ---------------------------------------------------------------------------


def _normalize_file_path_arg(file_path: Any) -> Optional[str]:
    """Return a str path, or None if the argument is not a usable path."""
    if isinstance(file_path, str):
        return file_path
    if isinstance(file_path, os.PathLike):
        fspath = os.fspath(file_path)
        if isinstance(fspath, str):
            return fspath
        return None
    return None


def _map_os_error_code(exc: OSError) -> str:
    """Map OS errors onto the frozen public code set. Conservative default."""
    err = exc.errno
    if isinstance(exc, FileNotFoundError) or err in (
        errno.ENOENT,
        errno.ENOTDIR,
        errno.ELOOP,
    ):
        return CODE_FILE_NOT_FOUND
    if isinstance(exc, IsADirectoryError) or err == errno.EISDIR:
        return CODE_NOT_A_REGULAR_FILE
    return CODE_READ_FAILURE


def _os_error_result(
    exc: OSError,
    *,
    input_path: Optional[str] = None,
    resolved_path: Optional[str] = None,
) -> dict:
    data: dict[str, Any] = {}
    if input_path is not None:
        data["input_path"] = input_path
    if resolved_path is not None:
        data["resolved_path"] = resolved_path
    data["os_errno"] = exc.errno
    return _result(STATUS_ERROR, _map_os_error_code(exc), data)


# ---------------------------------------------------------------------------
# inspect_file — canonical measurement primitive
# ---------------------------------------------------------------------------


def inspect_file(file_path: Any) -> dict:
    """Measure SHA-256 and size of a local regular file in one read pass.

    Returns a structured Result: status OK/ERROR, a frozen code, and data.
    """
    if not _ensure_sha256_self_test():
        return _self_test_failed_result()

    input_path = _normalize_file_path_arg(file_path)
    if input_path is None or input_path == "":
        return _result(
            STATUS_ERROR,
            CODE_INVALID_INPUT,
            {"invalid_fields": ["file_path"]},
        )

    provider = _io_provider

    try:
        resolved_path = provider.resolve(input_path)
    except OSError as exc:
        return _os_error_result(exc, input_path=input_path)

    try:
        pre_stat = provider.stat(resolved_path)
    except OSError as exc:
        return _os_error_result(
            exc, input_path=input_path, resolved_path=resolved_path
        )

    if not stat.S_ISREG(pre_stat.st_mode):
        return _result(
            STATUS_ERROR,
            CODE_NOT_A_REGULAR_FILE,
            {"input_path": input_path, "resolved_path": resolved_path},
        )

    try:
        fileobj = provider.open_binary_read(resolved_path)
    except OSError as exc:
        return _os_error_result(
            exc, input_path=input_path, resolved_path=resolved_path
        )

    try:
        try:
            stat_before = provider.fstat(fileobj)
        except OSError as exc:
            return _os_error_result(
                exc, input_path=input_path, resolved_path=resolved_path
            )

        if not stat.S_ISREG(stat_before.st_mode):
            return _result(
                STATUS_ERROR,
                CODE_NOT_A_REGULAR_FILE,
                {"input_path": input_path, "resolved_path": resolved_path},
            )

        hasher = _digest_factory.new_sha256()
        bytes_read = 0
        try:
            while True:
                chunk = provider.read(fileobj, _CHUNK_SIZE)
                if chunk is None:
                    return _result(
                        STATUS_ERROR,
                        CODE_READ_FAILURE,
                        {
                            "input_path": input_path,
                            "resolved_path": resolved_path,
                        },
                    )
                if chunk == b"":
                    break
                hasher.update(chunk)
                bytes_read += len(chunk)
        except OSError as exc:
            return _os_error_result(
                exc, input_path=input_path, resolved_path=resolved_path
            )
        except Exception:
            return _result(
                STATUS_ERROR,
                CODE_READ_FAILURE,
                {"input_path": input_path, "resolved_path": resolved_path},
            )

        try:
            stat_after = provider.fstat(fileobj)
        except OSError as exc:
            return _os_error_result(
                exc, input_path=input_path, resolved_path=resolved_path
            )

        size_before = stat_before.st_size
        size_after = stat_after.st_size
        signals = list(_STABILITY_SIGNALS)

        if not (size_before == bytes_read == size_after):
            return _result(
                STATUS_ERROR,
                CODE_FILE_CHANGED_DURING_READ,
                {
                    "input_path": input_path,
                    "resolved_path": resolved_path,
                    "stat_size_before": size_before,
                    "stat_size_after": size_after,
                    "bytes_read": bytes_read,
                    "stability_signals_checked": signals,
                },
            )

        try:
            digest = hasher.hexdigest()
        except Exception:
            return _result(
                STATUS_ERROR,
                CODE_READ_FAILURE,
                {"input_path": input_path, "resolved_path": resolved_path},
            )

        if not isinstance(digest, str) or _SHA256_ASCII_RE.fullmatch(digest) is None:
            return _result(
                STATUS_ERROR,
                CODE_READ_FAILURE,
                {"input_path": input_path, "resolved_path": resolved_path},
            )

        return _result(
            STATUS_OK,
            CODE_INSPECTION_COMPLETE,
            {
                "input_path": input_path,
                "resolved_path": resolved_path,
                "sha256": digest.lower(),
                "size_bytes": bytes_read,
                "stat_size_before": size_before,
                "stat_size_after": size_after,
                "stability_signals_checked": signals,
            },
        )
    finally:
        close = getattr(fileobj, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass


def calculate_sha256(file_path: Any) -> dict:
    """Thin wrapper over inspect_file(). Does not perform independent I/O."""
    return inspect_file(file_path)


def get_file_size(file_path: Any) -> dict:
    """Thin wrapper over inspect_file(). Does not perform independent I/O."""
    return inspect_file(file_path)


# ---------------------------------------------------------------------------
# compare_sha256 — string comparator (not disabled by KAT failure)
# ---------------------------------------------------------------------------


def _classify_sha256_argument(value: Any) -> tuple[str, Optional[str]]:
    """Return (class, normalized_or_none).

    class is one of: 'ok', 'type', 'sha256'.
    """
    if not isinstance(value, str):
        return "type", None
    trimmed = value.strip(_ASCII_WHITESPACE)
    if _SHA256_ASCII_RE.fullmatch(trimmed) is None:
        return "sha256", None
    return "ok", trimmed.lower()


def compare_sha256(expected: Any, actual: Any) -> dict:
    """Compare two values represented as raw-content SHA-256 digests.

    Statuses: MATCH / MISMATCH / ERROR. Never PASS / FAIL / UNKNOWN.
    """
    expected_class, expected_norm = _classify_sha256_argument(expected)
    actual_class, actual_norm = _classify_sha256_argument(actual)

    invalid_fields: list[str] = []
    field_reasons: dict[str, str] = {}

    if expected_class != "ok":
        invalid_fields.append("expected")
        field_reasons["expected"] = (
            "not_a_string" if expected_class == "type" else "invalid_sha256_representation"
        )
    if actual_class != "ok":
        invalid_fields.append("actual")
        field_reasons["actual"] = (
            "not_a_string" if actual_class == "type" else "invalid_sha256_representation"
        )

    if invalid_fields:
        # INVALID_INPUT takes precedence if any argument is the wrong type.
        has_type_error = expected_class == "type" or actual_class == "type"
        code = CODE_INVALID_INPUT if has_type_error else CODE_INVALID_SHA256
        return _result(
            STATUS_ERROR,
            code,
            {
                "invalid_fields": invalid_fields,
                "field_reasons": field_reasons,
            },
        )

    if expected_norm is None or actual_norm is None:
        missing = []
        if expected_norm is None:
            missing.append("expected")
        if actual_norm is None:
            missing.append("actual")
        return _result(
            STATUS_ERROR,
            CODE_INVALID_SHA256,
            {"invalid_fields": missing},
        )

    if expected_norm == actual_norm:
        return _result(
            STATUS_MATCH,
            CODE_HASH_MATCH,
            {"expected": expected_norm, "actual": actual_norm},
        )
    return _result(
        STATUS_MISMATCH,
        CODE_HASH_MISMATCH,
        {"expected": expected_norm, "actual": actual_norm},
    )
