#!/usr/bin/env python3
"""
Expected schemas module for jsonldframe2schema tests.

This module loads test cases from JSON files in the expected_schemas/ directory.
Each JSON file contains a test case with:
- id: Unique identifier for the test case
- name: Human-readable name
- description: Description of what the test case validates
- frame: The JSON-LD frame input
- expected_schema: The expected JSON Schema output
"""

import json
from pathlib import Path
from typing import Dict, Any, List


# Directory containing the JSON test case files
EXPECTED_SCHEMAS_DIR = Path(__file__).parent / "expected_schemas"


def _load_test_case(json_file: Path) -> Dict[str, Any]:
    """Load a single test case from a JSON file."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_all_test_cases() -> List[Dict[str, Any]]:
    """Load all test cases from JSON files in the expected_schemas directory."""
    test_cases = []
    if EXPECTED_SCHEMAS_DIR.exists():
        for json_file in sorted(EXPECTED_SCHEMAS_DIR.glob("*.json")):
            test_cases.append(_load_test_case(json_file))
    return test_cases


# Cache for test cases
_TEST_CASES_CACHE: List[Dict[str, Any]] = []


def get_all_test_cases() -> List[Dict[str, Any]]:
    """Return all defined test cases."""
    global _TEST_CASES_CACHE
    if not _TEST_CASES_CACHE:
        _TEST_CASES_CACHE = _load_all_test_cases()
    return _TEST_CASES_CACHE


def get_test_case_by_id(test_id: str) -> Dict[str, Any]:
    """Get a specific test case by ID."""
    for tc in get_all_test_cases():
        if tc["id"] == test_id:
            return tc
    raise KeyError(f"Test case '{test_id}' not found")


# For backward compatibility, also expose individual test case frames and schemas
# These are loaded lazily on first access
class _LazyTestCaseLoader:
    """Lazy loader for backward compatibility with direct attribute access."""

    def __init__(self):
        self._loaded = {}

    def _load_all(self):
        """Load all test cases into a dictionary keyed by id."""
        if not self._loaded:
            for tc in get_all_test_cases():
                self._loaded[tc["id"]] = tc
        return self._loaded


_lazy_loader = _LazyTestCaseLoader()


def __getattr__(name: str):
    """Support backward-compatible access to FRAME and EXPECTED_SCHEMA constants."""
    # Map old constant names to new test case IDs
    name_map = {
        "BASIC_PERSON_FRAME": ("basic_person", "frame"),
        "BASIC_PERSON_EXPECTED_SCHEMA": ("basic_person", "expected_schema"),
        "EXPLICIT_FRAME": ("explicit_frame", "frame"),
        "EXPLICIT_EXPECTED_SCHEMA": ("explicit_frame", "expected_schema"),
        "NON_EXPLICIT_FRAME": ("non_explicit_frame", "frame"),
        "NON_EXPLICIT_EXPECTED_SCHEMA": ("non_explicit_frame", "expected_schema"),
        "MULTIPLE_TYPES_FRAME": ("multiple_types", "frame"),
        "MULTIPLE_TYPES_EXPECTED_SCHEMA": ("multiple_types", "expected_schema"),
        "WILDCARD_TYPE_FRAME": ("wildcard_type", "frame"),
        "WILDCARD_TYPE_EXPECTED_SCHEMA": ("wildcard_type", "expected_schema"),
        "ID_MATCH_FRAME": ("id_match", "frame"),
        "ID_MATCH_EXPECTED_SCHEMA": ("id_match", "expected_schema"),
        "WILDCARD_ID_FRAME": ("wildcard_id", "frame"),
        "WILDCARD_ID_EXPECTED_SCHEMA": ("wildcard_id", "expected_schema"),
        "REQUIRE_ALL_FRAME": ("require_all", "frame"),
        "REQUIRE_ALL_EXPECTED_SCHEMA": ("require_all", "expected_schema"),
        "EMBED_FALSE_FRAME": ("embed_false", "frame"),
        "EMBED_FALSE_EXPECTED_SCHEMA": ("embed_false", "expected_schema"),
        "ARRAY_FRAME": ("array_frame", "frame"),
        "ARRAY_EXPECTED_SCHEMA": ("array_frame", "expected_schema"),
        "TYPED_PROPERTIES_FRAME": ("typed_properties", "frame"),
        "TYPED_PROPERTIES_EXPECTED_SCHEMA": ("typed_properties", "expected_schema"),
        "EMPTY_FRAME": ("empty_frame", "frame"),
        "EMPTY_EXPECTED_SCHEMA": ("empty_frame", "expected_schema"),
        "MATCH_NONE_TYPE_FRAME": ("match_none_type", "frame"),
        "MATCH_NONE_TYPE_EXPECTED_SCHEMA": ("match_none_type", "expected_schema"),
        "NESTED_EXPLICIT_FRAME": ("nested_explicit", "frame"),
        "NESTED_EXPLICIT_EXPECTED_SCHEMA": ("nested_explicit", "expected_schema"),
        "ID_COERCION_FRAME": ("id_coercion", "frame"),
        "ID_COERCION_EXPECTED_SCHEMA": ("id_coercion", "expected_schema"),
        "MULTIPLE_ID_FRAME": ("multiple_id", "frame"),
        "MULTIPLE_ID_EXPECTED_SCHEMA": ("multiple_id", "expected_schema"),
    }

    if name in name_map:
        test_id, field = name_map[name]
        cases = _lazy_loader._load_all()
        if test_id in cases:
            return cases[test_id][field]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
