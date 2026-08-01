"""Supported public package entrypoint for Ternforge test helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from py_lib_testkit._api.config import (
    ProjectToolingConfig,
    get_project_tooling_config,
    get_repo_root,
)
from py_lib_testkit._api.test_support import (
    DemoConsole,
    cassette_file_path,
    compare_optional_json_bodies,
    compare_optional_multipart_single_file_content,
    configure_direct_module_process,
    configure_pytest_process,
    console,
    decode_base64_bytes,
    describe_first_difference,
    extract_boundary,
    extract_single_part_content,
    get_header_value,
    get_test_data_path,
    get_test_output_dir,
    get_test_output_path,
    get_workbench_output_dir,
    get_workbench_output_path,
    image_changed,
    is_png,
    json_semantic_body,
    method_case_insensitive,
    multipart_signature_prefix,
    multipart_single_file_content,
    normalize_inline_media_bytes,
    normalize_json_body,
    parse_data_url,
    png_pixels_digest,
    png_pixels_signature,
    require_vcr_cassette_or_record_mode,
    run_async,
    save_test_output_image,
    strip_ascii_whitespace,
    to_bytes,
)

try:
    __version__ = version("py-lib-testkit")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+local"

__all__ = [
    "DemoConsole",
    "ProjectToolingConfig",
    "__version__",
    "cassette_file_path",
    "compare_optional_json_bodies",
    "compare_optional_multipart_single_file_content",
    "configure_direct_module_process",
    "configure_pytest_process",
    "console",
    "decode_base64_bytes",
    "describe_first_difference",
    "extract_boundary",
    "extract_single_part_content",
    "get_header_value",
    "get_project_tooling_config",
    "get_repo_root",
    "get_test_data_path",
    "get_test_output_dir",
    "get_test_output_path",
    "get_workbench_output_dir",
    "get_workbench_output_path",
    "image_changed",
    "is_png",
    "json_semantic_body",
    "method_case_insensitive",
    "multipart_signature_prefix",
    "multipart_single_file_content",
    "normalize_inline_media_bytes",
    "normalize_json_body",
    "parse_data_url",
    "png_pixels_digest",
    "png_pixels_signature",
    "require_vcr_cassette_or_record_mode",
    "run_async",
    "save_test_output_image",
    "strip_ascii_whitespace",
    "to_bytes",
]
