from __future__ import annotations

from pathlib import Path

import pytest

import py_lib_policy as policy


PACKAGE_DOCS = (
    "README.md",
    "architecture/README.md",
    "architecture/concepts/README.md",
    "architecture/concepts/public-boundary-and-errors.md",
    "architecture/flows/README.md",
    "architecture/system.md",
    "dependencies.md",
    "usage.md",
    "verification/README.md",
    "verification/e2e/README.md",
    "verification/public-boundary-and-errors.md",
    "verification/workbench.md",
)


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_project(root: Path, *, package: str = "sample_lib", distribution: str = "sample-lib") -> None:
    _write(
        root / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                f'name = "{distribution}"',
                'version = "1.2.3"',
                "",
                "[tool.ternforge]",
                f'primary_package = "{package}"',
                f'package_names = [ "{package}" ]',
                f'env_prefix = "{package.upper()}"',
                'library_lane = "standard-lib"',
                "",
            ]
        ),
    )
    package_root = root / "src" / package
    _write(
        package_root / "__init__.py",
        "\n".join(
            [
                '"""Public package."""',
                "from __future__ import annotations",
                f"from {package}._api.config import SampleConfig",
                '__all__ = ["SampleConfig"]',
                "",
            ]
        ),
    )
    _write(package_root / "py.typed")
    _write(package_root / "_api" / "__init__.py", '"""Public declarations."""\n')
    _write(package_root / "_api" / "config.py", f"from {package}._internal import SampleConfig\n")
    _write(package_root / "_api" / "defaults.py", "DEFAULT_LEVEL = 10\n")
    _write(package_root / "_api" / "errors.py", "class SampleError(Exception):\n    pass\n")
    _write(package_root / "_api" / "types.py", "from dataclasses import dataclass\n@dataclass\nclass SampleType:\n    value: str\n")
    _write(package_root / "_internal" / "__init__.py", f"from {package}._internal.config import SampleConfig\n")
    _write(package_root / "_internal" / "config" / "__init__.py", "from .models import SampleConfig\n")
    _write(package_root / "_internal" / "config" / "assembly.py", "def build_config():\n    return None\n")
    _write(package_root / "_internal" / "config" / "models.py", "class SampleConfig:\n    pass\n")
    _write(package_root / "_internal" / "config" / "state.py", "def get_config():\n    return None\n")
    _write(package_root / "_internal" / "config" / "validation.py", "def validate():\n    return None\n")

    tests = root / "tests"
    _write(tests / "README.md", "# Tests\n")
    _write(tests / "__init__.py")
    package_tests = tests / package
    for relative in (
        "__init__.py",
        "conftest.py",
        "e2e/__init__.py",
        "e2e/public_boundary/__init__.py",
        "e2e/public_boundary/test_public_config_pipeline.py",
        "integration/__init__.py",
        "integration/test_config_lifecycle.py",
        "property_based/__init__.py",
        "property_based/internal/__init__.py",
        "property_based/public_contract/__init__.py",
        "property_based/public_contract/test_config_contract.py",
        "support/__init__.py",
        "unit/__init__.py",
        "unit/test_public_package.py",
    ):
        text = "# %%\n" if relative.endswith(".py") and "/e2e/" in f"/{relative}" and not relative.endswith("__init__.py") else ""
        _write(package_tests / relative, text)

    _write(root / "docs" / "README.md", "# Docs\n")
    for relative in PACKAGE_DOCS:
        _write(root / "docs" / package / relative, "# Doc\n")
    _write(root / "examples" / "__init__.py")
    _write(root / "examples" / package / "__init__.py")
    _write(root / "examples" / package / "demo.py", "# %%\nprint('demo')\n")
    _write(root / "workbench" / "__init__.py")
    _write(root / "workbench" / package / "__init__.py")
    _write(root / "workbench" / package / "probe.py", "# %%\nprint('probe')\n")
    _write(root / "_copier_answers.yml", "e2e_slices: []\n")


def _messages(root: Path) -> list[str]:
    return [item.message for item in policy.check(start=root)]


def test_valid_nondefault_distribution_and_package(tmp_path: Path) -> None:
    _valid_project(tmp_path, package="actual_pkg", distribution="different-name")
    assert policy.check(start=tmp_path) == ()


