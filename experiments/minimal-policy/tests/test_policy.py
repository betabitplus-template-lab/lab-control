from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "py_lib_policy.py"
spec = importlib.util.spec_from_file_location("py_lib_policy", MODULE_PATH)
policy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = policy
spec.loader.exec_module(policy)


class PolicyTest(unittest.TestCase):
    def make_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "pyproject.toml").write_text(
            '''[project]\nname="demo"\n[project.scripts]\ndemo="demo._api.cli:main"\n[tool.py_lib_starter]\nprimary_package="demo"\npackage_names=["demo"]\n'''
        )
        for path in ["src/demo/_api", "src/demo/_internal", "tests"]:
            (root / path).mkdir(parents=True, exist_ok=True)
        (root / "src/demo/__init__.py").write_text('from demo._api import public\n__all__ = ["public"]\n')
        (root / "src/demo/_api/__init__.py").write_text("public = 1\n")
        (root / "src/demo/_api/cli.py").write_text("def main():\n    return 0\n")
        (root / "src/demo/py.typed").write_text("")
        for relative in policy.DOCS_SKELETON:
            path = root / "docs/demo" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n")
        return root

    def test_good_project(self):
        self.assertEqual(policy.check(self.make_project()), ())

    def test_script_must_use_api_cli(self):
        root = self.make_project()
        path = root / "pyproject.toml"
        path.write_text(path.read_text().replace("demo._api.cli:main", "demo._internal.cli:main"))
        self.assertTrue(any("must target" in item.message for item in policy.check(root)))

    def test_root_internal_import_is_rejected(self):
        root = self.make_project()
        (root / "src/demo/__init__.py").write_text("from demo._internal import secret\n")
        self.assertTrue(any("root __init__" in item.message for item in policy.check(root)))

    def test_version_fallback_is_allowed(self):
        root = self.make_project()
        (root / "src/demo/__init__.py").write_text(
            "from importlib.metadata import PackageNotFoundError, version\n"
            "try:\n"
            "    __version__ = version('demo')\n"
            "except PackageNotFoundError:\n"
            "    __version__ = '0.0.0+local'\n"
        )
        self.assertEqual(policy.check(root), ())

    def test_dynamic_private_import_is_rejected(self):
        root = self.make_project()
        path = root / "src/demo/_api/cli.py"
        path.write_text('import importlib\ndef main():\n    return importlib.import_module("demo._internal.secret")\n')
        self.assertTrue(any("dynamic import" in item.message for item in policy.check(root)))

    def test_example_cell_marker(self):
        root = self.make_project()
        path = root / "examples/example.py"
        path.parent.mkdir()
        path.write_text("print(1)\n")
        self.assertTrue(any("# %%" in item.message for item in policy.check(root)))

    def test_example_initializers_are_exempt(self):
        root = self.make_project()
        path = root / "examples/demo/__init__.py"
        path.parent.mkdir(parents=True)
        path.write_text("")
        self.assertEqual(policy.check(root), ())

    def test_docs_skeleton(self):
        root = self.make_project()
        (root / "docs/demo/usage.md").unlink()
        self.assertTrue(any("docs skeleton" in item.message for item in policy.check(root)))


if __name__ == "__main__":
    unittest.main()
