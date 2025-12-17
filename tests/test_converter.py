#!/usr/bin/env python3
"""
Test runner for jsonldframe2schema.

This module provides comprehensive tests for the JSON-LD Frame to JSON Schema converter.
Tests are organized into:
1. Unit tests for expected frame->schema mappings
2. Integration tests using the W3C JSON-LD Framing test suite frames
3. Validation tests to ensure generated schemas are valid JSON Schema

Usage:
    python -m pytest tests/test_converter.py -v
    or
    python tests/test_converter.py
"""

import sys
import unittest
from typing import Dict

from jsonldframe2schema import frame_to_schema, FrameToSchemaConverter
from tests.expected_schemas import get_all_test_cases, get_test_case_by_id
from tests.conftest import compare_schemas


class TestFrameToSchemaMapping(unittest.TestCase):
    """Tests for the frame to schema mapping using predefined expected outputs."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = FrameToSchemaConverter()

    def assert_schema_matches(self, actual: Dict, expected: Dict, test_id: str) -> None:
        """
        Assert that actual and expected schemas match.

        Args:
            actual: The actual generated schema
            expected: The expected schema
            test_id: Test identifier for error messages
        """
        is_match, error_msg = compare_schemas(actual, expected, test_id)
        if not is_match:
            self.fail(error_msg)

    def test_basic_person_frame(self):
        """Test basic person frame with nested object."""
        tc = get_test_case_by_id("basic_person")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_explicit_frame(self):
        """Test @explicit: true disallows additional properties."""
        tc = get_test_case_by_id("explicit_frame")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_non_explicit_frame(self):
        """Test default behavior allows additional properties."""
        tc = get_test_case_by_id("non_explicit_frame")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_multiple_types(self):
        """Test multiple types in @type become enum."""
        tc = get_test_case_by_id("multiple_types")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_wildcard_type(self):
        """Test empty object for @type allows any type."""
        tc = get_test_case_by_id("wildcard_type")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_id_match(self):
        """Test specific @id value becomes const."""
        tc = get_test_case_by_id("id_match")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_wildcard_id(self):
        """Test empty object for @id requires URI format."""
        tc = get_test_case_by_id("wildcard_id")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_require_all(self):
        """Test @requireAll: true makes all properties required."""
        tc = get_test_case_by_id("require_all")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_embed_false(self):
        """Test @embed: false creates ID reference schema."""
        tc = get_test_case_by_id("embed_false")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_array_frame(self):
        """Test array in frame becomes array schema."""
        tc = get_test_case_by_id("array_frame")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_typed_properties(self):
        """Test type coercion from @context maps to JSON Schema types."""
        tc = get_test_case_by_id("typed_properties")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_empty_frame(self):
        """Test empty frame produces minimal schema."""
        tc = get_test_case_by_id("empty_frame")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_match_none_type(self):
        """Test empty array for @type acts as wildcard."""
        tc = get_test_case_by_id("match_none_type")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_nested_explicit(self):
        """Test @explicit propagates to nested objects."""
        tc = get_test_case_by_id("nested_explicit")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])

    def test_id_coercion(self):
        """Test @type: @id in context maps to URI format."""
        tc = get_test_case_by_id("id_coercion")
        actual = frame_to_schema(tc["frame"])
        self.assert_schema_matches(actual, tc["expected_schema"], tc["id"])


class TestSchemaValidity(unittest.TestCase):
    """Tests to ensure generated schemas are valid JSON Schema."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = FrameToSchemaConverter()

    def test_schema_has_required_fields(self):
        """Test that all generated schemas have required fields."""
        for tc in get_all_test_cases():
            with self.subTest(test_id=tc["id"]):
                schema = frame_to_schema(tc["frame"])
                self.assertIn("$schema", schema, f"Missing $schema in {tc['id']}")
                self.assertIn("type", schema, f"Missing type in {tc['id']}")
                self.assertEqual(
                    schema["type"],
                    "object",
                    f"Root type should be object in {tc['id']}",
                )

    def test_schema_version_customization(self):
        """Test that schema version can be customized."""
        frame = {"@type": "Test"}

        # Default version
        schema1 = frame_to_schema(frame)
        self.assertEqual(
            schema1["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )

        # Custom version
        schema2 = frame_to_schema(
            frame, schema_version="https://json-schema.org/draft/2019-09/schema"
        )
        self.assertEqual(
            schema2["$schema"], "https://json-schema.org/draft/2019-09/schema"
        )

    def test_properties_are_objects(self):
        """Test that all property definitions are valid objects."""
        for tc in get_all_test_cases():
            with self.subTest(test_id=tc["id"]):
                schema = frame_to_schema(tc["frame"])
                if "properties" in schema:
                    for prop_name, prop_schema in schema["properties"].items():
                        self.assertIsInstance(
                            prop_schema,
                            dict,
                            f"Property {prop_name} schema is not an object in {tc['id']}",
                        )

    def test_required_is_list_of_strings(self):
        """Test that 'required' field is always a list of strings."""
        for tc in get_all_test_cases():
            with self.subTest(test_id=tc["id"]):
                schema = frame_to_schema(tc["frame"])
                if "required" in schema:
                    self.assertIsInstance(
                        schema["required"],
                        list,
                        f"'required' is not a list in {tc['id']}",
                    )
                    for item in schema["required"]:
                        self.assertIsInstance(
                            item, str, f"'required' contains non-string in {tc['id']}"
                        )


class TestConverterClass(unittest.TestCase):
    """Tests for the FrameToSchemaConverter class itself."""

    def test_converter_initialization(self):
        """Test converter initializes with default values."""
        converter = FrameToSchemaConverter()
        self.assertEqual(
            converter.schema_version, "https://json-schema.org/draft/2020-12/schema"
        )

    def test_converter_custom_version(self):
        """Test converter accepts custom schema version."""
        custom_version = "https://json-schema.org/draft/2019-09/schema"
        converter = FrameToSchemaConverter(schema_version=custom_version)
        self.assertEqual(converter.schema_version, custom_version)

    def test_type_mappings_exist(self):
        """Test that common XSD types are mapped."""
        converter = FrameToSchemaConverter()

        expected_types = [
            "http://www.w3.org/2001/XMLSchema#string",
            "http://www.w3.org/2001/XMLSchema#integer",
            "http://www.w3.org/2001/XMLSchema#boolean",
            "http://www.w3.org/2001/XMLSchema#double",
            "http://www.w3.org/2001/XMLSchema#dateTime",
            "http://www.w3.org/2001/XMLSchema#date",
        ]

        for xsd_type in expected_types:
            self.assertIn(
                xsd_type,
                converter.TYPE_MAPPINGS,
                f"Missing type mapping for {xsd_type}",
            )


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and unusual inputs."""

    def test_frame_with_only_context(self):
        """Test frame with only @context."""
        frame = {"@context": {"ex": "http://example.org/"}}
        schema = frame_to_schema(frame)
        self.assertEqual(schema["type"], "object")
        self.assertTrue(schema["additionalProperties"])

    def test_deeply_nested_frame(self):
        """Test deeply nested frame structure."""
        frame = {
            "@type": "A",
            "level1": {
                "@type": "B",
                "level2": {"@type": "C", "level3": {"@type": "D", "value": {}}},
            },
        }
        schema = frame_to_schema(frame)

        # Navigate through @graph wrapper to deepest level
        self.assertIn("properties", schema)
        self.assertIn("@graph", schema["properties"])
        graph_schema = schema["properties"]["@graph"]
        self.assertEqual(graph_schema["type"], "array")
        items_schema = graph_schema["items"]
        self.assertIn("properties", items_schema)
        self.assertIn("level1", items_schema["properties"])
        level1 = items_schema["properties"]["level1"]
        self.assertIn("properties", level1)
        self.assertIn("level2", level1["properties"])
        level2 = level1["properties"]["level2"]
        self.assertIn("properties", level2)
        self.assertIn("level3", level2["properties"])
        level3 = level2["properties"]["level3"]
        self.assertIn("properties", level3)
        self.assertIn("value", level3["properties"])

    def test_empty_array_property(self):
        """Test property with empty array value."""
        frame = {"@type": "Test", "items": []}
        schema = frame_to_schema(frame)
        graph_items = schema["properties"]["@graph"]["items"]
        self.assertIn("items", graph_items["properties"])
        items_schema = graph_items["properties"]["items"]
        self.assertEqual(items_schema["type"], "array")

    def test_literal_value_in_frame(self):
        """Test frame with literal values (used as defaults)."""
        frame = {"@type": "Test", "status": "active", "count": 42, "enabled": True}
        schema = frame_to_schema(frame)

        # Check that literal values create defaults (inside @graph items)
        graph_items = schema["properties"]["@graph"]["items"]
        self.assertIn("status", graph_items["properties"])
        self.assertIn("count", graph_items["properties"])
        self.assertIn("enabled", graph_items["properties"])

    def test_frame_with_null_value(self):
        """Test frame with null value."""
        frame = {"@type": "Test", "optional": None}
        schema = frame_to_schema(frame)
        # Should handle None gracefully (inside @graph items)
        graph_items = schema["properties"]["@graph"]["items"]
        self.assertIn("optional", graph_items["properties"])


class TestNewFeatures(unittest.TestCase):
    """Tests for newly implemented features like @reverse, value objects, etc."""

    def test_reverse_property(self):
        """Test @reverse property is a framing keyword and not in schema."""
        frame = {
            "@context": {"@vocab": "http://schema.org/"},
            "@type": "Person",
            "name": {},
            "@reverse": {"author": {"@type": "Book", "title": {}}},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # @reverse should NOT be in the schema properties
        # It's a framing keyword for querying, not an output property
        self.assertNotIn("@reverse", schema["properties"])

        # The frame should still generate a valid schema
        self.assertIn("@type", schema["properties"])
        self.assertIn("name", schema["properties"])

    def test_reverse_property_required(self):
        """Test that @reverse is skipped during schema generation."""
        frame = {
            "@context": {"@vocab": "http://schema.org/"},
            "@type": "Person",
            "@reverse": {"author": {"@type": "Book"}},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # @reverse should NOT be in required or properties
        self.assertNotIn("@reverse", schema.get("required", []))
        self.assertNotIn("@reverse", schema["properties"])

    def test_value_object_with_language(self):
        """Test value object frame with @language constraint."""
        frame = {
            "@context": {"@vocab": "http://schema.org/"},
            "@type": "Person",
            "name": {"@value": {}, "@language": "en"},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that name property allows string or value object
        self.assertIn("name", schema["properties"])
        name_schema = schema["properties"]["name"]
        self.assertIn("oneOf", name_schema)
        self.assertEqual(len(name_schema["oneOf"]), 2)

        # First option should be simple string
        self.assertEqual(name_schema["oneOf"][0]["type"], "string")

        # Second option should be value object with language constraint
        value_obj = name_schema["oneOf"][1]
        self.assertEqual(value_obj["type"], "object")
        self.assertIn("@value", value_obj["properties"])
        self.assertIn("@language", value_obj["properties"])
        self.assertEqual(value_obj["properties"]["@language"]["const"], "en")

    def test_value_object_with_type(self):
        """Test value object frame with @type constraint."""
        frame = {
            "@context": {"@vocab": "http://schema.org/"},
            "@type": "Article",
            "datePublished": {"@value": {}, "@type": "xsd:date"},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that datePublished allows string or typed value object
        self.assertIn("datePublished", schema["properties"])
        date_schema = schema["properties"]["datePublished"]
        self.assertIn("oneOf", date_schema)

        # Second option should have @type constraint
        value_obj = date_schema["oneOf"][1]
        self.assertIn("@type", value_obj["properties"])
        self.assertEqual(value_obj["properties"]["@type"]["const"], "xsd:date")

    def test_language_map_container(self):
        """Test @container: @language creates language map schema."""
        frame = {
            "@context": {
                "@vocab": "http://schema.org/",
                "name": {
                    "@id": "http://schema.org/name",
                    "@container": "@language",
                },
            },
            "@type": "Person",
            "name": {},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that name property allows string or language map
        self.assertIn("name", schema["properties"])
        name_schema = schema["properties"]["name"]
        self.assertIn("oneOf", name_schema)

        # Second option should be object with pattern properties
        lang_map = name_schema["oneOf"][1]
        self.assertEqual(lang_map["type"], "object")
        self.assertIn("patternProperties", lang_map)
        self.assertFalse(lang_map["additionalProperties"])

    def test_index_container(self):
        """Test @container: @index creates index map schema."""
        frame = {
            "@context": {
                "@vocab": "http://schema.org/",
                "address": {
                    "@id": "http://schema.org/address",
                    "@container": "@index",
                },
            },
            "@type": "Organization",
            "address": {},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that address property is object with additionalProperties
        self.assertIn("address", schema["properties"])
        address_schema = schema["properties"]["address"]
        self.assertEqual(address_schema["type"], "object")
        self.assertIn("additionalProperties", address_schema)

    def test_set_container(self):
        """Test @container: @set creates array with uniqueItems."""
        frame = {
            "@context": {
                "@vocab": "http://schema.org/",
                "keywords": {
                    "@id": "http://schema.org/keywords",
                    "@container": "@set",
                },
            },
            "@type": "Article",
            "keywords": {},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that keywords is array with uniqueItems
        self.assertIn("keywords", schema["properties"])
        keywords_schema = schema["properties"]["keywords"]
        self.assertEqual(keywords_schema["type"], "array")
        self.assertTrue(keywords_schema["uniqueItems"])

    def test_list_container(self):
        """Test @container: @list creates ordered array schema."""
        frame = {
            "@context": {
                "@vocab": "http://schema.org/",
                "itemListElement": {
                    "@id": "http://schema.org/itemListElement",
                    "@container": "@list",
                },
            },
            "@type": "ItemList",
            "itemListElement": {},
        }
        schema = frame_to_schema(frame, graph_only=True)

        # Check that itemListElement is array
        self.assertIn("itemListElement", schema["properties"])
        list_schema = schema["properties"]["itemListElement"]
        self.assertEqual(list_schema["type"], "array")


class TestAllPredefinedCases(unittest.TestCase):
    """Run all predefined test cases as a batch."""

    def test_all_predefined_cases(self):
        """Test all predefined frame->schema mappings."""
        test_cases = get_all_test_cases()
        failures = []

        for tc in test_cases:
            try:
                actual = frame_to_schema(tc["frame"])
                is_match, error_msg = compare_schemas(
                    actual, tc["expected_schema"], tc["id"]
                )

                if not is_match:
                    failures.append(
                        {"id": tc["id"], "name": tc["name"], "error": "Schema mismatch"}
                    )
            except Exception as e:
                failures.append({"id": tc["id"], "name": tc["name"], "error": str(e)})

        if failures:
            msg_parts = [f"\n\n{len(failures)} test case(s) failed:\n"]
            for f in failures:
                if "error" in f:
                    msg_parts.append(f"  ❌ {f['id']} ({f['name']}): {f['error']}")
                else:
                    msg_parts.append(f"  ❌ {f['id']} ({f['name']}): Schema mismatch")

            # Print passed tests
            passed = [
                tc for tc in test_cases if tc["id"] not in [f["id"] for f in failures]
            ]
            if passed:
                msg_parts.append(f"\n\n{len(passed)} test case(s) passed:")
                for tc in passed:
                    msg_parts.append(f"  ✅ {tc['id']} ({tc['name']})")

            self.fail("\n".join(msg_parts))


def run_tests_verbose():
    """Run tests with verbose output."""
    print("=" * 70)
    print("JSON-LD Frame to Schema Test Suite")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFrameToSchemaMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaValidity))
    suite.addTests(loader.loadTestsFromTestCase(TestConverterClass))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests_verbose()
    sys.exit(0 if success else 1)
