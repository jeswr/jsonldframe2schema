"""
Test runner for test_cases folder.

This module provides tests that automatically discover and run all test case
pairs in the test_cases directory. Each pair consists of:
- A .jsonld file containing the JSON-LD Frame input
- A .json file containing the expected JSON Schema output
"""

import json
from pathlib import Path
import pytest

from jsonldframe2schema import frame_to_schema
from tests.conftest import TEST_CASES_DIR, compare_schemas


def discover_test_cases():
    """Discover all test case pairs in the test_cases directory."""
    test_cases = []

    if not TEST_CASES_DIR.exists():
        return test_cases

    # Find all .jsonld files
    jsonld_files = sorted(TEST_CASES_DIR.glob("*.jsonld"))

    for jsonld_file in jsonld_files:
        # Look for matching .json file
        json_file = jsonld_file.with_suffix(".json")

        if json_file.exists():
            test_name = jsonld_file.stem
            test_cases.append((test_name, jsonld_file, json_file))

    return test_cases


# Discover test cases at module load time
TEST_CASES = discover_test_cases()


@pytest.mark.parametrize(
    "test_name,frame_file,schema_file", TEST_CASES, ids=[tc[0] for tc in TEST_CASES]
)
def test_frame_to_schema_conversion(test_name, frame_file, schema_file):
    """Test that a JSON-LD frame converts to the expected JSON Schema."""
    # Load the frame
    with open(frame_file, "r") as f:
        frame = json.load(f)

    # Load the expected schema
    with open(schema_file, "r") as f:
        expected_schema = json.load(f)

    # Convert the frame
    actual_schema = frame_to_schema(frame)

    # Compare using shared utility
    is_match, error_msg = compare_schemas(actual_schema, expected_schema, test_name)
    assert is_match, error_msg


class TestCaseDiscovery:
    """Tests for verifying test case file structure."""

    def test_test_cases_directory_exists(self):
        """Verify test_cases directory exists."""
        assert (
            TEST_CASES_DIR.exists()
        ), f"Test cases directory not found: {TEST_CASES_DIR}"

    def test_has_test_cases(self):
        """Verify we have at least some test cases."""
        assert len(TEST_CASES) > 0, "No test cases found in test_cases directory"

    def test_all_jsonld_have_json_pair(self):
        """Verify every .jsonld file has a matching .json file."""
        if not TEST_CASES_DIR.exists():
            pytest.skip("test_cases directory does not exist")

        jsonld_files = list(TEST_CASES_DIR.glob("*.jsonld"))
        missing_pairs = []

        for jsonld_file in jsonld_files:
            json_file = jsonld_file.with_suffix(".json")
            if not json_file.exists():
                missing_pairs.append(jsonld_file.name)

        assert not missing_pairs, f"Missing JSON Schema files for: {missing_pairs}"

    def test_all_json_have_jsonld_pair(self):
        """Verify every .json file has a matching .jsonld file."""
        if not TEST_CASES_DIR.exists():
            pytest.skip("test_cases directory does not exist")

        json_files = list(TEST_CASES_DIR.glob("*.json"))
        missing_pairs = []

        for json_file in json_files:
            jsonld_file = json_file.with_suffix(".jsonld")
            if not jsonld_file.exists():
                missing_pairs.append(json_file.name)

        assert not missing_pairs, f"Missing JSON-LD Frame files for: {missing_pairs}"


class TestFileValidity:
    """Tests for verifying test case files are valid JSON."""

    @pytest.mark.parametrize(
        "test_name,frame_file,schema_file", TEST_CASES, ids=[tc[0] for tc in TEST_CASES]
    )
    def test_frame_is_valid_json(self, test_name, frame_file, schema_file):
        """Verify frame file is valid JSON."""
        with open(frame_file, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {frame_file.name}: {e}")

    @pytest.mark.parametrize(
        "test_name,frame_file,schema_file", TEST_CASES, ids=[tc[0] for tc in TEST_CASES]
    )
    def test_schema_is_valid_json(self, test_name, frame_file, schema_file):
        """Verify schema file is valid JSON."""
        with open(schema_file, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {schema_file.name}: {e}")

    @pytest.mark.parametrize(
        "test_name,frame_file,schema_file", TEST_CASES, ids=[tc[0] for tc in TEST_CASES]
    )
    def test_schema_has_schema_keyword(self, test_name, frame_file, schema_file):
        """Verify expected schema has $schema keyword."""
        with open(schema_file, "r") as f:
            schema = json.load(f)

        assert (
            "$schema" in schema
        ), f"Expected schema in {schema_file.name} should have $schema keyword"


def list_test_cases():
    """Utility function to list all discovered test cases."""
    print(f"\nDiscovered {len(TEST_CASES)} test cases in {TEST_CASES_DIR}:")
    for name, frame_file, schema_file in TEST_CASES:
        print(f"  - {name}")
    return TEST_CASES


if __name__ == "__main__":
    # When run directly, list all test cases
    list_test_cases()
