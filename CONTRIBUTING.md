# Contributing

Thank you for your interest in File Integrity Toolkit.

## Current public scope

The current public OSS scope is intentionally small:

- local regular-file inspection
- SHA-256 measurement
- exact byte-size measurement
- direct SHA-256 comparison
- deterministic tests for those operations

Please keep pull requests within the public scope unless an issue or maintainer
discussion explicitly expands it first.

Remote-provider resolution / retrieval, repository mutation, repair, manifest
verification, and overall verification verdicts are not part of the current
public release surface.

## Before opening a pull request

1. Keep the change focused.
2. Add or update tests when behavior changes.
3. Run:

   ```bash
   python -m pip install -e ".[test]"
   pytest
   ```

4. Do not add credentials, private URLs, private artifacts, or generated secret
   material.
5. Do not turn `MATCH` into an overall PASS / FAIL conclusion.

## Bug reports

Useful bug reports include:

- Python version
- operating system
- minimal reproduction
- expected result
- actual result
- relevant error code / structured result

## Security-sensitive reports

Please avoid publishing credentials or private artifact contents in a public
issue. A dedicated security-reporting path may be added in a later repository
hardening step.
