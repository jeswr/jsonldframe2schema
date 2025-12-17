"""
Pytest configuration and shared fixtures for jsonldframe2schema tests.

This module provides:
- Path configuration (project root in sys.path)
- Pytest markers configuration
- Shared fixtures for test suite access
- Common test utilities
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pytest
from deepdiff import DeepDiff

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Path Constants
# =============================================================================

TESTS_DIR = Path(__file__).parent
TEST_CASES_DIR = TESTS_DIR / "test_cases"
EXPECTED_SCHEMAS_DIR = TESTS_DIR / "expected_schemas"


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# =============================================================================
# Shared Utilities
# =============================================================================


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON or JSON-LD file.

    Args:
        path: Path to the JSON file

    Returns:
        Parsed JSON content, or None if file doesn't exist
    """
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_schemas(
    actual: Dict[str, Any], expected: Dict[str, Any], test_id: str = "unknown"
) -> Tuple[bool, Optional[str]]:
    """
    Compare actual and expected schemas with detailed error reporting.

    Args:
        actual: The actual generated schema
        expected: The expected schema
        test_id: Test identifier for error messages

    Returns:
        Tuple of (is_match, error_message). error_message is None if match.
    """
    diff = DeepDiff(expected, actual, ignore_order=True)

    if not diff:
        return True, None

    # Build a detailed error message
    msg_parts = [f"\n\nSchema mismatch for test '{test_id}':"]

    if "values_changed" in diff:
        msg_parts.append("\nValues changed:")
        for path, change in diff["values_changed"].items():
            msg_parts.append(
                f"  {path}: {change['old_value']} -> {change['new_value']}"
            )

    if "dictionary_item_added" in diff:
        msg_parts.append("\nExtra items in actual:")
        for item in diff["dictionary_item_added"]:
            msg_parts.append(f"  {item}")

    if "dictionary_item_removed" in diff:
        msg_parts.append("\nMissing items from actual:")
        for item in diff["dictionary_item_removed"]:
            msg_parts.append(f"  {item}")

    if "type_changes" in diff:
        msg_parts.append("\nType changes:")
        for path, change in diff["type_changes"].items():
            msg_parts.append(
                f"  {path}: {type(change['old_value']).__name__} -> {type(change['new_value']).__name__}"
            )

    msg_parts.append(f"\n\nExpected schema:\n{json.dumps(expected, indent=2)}")
    msg_parts.append(f"\nActual schema:\n{json.dumps(actual, indent=2)}")

    return False, "\n".join(msg_parts)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_cases_dir():
    """Fixture providing path to test_cases directory."""
    return TEST_CASES_DIR


@pytest.fixture
def expected_schemas_dir():
    """Fixture providing path to expected_schemas directory."""
    return EXPECTED_SCHEMAS_DIR
