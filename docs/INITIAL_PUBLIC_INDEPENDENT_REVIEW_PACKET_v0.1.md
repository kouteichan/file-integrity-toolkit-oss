# File Integrity Toolkit OSS
## Initial Local Core — Independent Review Packet v0.1

**Date:** 2026-09-24  
**Status:** INDEPENDENT PUBLIC PACKAGE REVIEW REQUEST / READ ONLY  
**Public Repository:** `kouteichan/file-integrity-toolkit-oss`  
**Review Branch:** `release/initial-local-core-v0.1`  
**Base main:** `7eb8d83d6d01035f42af0a196bb9e8c9c78990bc`  
**Canonical private source snapshot:** `a6b1666636326651484b9b4d37999ab97bf9edbe`  
**PR:** #2 — Draft / not merged

---

## 0. Review Purpose

Independently review the first public code promotion of File Integrity Toolkit.

The intended public boundary is deliberately narrow:

```text
File
→ local deterministic measurement
→ optional direct SHA-256 comparison
```

Remote-provider / governed retrieval architecture is intentionally excluded.

Do not edit files, merge the PR, or broaden public scope.

---

## 1. Expected Public Code Surface

Expected package files:

- `src/file_integrity_toolkit/__init__.py`
- `src/file_integrity_toolkit/core.py`

There should be **no**:

```text
src/file_integrity_toolkit/remote/
```

directory in the public candidate.

Expected public functions:

- `inspect_file`
- `calculate_sha256`
- `get_file_size`
- `compare_sha256`

The public `__init__.py` must not import or export remote-provider APIs.

---

## 2. Exact-copy Canonical Files

The following files should be byte-identical to the private canonical source
snapshot and retain these Git blob SHA-1 values:

| Path | Expected Git blob SHA-1 |
|---|---|
| `.gitignore` | `c96a4e90ce3db86f013b7eb04580dc62949e3451` |
| `src/file_integrity_toolkit/core.py` | `55111eca10e612ff7c9b6adb1c32773c8bebf018` |
| `tests/__init__.py` | `49b6dcade39d91da6ae156017470e0d927075e1c` |
| `tests/helpers.py` | `f00b7538323802aa781b941ddb0986e1e47efbd4` |
| `tests/test_compare_sha256.py` | `bd4cf39201d4913e4abf2acde5ada72527d1bb96` |
| `tests/test_inspect_file.py` | `a39581f3915e91c8003d2297eeb4f26ef23e3654` |
| `tests/test_self_test.py` | `94ab40ed0005c30cbc4bdb8c9b4d18429892536f` |

Please independently calculate / verify these identities if your environment
permits.

---

## 3. Sanitized Public Files

Review these specifically for accidental remote-architecture leakage or stale
private metadata:

- `src/file_integrity_toolkit/__init__.py`
- `tests/conftest.py`
- `pyproject.toml`
- `README.md`
- `CONTRIBUTING.md`
- `.github/workflows/tests.yml`

Expected boundaries:

### `__init__.py`

STEP1-only exports.

### `tests/conftest.py`

Only resets local Core seams. No `remote_seams` dependency.

### `pyproject.toml`

Description / keywords / URLs describe only the public Local Core.

### README / CONTRIBUTING

May explain local deterministic behavior and direct SHA-256 comparison.

Must not disclose the held governed remote pipeline, provider-independent
contract architecture, re-observation / re-binding architecture, or other
STEP2A / STEP2B implementation details.

Minimal statements that remote-provider functionality is outside the current
public release are expected.

---

## 4. Test Obligations

Please independently install / execute the public candidate.

Expected test modules:

- `tests/test_compare_sha256.py`
- `tests/test_inspect_file.py`
- `tests/test_self_test.py`

Project-side public CI observed:

```text
Python 3.9  = 65 passed
Python 3.10 = 65 passed
Python 3.11 = 65 passed
Python 3.12 = 65 passed
Python 3.13 = 65 passed
failed = 0
```

Workflow run id:

`35995212091`

Treat this as evidence only:

```text
Project-side CI PASS
≠ Independent Reviewer PASS
```

---

## 5. Functional Review Questions

Please confirm:

1. Does `inspect_file()` preserve same-read SHA-256 / size measurement?
2. Does instability fail rather than return successful partial measurement?
3. Are true zero-byte files valid?
4. Does the runtime SHA-256 KAT block measurement on failure?
5. Are `calculate_sha256()` and `get_file_size()` thin wrappers?
6. Does `compare_sha256()` distinguish MATCH / MISMATCH / ERROR?
7. Are invalid digest representations errors rather than mismatches?
8. Does public code avoid PASS / FAIL / UNKNOWN as Local Core result statuses?
9. Is public package importable without any remote package being present?
10. Do the public tests genuinely cover the Local Core rather than depending on
    hidden private modules?

---

## 6. Disclosure / Scope Review Questions

Please independently check that:

- no remote runtime implementation was promoted;
- no private development review packet / handoff / dogfooding record was
  promoted;
- no credentials, tokens, private artifact contents, or private URLs are
  present;
- public prose does not expose the held STEP2A / STEP2B governed remote
  architecture beyond saying it is outside current public scope;
- the public package can stand alone as a Local Deterministic Core.

---

## 7. Requested Verdict

Please report:

### A. Artifact / scope integrity

PASS / finding(s)

### B. Independent test result

Collected / passed / failed / skipped and environment.

### C. Functional findings

BLOCKING / MAJOR / MINOR / EDITORIAL as applicable.

### D. Public-boundary findings

Whether any held remote architecture is unintentionally disclosed.

### E. Overall verdict

One of:

- PASS — suitable to proceed to separate merge decision
- REPAIR REQUIRED
- HOLD — disclosure boundary unresolved

---

## 8. Stop Boundary

```text
Independent Review
≠ Merge Authorization
```

Do not merge, publish a release/tag, or add remote functionality.

Report and STOP.
