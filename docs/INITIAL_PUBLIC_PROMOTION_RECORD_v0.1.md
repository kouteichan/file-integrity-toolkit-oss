# Initial Public Promotion Record v0.1

**Date:** 2026-09-24  
**Status:** PUBLIC PROMOTION CANDIDATE / PUBLIC CI PASS / INDEPENDENT REVIEW PENDING / NOT MERGED

## Public boundary

This candidate contains only the Local Deterministic Core.

Included public capability:

```text
local file
→ deterministic measurement
→ optional direct SHA-256 comparison
```

Remote-provider architecture is not included in this promotion.

## Canonical provenance

Private canonical source snapshot:

```text
a6b1666636326651484b9b4d37999ab97bf9edbe
```

Promoted without semantic modification:

- `.gitignore`
- `src/file_integrity_toolkit/core.py`
- `tests/__init__.py`
- `tests/helpers.py`
- `tests/test_compare_sha256.py`
- `tests/test_inspect_file.py`
- `tests/test_self_test.py`

The Git blob identities of these copied files match the canonical source
snapshot exactly.

Public-specific sanitized / created artifacts:

- `src/file_integrity_toolkit/__init__.py`
- `tests/conftest.py`
- `pyproject.toml`
- `README.md`
- `CONTRIBUTING.md`
- `.github/workflows/tests.yml`
- this promotion record
- public candidate test-run record
- independent-review packet

## Held from the initial public release

- `src/file_integrity_toolkit/remote/**`
- STEP2A / STEP2B tests
- real-artifact replay test
- remote specifications / architecture documents
- internal review, repair, handoff, closure, planning, and dogfooding evidence

## Public CI result

GitHub Actions workflow:

```text
tests
run #1
run id = 35995212091
```

Observed results:

```text
Python 3.9  = 65 passed
Python 3.10 = 65 passed
Python 3.11 = 65 passed
Python 3.12 = 65 passed
Python 3.13 = 65 passed

failed = 0
```

The CI installed the candidate with:

```text
python -m pip install -e ".[test]"
```

before running `pytest`.

## Verification state

```text
Candidate assembled = YES
Public snapshot CI = PASS
Independent package review = PENDING
Merge authorization = NO
```

Boundary:

```text
Public CI PASS
≠ Independent Review PASS
≠ Merge Authorization
```
