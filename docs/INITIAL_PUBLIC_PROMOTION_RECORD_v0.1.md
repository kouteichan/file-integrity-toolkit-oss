# Initial Public Promotion Record v0.1

**Date:** 2026-09-24  
**Status:** PUBLIC PROMOTION CANDIDATE / TEST PENDING / NOT MERGED

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

Public-specific sanitized / created artifacts:

- `src/file_integrity_toolkit/__init__.py`
- `tests/conftest.py`
- `pyproject.toml`
- `README.md`
- `CONTRIBUTING.md`
- `.github/workflows/tests.yml`
- this promotion record

## Held from the initial public release

- `src/file_integrity_toolkit/remote/**`
- STEP2A / STEP2B tests
- real-artifact replay test
- remote specifications / architecture documents
- internal review, repair, handoff, closure, planning, and dogfooding evidence

## Verification state

```text
Candidate assembled = YES
Public snapshot pytest = PENDING
Independent package review = PENDING
Merge authorization = NO
```

The private full-suite test count must not be reused as a public-package claim.
The public snapshot will establish its own collected / passed / failed / skipped
inventory.
