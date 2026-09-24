"""File Integrity Toolkit — local deterministic core.

Public initial scope:
- local regular-file inspection
- raw-content SHA-256 measurement
- exact byte-size measurement
- direct SHA-256 comparison

This public package surface does not include remote provider integration.
"""

from .core import calculate_sha256, compare_sha256, get_file_size, inspect_file

__all__ = [
    "inspect_file",
    "calculate_sha256",
    "get_file_size",
    "compare_sha256",
]
