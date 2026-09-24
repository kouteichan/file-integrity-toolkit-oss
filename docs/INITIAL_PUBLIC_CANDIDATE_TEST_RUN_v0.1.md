# Initial Public Candidate Test Run v0.1

**Date:** 2026-09-24  
**Mode:** PUBLIC GITHUB ACTIONS / CLEAN RUNNER MATRIX  
**Repository:** `kouteichan/file-integrity-toolkit-oss`  
**Candidate branch:** `release/initial-local-core-v0.1`  
**Tested code commit:** `a6dc03c8e0bfa9a849e21596071ad1b66b4dbd3a`  
**Workflow run:** `35995212091`

## Result

| Python | Result |
|---|---|
| 3.9 | 65 passed |
| 3.10 | 65 passed |
| 3.11 | 65 passed |
| 3.12 | 65 passed |
| 3.13 | 65 passed |

```text
failed = 0
```

Each matrix job completed:

- checkout
- Python setup
- editable install with test extra
- pytest

successfully.

## Scope

The public candidate includes only:

- Local deterministic file measurement
- SHA-256 comparison
- STEP1-only tests

It does not contain `src/file_integrity_toolkit/remote/**`.

## Interpretation boundary

```text
CI PASS
≠ Proof of correctness
≠ Independent review
≠ Merge authorization
```

This record is execution evidence only.