def test_old_tool_table_is_rejected(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    path = tmp_path / "pyproject.toml"
    path.write_text(path.read_text().replace("[tool.ternforge]", "[tool.py_lib_starter]"), encoding="utf-8")
    assert any("[tool.ternforge]" in message for message in _messages(tmp_path))


def test_missing_source_and_test_paths_are_reported(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    (tmp_path / "src/sample_lib/_api/config.py").unlink()
    (tmp_path / "tests/sample_lib/unit/__init__.py").unlink()
    messages = _messages(tmp_path)
    assert "required Ternforge package path is missing" in messages
    assert "required Ternforge test path is missing" in messages


def test_console_script_must_use_existing_api_facade_function(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    path = tmp_path / "pyproject.toml"
    path.write_text(path.read_text() + '\n[project.scripts]\nsample = "sample_lib._internal.cli:main"\n', encoding="utf-8")
    assert any("project scripts must target" in message for message in _messages(tmp_path))
    path.write_text(path.read_text().replace("sample_lib._internal.cli:main", "sample_lib._api.cli:missing"), encoding="utf-8")
    _write(tmp_path / "src/sample_lib/_api/cli.py", "def present():\n    return 0\n")
    assert any("target function is missing" in message for message in _messages(tmp_path))


def test_root_initializer_rejects_private_import(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/__init__.py", "from sample_lib._internal import SampleConfig\n")
    assert "root __init__.py may contain only declaration/facade imports" in _messages(tmp_path)


def test_root_initializer_accepts_version_fallback(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(
        tmp_path / "src/sample_lib/__init__.py",
        "\n".join(
            [
                "from importlib.metadata import PackageNotFoundError, version",
                "try:",
                '    __version__ = version("sample-lib")',
                "except PackageNotFoundError:",
                '    __version__ = "0.0.0+local"',
                "",
            ]
        ),
    )
    assert policy.check(start=tmp_path) == ()


@pytest.mark.parametrize(
    ("relative", "source", "message"),
    [
        ("_api/__init__.py", "VALUE = 1\n", "`_api/__init__.py` must stay empty"),
        ("_api/config.py", "def build():\n    pass\n", "`_api/config.py` must contain imports only"),
        ("_api/defaults.py", "def build():\n    pass\n", "`_api/defaults.py` must contain constants only"),
        ("_api/errors.py", "class Value:\n    pass\n", "`_api/errors.py` must contain public exception classes only"),
        ("_api/types.py", "def runtime():\n    pass\n", "`_api/types.py` must contain public type declarations only"),
    ],
)
def test_declaration_module_shapes(tmp_path: Path, relative: str, source: str, message: str) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib" / relative, source)
    assert any(message in item for item in _messages(tmp_path))


def test_product_api_module_must_define_facade(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/_api/product.py", "from sample_lib._internal import SampleConfig\n")
    assert "product `_api` modules must define facades, not re-export wrappers" in _messages(tmp_path)


def test_all_is_allowed_only_in_public_root(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/_internal/config/__init__.py", '__all__ = ["SampleConfig"]\n')
    assert "`__all__` must be declared only in root package" in _messages(tmp_path)


def test_private_implementation_must_use_subpackages(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/_internal/service.py", "VALUE = 1\n")
    assert "private implementation modules must live in `_internal` subpackages" in _messages(tmp_path)


def test_public_root_children_must_be_declared_or_private(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/public_module.py", "VALUE = 1\n")
    _write(tmp_path / "src/sample_lib/public_package/__init__.py")
    messages = _messages(tmp_path)
    assert "public-looking root module must live under `_api` or `_internal`" in messages
    assert "public-looking root package must be declared or moved under `_api`/`_internal`" in messages


def test_declared_public_namespace_is_allowed(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    path = tmp_path / "pyproject.toml"
    path.write_text(path.read_text().replace('library_lane = "standard-lib"', 'library_lane = "standard-lib"\npublic_namespace_packages = [ "models" ]'), encoding="utf-8")
    _write(tmp_path / "src/sample_lib/models/__init__.py")
    assert policy.check(start=tmp_path) == ()


def test_literal_dynamic_private_import_is_rejected(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/_api/product.py", 'import importlib\ndef load():\n    return importlib.import_module("sample_lib._internal.config")\n')
    assert "string-based dynamic import of `_internal` is forbidden" in _messages(tmp_path)


def test_generic_static_import_relationship_is_left_to_import_linter(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "src/sample_lib/_internal/config/state.py", "from sample_lib._api.config import SampleConfig\n")
    assert not any("must not import public" in message for message in _messages(tmp_path))


def test_examples_enforce_location_marker_and_private_string_references(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "examples/loose.py", "print('loose')\n")
    _write(tmp_path / "examples/sample_lib/demo.py", 'print("sample_lib._internal.config")\n')
    messages = _messages(tmp_path)
    assert "examples must live under `examples/<package>/`" in messages
    assert "runnable examples must start with `# %%` for IPython console use" in messages
    assert "examples must not reference private package modules" in messages


def test_e2e_and_workbench_require_cell_markers(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "tests/sample_lib/e2e/case.py", "print('case')\n")
    _write(tmp_path / "workbench/sample_lib/probe.py", "print('probe')\n")
    messages = _messages(tmp_path)
    assert "runnable e2e tests must start with `# %%` for IPython console use" in messages
    assert "runnable workbench modules must start with `# %%` for IPython console use" in messages


def test_complete_docs_skeleton_is_required(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    (tmp_path / "docs/sample_lib/architecture/concepts/README.md").unlink()
    assert "required Ternforge docs file is missing" in _messages(tmp_path)


def test_configured_e2e_slice_requires_path_and_documentation(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(
        tmp_path / "_copier_answers.yml",
        "\n".join(
            [
                "e2e_slices:",
                "  - name: custom-flow",
                "    path: tests/__PACKAGE_NAME__/e2e/custom_flow",
                "",
            ]
        ),
    )
    messages = _messages(tmp_path)
    assert "configured e2e slice directory is missing" in messages
    assert "configured e2e slice documentation is missing" in messages
    (tmp_path / "tests/sample_lib/e2e/custom_flow").mkdir(parents=True)
    _write(tmp_path / "docs/sample_lib/verification/e2e/custom-flow.md", "# Custom flow\n")
    assert policy.check(start=tmp_path) == ()


def test_malformed_e2e_slice_config_fails_closed(tmp_path: Path) -> None:
    _valid_project(tmp_path)
    _write(tmp_path / "_copier_answers.yml", "e2e_slices: invalid\n")
    assert any("e2e_slices must be a list" in message for message in _messages(tmp_path))


def test_uv_workspace_members_are_checked(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "workspace"',
                'version = "1.0.0"',
                "[tool.uv.workspace]",
                'members = [ "packages/one", "packages/two" ]',
                "",
            ]
        ),
    )
    _valid_project(tmp_path / "packages/one", package="one")
    _valid_project(tmp_path / "packages/two", package="two")
    assert policy.check(start=tmp_path) == ()
    (tmp_path / "packages/two/src/two/py.typed").unlink()
    assert "required Ternforge package path is missing" in _messages(tmp_path)
