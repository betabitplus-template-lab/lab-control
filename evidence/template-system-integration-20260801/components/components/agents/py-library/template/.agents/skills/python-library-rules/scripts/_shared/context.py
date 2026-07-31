"""Shared context and check-spec primitives for template checkers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ErrorSink = list[str]
FileCheck = Callable[["ProjectContext", Path, ErrorSink], None]
PathSelector = Callable[["ProjectContext"], list[Path]]


@dataclass(frozen=True)
class CheckSpec:
    """One reusable file-selection and file-check pairing."""

    name: str
    select_paths: PathSelector
    check_file: FileCheck


@dataclass(frozen=True)
class ProjectContext:
    """Resolved roots and shared helpers for one checker run."""

    repo_root: Path
    docs_root: Path | None = None
    src_root: Path | None = None
    tests_root: Path | None = None
    workbench_root: Path | None = None
    selected_paths: frozenset[Path] | None = None

    def read_text(self, path: Path) -> str:
        """Read a UTF-8 text file."""
        return path.read_text(encoding="utf-8")

    def display_path(self, path: Path) -> str:
        """Return a repo-relative path when possible."""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def glob_paths(
        self,
        root: Path | None,
        pattern: str,
        *,
        exclude_names: Sequence[str] = (),
        exclude_prefixes: Sequence[str] = (),
    ) -> list[Path]:
        """Return sorted file paths under one root that match a glob."""
        if root is None or not root.exists():
            return []
        return self._filter_selected(
            [
                path
                for path in sorted(root.glob(pattern))
                if path.is_file()
                and path.name not in exclude_names
                and not any(path.name.startswith(prefix) for prefix in exclude_prefixes)
            ]
        )

    def existing_paths(self, root: Path | None, *relative_paths: str) -> list[Path]:
        """Return existing files under one root."""
        if root is None or not root.exists():
            return []
        return self._filter_selected(
            [path for raw_path in relative_paths if (path := root / raw_path).exists()]
        )

    def _filter_selected(self, paths: list[Path]) -> list[Path]:
        """Limit candidate paths when one explicit selection is active."""
        if self.selected_paths is None:
            return paths
        return [path for path in paths if path in self.selected_paths]

    def doc_glob(
        self,
        pattern: str,
        *,
        exclude_names: Sequence[str] = (),
    ) -> list[Path]:
        """Return docs-root files for one glob."""
        return self.glob_paths(
            self.docs_root,
            pattern,
            exclude_names=exclude_names,
        )

    def src_glob(
        self,
        pattern: str,
        *,
        exclude_names: Sequence[str] = (),
    ) -> list[Path]:
        """Return src-root files for one glob."""
        return self.glob_paths(
            self.src_root,
            pattern,
            exclude_names=exclude_names,
        )

    def tests_glob(
        self,
        pattern: str,
        *,
        exclude_names: Sequence[str] = (),
        exclude_prefixes: Sequence[str] = (),
    ) -> list[Path]:
        """Return tests-root files for one glob."""
        return self.glob_paths(
            self.tests_root,
            pattern,
            exclude_names=exclude_names,
            exclude_prefixes=exclude_prefixes,
        )

    def workbench_glob(
        self,
        pattern: str,
        *,
        exclude_names: Sequence[str] = (),
        exclude_prefixes: Sequence[str] = (),
    ) -> list[Path]:
        """Return workbench-root files for one glob."""
        return self.glob_paths(
            self.workbench_root,
            pattern,
            exclude_names=exclude_names,
            exclude_prefixes=exclude_prefixes,
        )

    def doc_paths(self, *relative_paths: str) -> list[Path]:
        """Return existing docs-root paths."""
        return self.existing_paths(self.docs_root, *relative_paths)
