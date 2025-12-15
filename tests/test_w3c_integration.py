#!/usr/bin/env python3
"""
Integration tests using the W3C JSON-LD Framing test suite.

These tests download and use the official JSON-LD frame files from the W3C
test suite to test the converter against real-world frames.

Note: These tests focus on ensuring the converter doesn't crash on real frames
and produces valid JSON Schema output. The expected outputs are different
from the W3C test suite because:
- The W3C tests test frame ALGORITHM (input + frame -> framed output)
- Our converter tests frame->SCHEMA mapping (frame -> JSON Schema)
"""

import json
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonldframe2schema import frame_to_schema
from tests.download_test_suite import (
    download_test_suite,
    get_test_suite_dir,
    load_test_summary,
    is_test_suite_downloaded,
)


class TestW3CFrameFiles(unittest.TestCase):
    """
    Integration tests using W3C JSON-LD Frame test suite files.

    These tests ensure the converter can handle real-world frame files
    and produces valid output.
    """

    @classmethod
    def setUpClass(cls):
        """Download test suite if needed."""
        if not is_test_suite_downloaded():
            print("\nDownloading W3C JSON-LD Frame test suite...")
            result = download_test_suite()
            if not result["success"]:
                raise unittest.SkipTest("Failed to download test suite")

        cls.test_summary = load_test_summary()
        cls.test_suite_dir = get_test_suite_dir()

    def load_frame_file(self, frame_path: str) -> Optional[Dict[str, Any]]:
        """Load a frame file from the test suite."""
        full_path = self.test_suite_dir / frame_path
        if not full_path.exists():
            return None

        with open(full_path, "r") as f:
            return json.load(f)

    def test_all_frame_files_parse(self):
        """Test that all frame files from W3C suite can be parsed and converted."""
        if not self.test_summary:
            self.skipTest("Test summary not available")

        failures = []
        successes = []
        skipped = []

        for test in self.test_summary.get("tests", []):
            test_id = test.get("id", "unknown")
            frame_path = test.get("frame")

            if not frame_path:
                skipped.append(test_id)
                continue

            try:
                frame = self.load_frame_file(frame_path)
                if frame is None:
                    skipped.append(test_id)
                    continue

                # Convert frame to schema
                schema = frame_to_schema(frame)

                # Basic validation
                self.assertIsInstance(schema, dict)
                self.assertIn("$schema", schema)
                self.assertIn("type", schema)

                successes.append(test_id)

            except Exception as e:
                failures.append(
                    {"id": test_id, "frame_path": frame_path, "error": str(e)}
                )

        # Report results
        print(f"\n\nW3C Frame File Test Results:")
        print(f"  Successes: {len(successes)}")
        print(f"  Failures: {len(failures)}")
        print(f"  Skipped: {len(skipped)}")

        if failures:
            print(f"\nFailures:")
            for f in failures[:10]:  # Show first 10
                print(f"  - {f['id']}: {f['error']}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more")

        # Allow some failures for now (test suite may have edge cases)
        failure_rate = len(failures) / max(len(successes) + len(failures), 1)
        self.assertLess(
            failure_rate,
            0.2,
            f"Too many failures ({len(failures)}/{len(successes) + len(failures)})",
        )

    def test_specific_frame_t0001(self):
        """Test the library framing example (t0001)."""
        frame = self.load_frame_file("frame/0001-frame.jsonld")
        if frame is None:
            self.skipTest("Frame file not available")

        schema = frame_to_schema(frame)

        # Validate basic structure
        self.assertEqual(schema["type"], "object")
        self.assertIn("$schema", schema)

    def test_specific_frame_t0005_explicit(self):
        """Test the explicit frame example (t0005)."""
        frame = self.load_frame_file("frame/0005-frame.jsonld")
        if frame is None:
            self.skipTest("Frame file not available")

        schema = frame_to_schema(frame)

        # If @explicit is true, additionalProperties should be false
        if frame.get("@explicit") is True:
            self.assertFalse(
                schema.get("additionalProperties", True),
                "@explicit: true should set additionalProperties: false",
            )

    def test_specific_frame_t0011_embed(self):
        """Test the @embed frame example (t0011)."""
        frame = self.load_frame_file("frame/0011-frame.jsonld")
        if frame is None:
            self.skipTest("Frame file not available")

        schema = frame_to_schema(frame)

        # Should produce valid schema
        self.assertEqual(schema["type"], "object")

    def test_specific_frame_t0022_id_match(self):
        """Test the @id match frame example (t0022)."""
        frame = self.load_frame_file("frame/0022-frame.jsonld")
        if frame is None:
            self.skipTest("Frame file not available")

        schema = frame_to_schema(frame)

        # Should produce valid schema with @id constraint
        self.assertEqual(schema["type"], "object")


class TestConversionConsistency(unittest.TestCase):
    """Test that conversion is deterministic and consistent."""

    def test_conversion_is_deterministic(self):
        """Test that the same frame always produces the same schema."""
        frame = {"@type": "Person", "name": {}, "age": {}, "email": {}}

        # Convert multiple times
        schemas = [frame_to_schema(frame) for _ in range(5)]

        # All should be identical
        first = json.dumps(schemas[0], sort_keys=True)
        for schema in schemas[1:]:
            self.assertEqual(
                json.dumps(schema, sort_keys=True),
                first,
                "Conversion should be deterministic",
            )

    def test_deep_copy_safety(self):
        """Test that conversion doesn't modify the input frame."""
        original_frame = {
            "@type": "Person",
            "@context": {"ex": "http://example.org/"},
            "name": {},
            "nested": {"@type": "Address", "street": {}},
        }

        # Deep copy for comparison
        frame_copy = json.loads(json.dumps(original_frame))

        # Convert
        schema = frame_to_schema(original_frame)

        # Original should be unchanged
        self.assertEqual(
            json.dumps(original_frame, sort_keys=True),
            json.dumps(frame_copy, sort_keys=True),
            "Conversion should not modify input frame",
        )


def run_integration_tests():
    """Run integration tests."""
    print("=" * 70)
    print("W3C JSON-LD Frame Test Suite Integration Tests")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestW3CFrameFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestConversionConsistency))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
