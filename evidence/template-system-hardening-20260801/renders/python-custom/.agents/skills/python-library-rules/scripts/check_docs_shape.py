#!/usr/bin/env python3
"""Run all python-library-rules template checkers from one entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _shared.context import CheckSpec, ProjectContext
from _shared.runner import run_specs
from core.docstring_template import SPECS as DOCSTRING_TEMPLATE_SPECS
from docs.dependencies_doc_template import SPECS as DEPENDENCIES_DOC_SPECS
from docs.index_doc_template import SPECS as INDEX_DOC_SPECS
from docs.principles_doc_template import SPECS as PRINCIPLES_DOC_SPECS
from docs.system_doc_template import SPECS as SYSTEM_DOC_SPECS
from docs.usage_doc_template import SPECS as USAGE_DOC_SPECS
from docs.vertical_slice_doc_template import SPECS as VERTICAL_SLICE_DOC_SPECS
from verification.e2e_test_template import SPECS as E2E_TEST_TEMPLATE_SPECS
from verification.property_based_testing_doc_template import (
    SPECS as PROPERTY_BASED_TESTING_DOC_SPECS,
)
from verification.test_file_template import SPECS as TEST_FILE_TEMPLATE_SPECS
from verification.verification_doc_template import SPECS as VERIFICATION_DOC_SPECS
from verification.workbench_script_template import (
    SPECS as WORKBENCH_SCRIPT_TEMPLATE_SPECS,
)

ALL_SPECS: tuple[CheckSpec, ...] = (
    *INDEX_DOC_SPECS,
    *SYSTEM_DOC_SPECS,
    *VERTICAL_SLICE_DOC_SPECS,
    *PRINCIPLES_DOC_SPECS,
    *USAGE_DOC_SPECS,
    *DEPENDENCIES_DOC_SPECS,
    *PROPERTY_BASED_TESTING_DOC_SPECS,
    *VERIFICATION_DOC_SPECS,
    *DOCSTRING_TEMPLATE_SPECS,
    *TEST_FILE_TEMPLATE_SPECS,
    *E2E_TEST_TEMPLATE_SPECS,
    *WORKBENCH_SCRIPT_TEMPLATE_SPECS,
)


def _resolve_path(raw_path: str | None, base: Path) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def _is_within_root(path: Path, root: Path | None) -> bool:
    if root is None:
        return False
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_selected_paths(
    raw_paths: list[str],
    repo_root: Path,
    roots: tuple[Path | None, ...],
) -> frozenset[Path] | None:
    if not raw_paths:
        return None

    resolved_paths = [
        path
        for raw_path in raw_paths
        if (path := _resolve_path(raw_path, repo_root)) is not None
    ]
    if any(path.name == ".pre-commit-config.yaml" for path in resolved_paths):
        return None

    return frozenset(
        path
        for path in resolved_paths
        if any(_is_within_root(path, root) for root in roots)
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run python-library-rules template checks for docs, tests, src, "
            "and workbench trees."
        )
    )
    parser.add_argument(
        "docs_root",
        nargs="?",
        help="Docs root to check, kept as a positional alias for --docs-root.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repo root used for relative path resolution and error display.",
    )
    parser.add_argument(
        "--docs-root",
        dest="docs_root_flag",
        help="Docs root to check, relative to --repo-root or absolute.",
    )
    parser.add_argument(
        "--src-root",
        help="Optional src root for docstring-template checks.",
    )
    parser.add_argument(
        "--tests-root",
        help="Optional tests root for pytest and e2e template checks.",
    )
    parser.add_argument(
        "--workbench-root",
        help="Optional workbench root for live script template checks.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional explicit files to limit checks, useful for hook integration.",
    )
    if hasattr(parser, "parse_intermixed_args"):
        return parser.parse_intermixed_args(argv)
    return parser.parse_args(argv)


def _write_stdout(text: str) -> None:
    sys.stdout.write(f"{text}\n")


def _write_stderr(text: str) -> None:
    sys.stderr.write(f"{text}\n")


def main(argv: list[str] | None = None) -> int:
    """Run the aggregate template checker."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = _resolve_path(args.repo_root, Path.cwd())
    if repo_root is None:
        msg = "repo root could not be resolved"
        raise RuntimeError(msg)

    raw_docs_root = args.docs_root_flag or args.docs_root
    docs_root = _resolve_path(raw_docs_root, repo_root)
    src_root = _resolve_path(args.src_root, repo_root)
    tests_root = _resolve_path(args.tests_root, repo_root)
    workbench_root = _resolve_path(args.workbench_root, repo_root)
    selected_paths = _resolve_selected_paths(
        args.paths,
        repo_root,
        (docs_root, src_root, tests_root, workbench_root),
    )

    if all(root is None for root in (docs_root, src_root, tests_root, workbench_root)):
        _write_stderr(
            "Nothing to check. Provide at least one of docs_root/--docs-root, "
            "--src-root, --tests-root, or --workbench-root.",
        )
        return 2

    for label, root in (
        ("docs root", docs_root),
        ("src root", src_root),
        ("tests root", tests_root),
        ("workbench root", workbench_root),
    ):
        if root is not None and not root.exists():
            _write_stderr(f"{label} does not exist: {root}")
            return 2
        if root is not None and not root.is_dir():
            _write_stderr(f"{label} is not a directory: {root}")
            return 2

    if args.paths and selected_paths == frozenset():
        _write_stdout(
            "Nothing to check. None of the selected paths are under the "
            "configured docs/src/tests/workbench roots."
        )
        return 0

    context = ProjectContext(
        repo_root=repo_root,
        docs_root=docs_root,
        src_root=src_root,
        tests_root=tests_root,
        workbench_root=workbench_root,
        selected_paths=selected_paths,
    )
    errors = run_specs(context, ALL_SPECS)
    if errors:
        _write_stdout("\n".join(errors))
        return 1

    _write_stdout("Template checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
