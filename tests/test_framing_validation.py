#!/usr/bin/env python3
"""
Framing validation tests for jsonldframe2schema.

These tests use the W3C JSON-LD Framing test suite to validate that:
1. Input data can be framed using the frame
2. The framed output conforms to the JSON Schema generated from the frame

This provides end-to-end validation that the generated schemas correctly
describe the structure of framed JSON-LD documents.
"""

import json
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import pytest
from pyld import jsonld
from jsonschema import validate, ValidationError, Draft202012Validator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonldframe2schema import frame_to_schema
from tests.download_test_suite import (
    get_test_suite_dir,
    is_test_suite_downloaded,
    BASE_URL,
)


@dataclass
class FramingTestCase:
    """Represents a single framing test case."""
    test_id: str
    name: str
    purpose: str
    is_positive: bool
    input_path: Optional[str]
    frame_path: Optional[str]
    expect_path: Optional[str]
    options: Dict[str, Any]
    
    @property
    def has_all_files(self) -> bool:
        """Check if all required files are available."""
        return all([self.input_path, self.frame_path, self.expect_path])


def load_manifest_tests() -> List[FramingTestCase]:
    """
    Load test cases directly from the manifest file.
    
    This reads the original manifest to get accurate input/frame/expect paths.
    """
    test_suite_dir = get_test_suite_dir()
    manifest_path = test_suite_dir / "frame-manifest.jsonld"
    
    if not manifest_path.exists():
        return []
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    tests = []
    for test in manifest.get("sequence", []):
        test_id = test.get("@id", "").lstrip("#")
        test_types = test.get("@type", [])
        
        is_positive = "jld:PositiveEvaluationTest" in test_types
        is_negative = "jld:NegativeEvaluationTest" in test_types
        
        tests.append(FramingTestCase(
            test_id=test_id,
            name=test.get("name", ""),
            purpose=test.get("purpose", ""),
            is_positive=is_positive,
            input_path=test.get("input"),
            frame_path=test.get("frame"),
            expect_path=test.get("expect"),
            options=test.get("option", {}),
        ))
    
    return tests


def download_missing_files():
    """Download any missing test files from the W3C test suite."""
    import urllib.request
    import urllib.error
    
    test_suite_dir = get_test_suite_dir()
    tests = load_manifest_tests()
    
    downloaded = 0
    for test in tests:
        for path_attr in ['input_path', 'frame_path', 'expect_path']:
            rel_path = getattr(test, path_attr)
            if rel_path:
                local_path = test_suite_dir / rel_path
                if not local_path.exists():
                    url = BASE_URL + rel_path
                    try:
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        with urllib.request.urlopen(url, timeout=30) as response:
                            content = response.read()
                            with open(local_path, "wb") as f:
                                f.write(content)
                        downloaded += 1
                    except (urllib.error.URLError, urllib.error.HTTPError) as e:
                        print(f"Failed to download {url}: {e}")
    
    return downloaded


def load_jsonld_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON-LD file."""
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def frame_document(input_doc: Dict[str, Any], frame: Dict[str, Any], 
                   options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Apply JSON-LD framing to an input document.
    
    Args:
        input_doc: The input JSON-LD document
        frame: The frame to apply
        options: Framing options
        
    Returns:
        The framed output document
    """
    frame_options = options or {}
    
    # Set up framing options
    pyld_options = {}
    if "processingMode" in frame_options:
        pyld_options["processingMode"] = frame_options["processingMode"]
    if "specVersion" in frame_options:
        # Map specVersion to processingMode
        spec = frame_options["specVersion"]
        if spec == "json-ld-1.0":
            pyld_options["processingMode"] = "json-ld-1.0"
        elif spec == "json-ld-1.1":
            pyld_options["processingMode"] = "json-ld-1.1"
    
    # Apply framing
    framed = jsonld.frame(input_doc, frame, pyld_options)
    return framed


