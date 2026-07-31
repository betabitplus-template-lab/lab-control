"""Root pytest configuration for reusable test infrastructure.

Why:
    Keeps repository-wide pytest setup independent from the product package so
    this file can remain a portable backbone for future libraries.

When to use:
    Put only generic pytest hooks and fixtures here. Package-specific fixtures
    belong under the package test tree, for example `tests/<package>/`.
"""
