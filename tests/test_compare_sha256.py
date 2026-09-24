"""Unit tests for compare_sha256()."""

from __future__ import annotations

from file_integrity_toolkit import compare_sha256

EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
ABC_FLIP = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ae"


def _assert_result_shape(result: dict) -> None:
    assert set(result.keys()) == {"status", "code", "data"}
    assert isinstance(result["data"], dict)
    assert result["status"] in {"MATCH", "MISMATCH", "ERROR"}
    assert result["status"] not in {"PASS", "FAIL", "UNKNOWN"}
    assert result["code"] not in {"PASS", "FAIL", "UNKNOWN"}


def test_exact_same_digest_match():
    result = compare_sha256(ABC, ABC)
    _assert_result_shape(result)
    assert result["status"] == "MATCH"
    assert result["code"] == "HASH_MATCH"
    assert result["data"]["expected"] == ABC
    assert result["data"]["actual"] == ABC


def test_one_character_valid_difference_mismatch():
    result = compare_sha256(ABC, ABC_FLIP)
    _assert_result_shape(result)
    assert result["status"] == "MISMATCH"
    assert result["code"] == "HASH_MISMATCH"
    assert result["data"]["expected"] == ABC
    assert result["data"]["actual"] == ABC_FLIP


def test_uppercase_vs_lowercase_match():
    result = compare_sha256(ABC.upper(), ABC)
    _assert_result_shape(result)
    assert result["status"] == "MATCH"
    assert result["code"] == "HASH_MATCH"
    assert result["data"]["expected"] == ABC
    assert result["data"]["actual"] == ABC


def test_surrounding_whitespace_match():
    result = compare_sha256("  " + ABC + "\n", "\t" + ABC + "  ")
    _assert_result_shape(result)
    assert result["status"] == "MATCH"
    assert result["code"] == "HASH_MATCH"
    assert result["data"]["expected"] == ABC
    assert result["data"]["actual"] == ABC


def test_ascii_vt_ff_cr_surrounding_whitespace_match():
    wrapped = "\v\f\r" + ABC + "\r\f\v"
    result = compare_sha256(wrapped, ABC)
    _assert_result_shape(result)
    assert result["status"] == "MATCH"
    assert result["code"] == "HASH_MATCH"
    assert result["data"]["expected"] == ABC


def test_nbsp_surrounding_whitespace_invalid_sha256():
    result = compare_sha256("\u00a0" + ABC, ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_nbsp_trailing_whitespace_invalid_sha256():
    result = compare_sha256(ABC, ABC + "\u00a0")
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["actual"]


def test_0x_prefix_invalid_sha256():
    result = compare_sha256("0x" + ABC, ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_63_chars_invalid_sha256():
    result = compare_sha256(ABC[:-1], ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_65_chars_invalid_sha256():
    result = compare_sha256(ABC + "a", ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_non_hex_invalid_sha256():
    result = compare_sha256("g" + ABC[1:], ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_empty_string_invalid_sha256():
    result = compare_sha256("", ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"


def test_internal_whitespace_invalid_sha256():
    value = ABC[:32] + " " + ABC[32:]
    result = compare_sha256(value, ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"


def test_unicode_hex_like_invalid_sha256():
    # Fullwidth digit 5 is hex-like but not ASCII [0-9A-Fa-f].
    value = ABC[:-1] + "\uff15"
    assert len(value) == 64
    result = compare_sha256(value, ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"


def test_none_invalid_input():
    result = compare_sha256(None, ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_INPUT"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_bytes_invalid_input():
    result = compare_sha256(ABC.encode("ascii"), ABC)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_INPUT"
    assert result["data"]["invalid_fields"] == ["expected"]


def test_argument_reversal_same_status_code_match():
    forward = compare_sha256(ABC, ABC.upper())
    reverse = compare_sha256(ABC.upper(), ABC)
    assert forward["status"] == reverse["status"] == "MATCH"
    assert forward["code"] == reverse["code"] == "HASH_MATCH"


def test_argument_reversal_same_status_code_mismatch():
    forward = compare_sha256(ABC, ABC_FLIP)
    reverse = compare_sha256(ABC_FLIP, ABC)
    assert forward["status"] == reverse["status"] == "MISMATCH"
    assert forward["code"] == reverse["code"] == "HASH_MISMATCH"
    assert forward["data"]["expected"] != reverse["data"]["expected"]


def test_argument_reversal_same_status_code_invalid_sha256():
    forward = compare_sha256("0x" + ABC, ABC)
    reverse = compare_sha256(ABC, "0x" + ABC)
    assert forward["status"] == reverse["status"] == "ERROR"
    assert forward["code"] == reverse["code"] == "INVALID_SHA256"
    assert forward["data"]["invalid_fields"] == ["expected"]
    assert reverse["data"]["invalid_fields"] == ["actual"]


def test_different_invalid_classes_invalid_input_takes_precedence():
    result = compare_sha256(None, "not-a-digest")
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_INPUT"
    assert result["data"]["invalid_fields"] == ["expected", "actual"]


def test_different_invalid_classes_reversed_still_invalid_input():
    result = compare_sha256("not-a-digest", None)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_INPUT"
    assert result["data"]["invalid_fields"] == ["expected", "actual"]


def test_both_none_invalid_input():
    result = compare_sha256(None, 123)
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_INPUT"
    assert result["data"]["invalid_fields"] == ["expected", "actual"]


def test_both_invalid_sha256_records_both_fields():
    result = compare_sha256("0x" + ABC, ABC[:-1])
    _assert_result_shape(result)
    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_SHA256"
    assert result["data"]["invalid_fields"] == ["expected", "actual"]


def test_never_emits_pass_fail_unknown():
    samples = [
        compare_sha256(ABC, ABC),
        compare_sha256(ABC, EMPTY),
        compare_sha256(None, ABC),
        compare_sha256("zz", ABC),
    ]
    for result in samples:
        assert result["status"] not in {"PASS", "FAIL", "UNKNOWN"}
        assert result["code"] not in {"PASS", "FAIL", "UNKNOWN"}
