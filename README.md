# file-integrity-toolkit-oss

Public OSS distribution surface for **File Integrity Toolkit**.

> Do not ask the model to be exact where ordinary code can be exact.

## Repository role

This repository is the **public OSS surface** of File Integrity Toolkit.

Development is maintained separately in a private canonical repository. Public
artifacts are promoted here only after review for technical readiness, public
scope, and IP / disclosure boundaries.

```text
Private Development Canonical
→ Test
→ Review
→ Public / IP Boundary Check
→ Public Readiness Check
→ Promotion
→ This Repository
```

Important:

```text
Public OSS Repository
≠
Second Development Canonical
```

The public repository should contain only material that is intentionally
approved for public distribution.

## Current status

```text
Repository = PUBLIC
License = Apache License 2.0
Public OSS initialization = IN PROGRESS
Initial core promotion = NOT YET PERFORMED
```

The repository is intentionally being initialized before the first audited code
promotion. The absence of source code here does not mean the underlying project
is only conceptual; it means the public distribution boundary is being created
separately from private development history.

## Purpose

File Integrity Toolkit is intended to provide deterministic file-integrity
operations for AI agents, automated workflows, and ordinary software.

The project direction is to move exact byte-level work out of model reasoning
and into deterministic code.

Core conceptual boundary:

```text
Measurement Fact
≠
Comparison Fact
≠
Verification Verdict
```

The toolkit should report deterministic facts without silently turning them
into broader project or governance conclusions.

## Planned initial public scope

The first audited promotion is expected to focus on generic, reusable
functionality such as:

- local file measurement
- SHA-256 calculation
- exact size measurement
- deterministic SHA-256 comparison
- read-only remote artifact resolution
- exact-byte retrieval
- canonical in-memory measurement
- regression tests
- public-safe specifications and usage documentation

Each item remains subject to public-readiness and IP-boundary review before it
is promoted here.

## Out of scope for the initial public surface

The initial public OSS surface is not intended to include:

- private research artifacts
- unpublished patent-candidate mechanisms
- LMT / POS-specific proprietary implementation details
- repository write / mutation workflows
- repair automation
- migration authority
- overall verification verdicts such as `PASS` / `FAIL`
- private credentials or internal environment configuration

Generic public interfaces may later be used by private or public systems
without requiring those systems' internal mechanisms to be published here.

## Public-boundary rule

```text
Generic reusable mechanism
→ eligible for public review

Private research / patent candidate
→ keep outside this repository until separately cleared
```

A name, concept, or external project reference is not itself the deciding
factor. The deciding question is whether the material exposes technical content
that should remain private or be reviewed before publication.

## Development direction

The long-term direction is:

```text
One deterministic core
→ Thin application facade
→ Multiple integration surfaces
```

Possible future integration surfaces include:

- Python API
- CLI
- AI tool adapter
- MCP adapter
- plugin / app integration
- HTTP / service API

These are integration candidates, not requirements for the first public
release.

## License

This repository is licensed under the **Apache License 2.0**.

See [LICENSE](LICENSE).

Only material that is approved for distribution under this repository's license
should be promoted here.

## Public contribution policy

Contribution guidance will be added before the first public release candidate.

Until then, this repository should be treated as an initializing OSS surface
rather than a second unrestricted development workspace.

## Current next step

```text
Public Repository Initialization
→ Public IP / Content Boundary Audit
→ Initial Promotion Whitelist
→ Public CI / Contribution Setup
→ First Core Snapshot Promotion
→ Public Release Candidate Audit
```