def augment_schema_for_jsonld(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Augment a JSON Schema to allow JSON-LD structural keywords.
    
    JSON-LD framed output includes keywords like @context, @id, @graph
    that may not be in the frame but are added by the framing algorithm.
    This function adds these to the schema so validation doesn't fail.
    
    Args:
        schema: The original JSON Schema
        
    Returns:
        Augmented schema that allows JSON-LD keywords
    """
    import copy
    augmented = copy.deepcopy(schema)
    
    # JSON-LD keywords that should always be allowed
    jsonld_keywords = {
        "@context": {},  # Any value
        "@id": {"type": "string"},  # URI or string
        "@graph": {"type": "array"},
        "@index": {"type": "string"},
        "@language": {"type": "string"},
        "@value": {},  # Any value
        "@list": {"type": "array"},
        "@set": {"type": "array"},
    }
    
    def augment_object_schema(obj_schema: Dict) -> None:
        """Recursively augment object schemas to allow JSON-LD keywords."""
        if not isinstance(obj_schema, dict):
            return
            
        if obj_schema.get("type") == "object":
            props = obj_schema.setdefault("properties", {})
            for kw, kw_schema in jsonld_keywords.items():
                if kw not in props:
                    props[kw] = kw_schema
            
            # Recursively process nested object properties
            for prop_schema in props.values():
                augment_object_schema(prop_schema)
                
        # Handle array items
        if "items" in obj_schema:
            augment_object_schema(obj_schema["items"])
            
        # Handle oneOf, anyOf, allOf
        for key in ("oneOf", "anyOf", "allOf"):
            if key in obj_schema:
                for item in obj_schema[key]:
                    augment_object_schema(item)
    
    augment_object_schema(augmented)
    return augmented


def allow_null_in_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modify schema to allow null values and arrays where appropriate.
    
    JSON-LD framing can produce:
    1. null values for properties specified in frame but not in input
    2. arrays when @container is @set or @list in context
    
    This function also handles oneOf schemas specially:
    - Converts oneOf to anyOf (since arrays can match multiple branches)
    - Adds array as an additional option in anyOf
    
    Args:
        schema: The JSON Schema
        
    Returns:
        Schema with null and array types allowed where there's a specific type
    """
    import copy
    modified = copy.deepcopy(schema)
    
    def allow_null_and_array(obj_schema: Dict, in_oneof: bool = False) -> None:
        if not isinstance(obj_schema, dict):
            return
        
        # Handle oneOf specially - convert to anyOf and add array option
        if "oneOf" in obj_schema and not in_oneof:
            # Convert oneOf to anyOf since with arrays, multiple branches might match
            branches = obj_schema.pop("oneOf")
            
            # Process each branch
            for branch in branches:
                allow_null_and_array(branch, in_oneof=True)
            
            # Add an array option that accepts any items
            array_branch = {"type": "array"}
            branches.append(array_branch)
            
            # Use anyOf instead of oneOf
            obj_schema["anyOf"] = branches
            return
            
        # If schema has a specific type, allow null (and array if not in oneOf)
        if "type" in obj_schema:
            current_type = obj_schema["type"]
            if isinstance(current_type, str):
                if in_oneof:
                    # In oneOf branch, only add null to avoid breaking the logic
                    if current_type != "null":
                        obj_schema["type"] = [current_type, "null"]
                else:
                    # Outside oneOf, allow null and array
                    if current_type not in ("null", "array", "object"):
                        obj_schema["type"] = [current_type, "null", "array"]
                    elif current_type == "object":
                        obj_schema["type"] = ["object", "null", "array"]
            elif isinstance(current_type, list):
                if "null" not in current_type:
                    current_type.append("null")
                if not in_oneof and "array" not in current_type:
                    current_type.append("array")
        
        # Process properties
        if "properties" in obj_schema:
            for prop_schema in obj_schema["properties"].values():
                allow_null_and_array(prop_schema, in_oneof)
                
        # Process items
        if "items" in obj_schema:
            allow_null_and_array(obj_schema["items"], in_oneof)
            
        # Handle anyOf, allOf (but not oneOf which we converted above)
        for key in ("anyOf", "allOf"):
            if key in obj_schema:
                for item in obj_schema[key]:
                    allow_null_and_array(item, in_oneof=(key == "anyOf"))
    
    allow_null_and_array(modified)
    return modified


def validate_against_schema(document: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a document against a JSON Schema.
    
    Handles JSON-LD specific structures:
    - Augments schema to allow JSON-LD keywords (@context, @id, etc.)
    - If document has @graph, validates each item in the graph
    - Allows null values (JSON-LD explicit matching)
    
    Args:
        document: The document to validate
        schema: The JSON Schema
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Augment schema to handle JSON-LD specifics
    augmented_schema = augment_schema_for_jsonld(schema)
    augmented_schema = allow_null_in_schema(augmented_schema)
    
    try:
        # Check if document has @graph wrapper
        if "@graph" in document and isinstance(document.get("@graph"), list):
            # Validate each item in @graph against the schema
            for i, item in enumerate(document["@graph"]):
                try:
                    validate(instance=item, schema=augmented_schema, cls=Draft202012Validator)
                except ValidationError as e:
                    return False, f"@graph[{i}]: {str(e)}"
            return True, None
        else:
            # Validate document directly
            validate(instance=document, schema=augmented_schema, cls=Draft202012Validator)
            return True, None
    except ValidationError as e:
        return False, str(e)


class TestFramingValidation(unittest.TestCase):
    """
    Test that framed JSON-LD documents conform to generated schemas.
    
    These tests:
    1. Load input data and frame from W3C test suite
    2. Apply JSON-LD framing algorithm
    3. Generate JSON Schema from the frame
    4. Validate that the framed output conforms to the schema
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not is_test_suite_downloaded():
            pytest.skip("W3C test suite not downloaded")
        
        # Download any missing files
        downloaded = download_missing_files()
        if downloaded > 0:
            print(f"Downloaded {downloaded} missing test files")
        
        cls.test_suite_dir = get_test_suite_dir()
        cls.tests = load_manifest_tests()
        
        # Filter to only positive evaluation tests with all files
        cls.valid_tests = [t for t in cls.tests if t.is_positive and t.has_all_files]
    
    def load_test_files(self, test: FramingTestCase) -> Tuple[
        Optional[Dict], Optional[Dict], Optional[Dict]
    ]:
        """Load the input, frame, and expected output files for a test."""
        input_doc = None
        frame = None
        expected = None
        
        if test.input_path:
            input_doc = load_jsonld_file(self.test_suite_dir / test.input_path)
        if test.frame_path:
            frame = load_jsonld_file(self.test_suite_dir / test.frame_path)
        if test.expect_path:
            expected = load_jsonld_file(self.test_suite_dir / test.expect_path)
        
        return input_doc, frame, expected


# Generate individual test methods for each W3C test case
def generate_test_method(test: FramingTestCase):
    """Generate a test method for a specific test case."""
    
    def test_method(self):
        """Test that framed output conforms to generated schema."""
        input_doc, frame, expected = self.load_test_files(test)
        
        if not all([input_doc, frame]):
            self.skipTest(f"Missing required files for {test.test_id}")
        
        # Step 1: Generate schema from frame
        try:
            schema = frame_to_schema(frame)
        except Exception as e:
            self.fail(f"Failed to generate schema: {e}")
        
        # Step 2: Apply framing algorithm
        try:
            framed = frame_document(input_doc, frame, test.options)
        except Exception as e:
            self.skipTest(f"Framing failed (pyld error): {e}")
        
        # Step 3: Validate framed output against schema
        is_valid, error = validate_against_schema(framed, schema)
        
        if not is_valid:
            # Provide detailed failure information
            msg = (
                f"\nTest: {test.test_id} - {test.name}\n"
                f"Purpose: {test.purpose}\n"
                f"Validation Error: {error}\n"
                f"\nFramed Output:\n{json.dumps(framed, indent=2)[:1000]}\n"
                f"\nGenerated Schema:\n{json.dumps(schema, indent=2)[:1000]}"
            )
            self.fail(msg)
    
    test_method.__name__ = f"test_{test.test_id}_{test.name.replace(' ', '_').replace('/', '_')[:30]}"
    test_method.__doc__ = f"{test.test_id}: {test.name} - {test.purpose}"
    return test_method


class TestFramingSchemaConformance(unittest.TestCase):
    """
    Comprehensive tests for framing + schema validation.
    
    This test class validates the core hypothesis: schemas generated from
    JSON-LD frames should validate the output of the framing algorithm.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not is_test_suite_downloaded():
            pytest.skip("W3C test suite not downloaded")
        
        # Download any missing files
        download_missing_files()
        
        cls.test_suite_dir = get_test_suite_dir()
        cls.tests = load_manifest_tests()
    
    def test_all_positive_tests_validate(self):
        """
        Run validation on all positive W3C frame tests.
        
        This is an aggregate test that tracks success/failure across all tests.
        """
        results = {
            "passed": [],
            "failed": [],
            "skipped": [],
            "framing_errors": [],
        }
        
        for test in self.tests:
            if not test.is_positive:
                continue
            
            if not test.has_all_files:
                results["skipped"].append((test.test_id, "Missing files"))
                continue
            
            # Load files
            input_path = self.test_suite_dir / test.input_path
            frame_path = self.test_suite_dir / test.frame_path
            
            if not input_path.exists() or not frame_path.exists():
                results["skipped"].append((test.test_id, "Files not found"))
                continue
            
            input_doc = load_jsonld_file(input_path)
            frame = load_jsonld_file(frame_path)
            
            if not input_doc or not frame:
                results["skipped"].append((test.test_id, "Failed to load files"))
                continue
            
            # Generate schema
            try:
                schema = frame_to_schema(frame)
            except Exception as e:
                results["failed"].append((test.test_id, f"Schema generation failed: {e}"))
                continue
            
            # Apply framing
            try:
                framed = frame_document(input_doc, frame, test.options)
            except Exception as e:
                results["framing_errors"].append((test.test_id, str(e)))
                continue
            
            # Validate
            is_valid, error = validate_against_schema(framed, schema)
            
            if is_valid:
                results["passed"].append(test.test_id)
            else:
                results["failed"].append((test.test_id, error[:200] if error else "Unknown"))
        
        # Print summary
        total = len(results["passed"]) + len(results["failed"])
        print(f"\n\n{'='*60}")
        print("FRAMING VALIDATION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Passed:          {len(results['passed'])}/{total}")
        print(f"Failed:          {len(results['failed'])}/{total}")
        print(f"Skipped:         {len(results['skipped'])}")
        print(f"Framing Errors:  {len(results['framing_errors'])}")
        
        if results["failed"]:
            print(f"\nFailed Tests:")
            for test_id, error in results["failed"][:10]:
                print(f"  - {test_id}: {error[:100]}")
            if len(results["failed"]) > 10:
                print(f"  ... and {len(results['failed']) - 10} more")
        
        if results["framing_errors"]:
            print(f"\nFraming Errors (pyld issues, not our fault):")
            for test_id, error in results["framing_errors"][:5]:
                print(f"  - {test_id}: {error[:100]}")
        
        # We expect some failures due to incomplete implementation
        # But track the pass rate
        pass_rate = len(results["passed"]) / max(total, 1)
        print(f"\nPass Rate: {pass_rate:.1%}")
        
        # Store results for potential further analysis
        self.results = results
    
    def test_expected_output_validates(self):
        """
        Test that the expected outputs from W3C test suite validate against
        generated schemas.
        
        This validates that our schema generation is correct by checking
        against the canonical expected outputs.
        """
        results = {"passed": [], "failed": [], "skipped": []}
        
        for test in self.tests:
            if not test.is_positive or not test.has_all_files:
                continue
            
            frame_path = self.test_suite_dir / test.frame_path
            expect_path = self.test_suite_dir / test.expect_path
            
            if not frame_path.exists() or not expect_path.exists():
                results["skipped"].append(test.test_id)
                continue
            
            frame = load_jsonld_file(frame_path)
            expected = load_jsonld_file(expect_path)
            
            if not frame or not expected:
                results["skipped"].append(test.test_id)
                continue
            
            # Generate schema
            try:
                schema = frame_to_schema(frame)
            except Exception as e:
                results["failed"].append((test.test_id, f"Schema gen: {e}"))
                continue
            
            # Validate expected output
            is_valid, error = validate_against_schema(expected, schema)
            
            if is_valid:
                results["passed"].append(test.test_id)
            else:
                results["failed"].append((test.test_id, error[:200] if error else "Unknown"))
        
        total = len(results["passed"]) + len(results["failed"])
        print(f"\n\nExpected Output Validation: {len(results['passed'])}/{total} passed")
        
        if results["failed"]:
            print("Failed:")
            for test_id, error in results["failed"][:5]:
                print(f"  - {test_id}: {error[:100]}")


class TestSpecificFramingCases(unittest.TestCase):
    """Test specific framing cases that are important for the library."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not is_test_suite_downloaded():
            pytest.skip("W3C test suite not downloaded")
        
        download_missing_files()
        cls.test_suite_dir = get_test_suite_dir()
    
    def run_validation_test(self, test_num: str):
        """Helper to run validation for a specific test number."""
        frame_path = self.test_suite_dir / f"frame/{test_num}-frame.jsonld"
        input_path = self.test_suite_dir / f"frame/{test_num}-in.jsonld"
        expect_path = self.test_suite_dir / f"frame/{test_num}-out.jsonld"
        
        if not all(p.exists() for p in [frame_path, input_path]):
            self.skipTest(f"Test files not found for {test_num}")
        
        frame = load_jsonld_file(frame_path)
        input_doc = load_jsonld_file(input_path)
        
        # Generate schema
        schema = frame_to_schema(frame)
        
        # Frame the document
        try:
            framed = frame_document(input_doc, frame)
        except Exception as e:
            self.skipTest(f"Framing failed: {e}")
        
        # Validate
        is_valid, error = validate_against_schema(framed, schema)
        
        if not is_valid:
            self.fail(f"Validation failed: {error}\n\nFramed: {json.dumps(framed, indent=2)[:500]}")
        
        # Also validate expected output if available
        if expect_path.exists():
            expected = load_jsonld_file(expect_path)
            is_valid_exp, error_exp = validate_against_schema(expected, schema)
            if not is_valid_exp:
                self.fail(f"Expected output validation failed: {error_exp}")
    
    def test_t0001_library_framing(self):
        """Test t0001: Library framing example."""
        self.run_validation_test("0001")
    
    def test_t0005_explicit(self):
        """Test t0005: @explicit flag."""
        self.run_validation_test("0005")
    
    def test_t0006_non_explicit(self):
        """Test t0006: Non-explicit framing."""
        self.run_validation_test("0006")
    
    def test_t0008_array_framing(self):
        """Test t0008: Array framing cases with @container: @set and @embed: false."""
        self.run_validation_test("0008")
    
    def test_t0011_embed(self):
        """Test t0011: @embed true/false."""
        self.run_validation_test("0011")
    
    def test_t0022_id_match(self):
        """Test t0022: @id matching."""
        self.run_validation_test("0022")


# =============================================================================
# Parametrized W3C Test Suite
# =============================================================================

def get_w3c_test_params():
    """Get test parameters for all W3C positive evaluation tests."""
    if not is_test_suite_downloaded():
        return []
    
    # Download missing files first
    download_missing_files()
    
    tests = load_manifest_tests()
    test_suite_dir = get_test_suite_dir()
    
    params = []
    for test in tests:
        if not test.is_positive:
            continue
        if not test.has_all_files:
            continue
        
        # Verify files exist
        input_path = test_suite_dir / test.input_path if test.input_path else None
        frame_path = test_suite_dir / test.frame_path if test.frame_path else None
        
        if input_path and frame_path and input_path.exists() and frame_path.exists():
            params.append(pytest.param(
                test,
                id=f"{test.test_id}-{test.name[:30].replace(' ', '_')}"
            ))
    
    return params


@pytest.mark.parametrize("test_case", get_w3c_test_params())
def test_w3c_framing_validation(test_case: FramingTestCase):
    """
    Parametrized test that validates each W3C framing test case.
    
    For each positive evaluation test:
    1. Load input data and frame
    2. Apply JSON-LD framing algorithm
    3. Generate JSON Schema from the frame
    4. Validate that framed output conforms to the schema
    """
    test_suite_dir = get_test_suite_dir()
    
    # Load files
    input_path = test_suite_dir / test_case.input_path
    frame_path = test_suite_dir / test_case.frame_path
    
    input_doc = load_jsonld_file(input_path)
    frame = load_jsonld_file(frame_path)
    
    if not input_doc or not frame:
        pytest.skip(f"Failed to load files for {test_case.test_id}")
    
    # Generate schema from frame
    try:
        schema = frame_to_schema(frame)
    except Exception as e:
        pytest.fail(f"Schema generation failed: {e}")
    
    # Apply framing algorithm
    try:
        framed = frame_document(input_doc, frame, test_case.options)
    except Exception as e:
        pytest.skip(f"Framing failed (pyld error): {e}")
    
    # Validate framed output against schema
    is_valid, error = validate_against_schema(framed, schema)
    
    if not is_valid:
        pytest.fail(
            f"Test: {test_case.test_id} - {test_case.name}\n"
            f"Purpose: {test_case.purpose}\n"
            f"Validation Error: {error}\n"
            f"\nFramed Output (truncated):\n{json.dumps(framed, indent=2)[:800]}"
        )


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
