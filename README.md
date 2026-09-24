# File Integrity Toolkit

A small deterministic Python toolkit for **local file measurement** and
**SHA-256 comparison**.

> Do not ask the model to be exact where ordinary code can be exact.

This repository is the public OSS distribution surface of File Integrity
Toolkit. Development and review are maintained separately; only material
cleared for public distribution is promoted here.

## Public scope

The initial public release contains the **Local Deterministic Core**:

- inspect a local regular file
- compute raw-content SHA-256
- measure exact bytes read
- verify same-read size stability
- handle true zero-byte files
- compare two valid SHA-256 digests deterministically
- run a SHA-256 known-answer self-test before measurement

The initial public release does **not** include remote-provider resolution,
remote retrieval, repository mutation, repair, manifest verification, CLI,
MCP, or an overall verification verdict.

## Install from source

```bash
git clone https://github.com/kouteichan/file-integrity-toolkit-oss.git
cd file-integrity-toolkit-oss
python -m pip install -e .
```

For development / tests:

```bash
python -m pip install -e ".[test]"
pytest
```

## Quick start

```python
from file_integrity_toolkit import inspect_file, compare_sha256

measured = inspect_file("artifact.bin")

if measured["status"] == "OK":
    print(measured["data"]["size_bytes"])
    print(measured["data"]["sha256"])

expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
comparison = compare_sha256(expected, expected)

assert comparison["status"] == "MATCH"
```

## Result semantics

Local measurement returns:

```text
OK
or
ERROR
```

Direct SHA-256 comparison returns:

```text
MATCH
MISMATCH
or
ERROR
```

A `MATCH` means only that two valid SHA-256 digest strings are equal after
the documented normalization. It is **not** an overall project or artifact
verification verdict.

## Core API

### `inspect_file(file_path)`

Measures a local regular file in one read pass.

On success, the result includes:

- raw-content SHA-256
- `size_bytes`
- observed size before / after the read
- stability signals checked

Required stability relation:

```text
stat_size_before == bytes_read == stat_size_after
```

### `calculate_sha256(file_path)`

Thin wrapper over `inspect_file()`.

### `get_file_size(file_path)`

Thin wrapper over `inspect_file()`.

### `compare_sha256(expected, actual)`

Validates and compares two raw-content SHA-256 strings.

Accepted normalization:

- surrounding ASCII whitespace is trimmed
- uppercase / lowercase hex is accepted
- normalized output is lowercase

Invalid SHA-256 representations return `ERROR`; they are not converted to
`MISMATCH`.

## Known boundaries

The Local Deterministic Core does not claim:

- atomic filesystem snapshot semantics
- adversarial concurrent-mutation resistance
- path authorization
- artifact authority
- trusted-reference provenance
- manifest completeness
- overall PASS / FAIL decisions

It reports deterministic local measurement and direct comparison results only.

## Repository model

```text
Private development / review
→ public-boundary review
→ audited promotion
→ this repository
```

This repository is **not** a second private-development canonical.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).
