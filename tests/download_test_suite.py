#!/usr/bin/env python3
"""
Download the official JSON-LD Framing test suite from W3C.

This script downloads the frame test manifest and all referenced test files
(input, frame, and expected output) to a local directory for testing.

The manifest is parsed as proper JSON-LD using pyld and rdflib to correctly
handle @context, @base, and other JSON-LD features.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from pathlib import Path

from pyld import jsonld
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS


BASE_URL = "https://w3c.github.io/json-ld-framing/tests/"
FRAME_MANIFEST_URL = BASE_URL + "frame-manifest.jsonld"
TEST_SUITE_DIR = Path(__file__).parent / "jsonld_test_suite"

# JSON-LD Test vocabulary namespace
MF = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
JLD = Namespace("https://w3c.github.io/json-ld-api/tests/vocab#")


def create_document_loader():
    """
    Create a custom document loader for pyld that can fetch remote contexts.
    """

    def loader(url, options=None):
        """Custom document loader that fetches remote documents."""
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read().decode("utf-8")
                doc = json.loads(content)
                return {"contextUrl": None, "documentUrl": url, "document": doc}
        except Exception as e:
            raise jsonld.JsonLdError(
                f"Could not load document: {url}",
                "jsonld.LoadDocumentError",
                {"url": url},
                code="loading document failed",
            )

    return loader


# Set up the document loader for pyld
jsonld.set_document_loader(create_document_loader())


def download_jsonld(url: str) -> Optional[Dict[str, Any]]:
    """
    Download and parse a JSON-LD file from URL using pyld.

    This properly handles JSON-LD features like @context and @base.
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode("utf-8")
            doc = json.loads(content)

            # Expand the JSON-LD to resolve all IRIs
            expanded = jsonld.expand(doc, {"base": url})

            return {"original": doc, "expanded": expanded}
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"Error downloading {url}: {e}")
        return None
    except jsonld.JsonLdError as e:
        print(f"Error parsing JSON-LD from {url}: {e}")
        return None


def download_file(url: str, local_path: Path) -> bool:
    """Download a file from URL to local path."""
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            with open(local_path, "wb") as f:
                f.write(content)
            return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Error downloading {url}: {e}")
        return False


def parse_manifest_with_rdflib(
    manifest_url: str, manifest_doc: Dict[str, Any]
) -> Graph:
    """
    Parse the manifest JSON-LD into an RDF graph using rdflib.

    This allows us to query the manifest using SPARQL or RDF patterns.
    """
    g = Graph()

    # Serialize the original doc to JSON-LD string and parse with rdflib
    jsonld_str = json.dumps(manifest_doc)
    g.parse(data=jsonld_str, format="json-ld", base=manifest_url)

    return g


def extract_test_info_from_expanded(
    test: Dict[str, Any], base_url: str
) -> Dict[str, Any]:
    """
    Extract relevant information from an expanded JSON-LD test entry.

    When JSON-LD is expanded, properties become full URIs and values are wrapped.
    """
    # Get @id (already a full URI after expansion)
    test_id_full = test.get("@id", "")
    # Extract just the fragment for the test ID
    test_id = test_id_full.split("#")[-1] if "#" in test_id_full else test_id_full

    # Get @type (list of full URIs)
    test_types = test.get("@type", [])

    # Determine if it's a positive or negative evaluation test
    is_positive = (
        "https://w3c.github.io/json-ld-api/tests/vocab#PositiveEvaluationTest"
        in test_types
    )
    is_negative = (
        "https://w3c.github.io/json-ld-api/tests/vocab#NegativeEvaluationTest"
        in test_types
    )

    # Helper to extract string value from expanded JSON-LD
    def get_value(key: str) -> Optional[str]:
        values = test.get(key, [])
        if values and len(values) > 0:
            val = values[0]
            if isinstance(val, dict):
                # Could be @value or @id
                return val.get("@value") or val.get("@id")
            return val
        return None

    # Helper to extract relative path from full URI
    def get_relative_path(key: str) -> Optional[str]:
        values = test.get(key, [])
        if values and len(values) > 0:
            val = values[0]
            if isinstance(val, dict):
                full_uri = val.get("@id", "")
            else:
                full_uri = val
            # Convert full URI back to relative path
            if full_uri.startswith(base_url):
                return full_uri[len(base_url) :]
            return full_uri
        return None

    # Extract name and purpose (these use the mf: namespace)
    name = get_value("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#name")
    purpose = get_value("https://w3c.github.io/json-ld-api/tests/vocab#purpose")

    # Extract file paths (these use the jld: namespace)
    input_path = get_relative_path(
        "https://w3c.github.io/json-ld-api/tests/vocab#input"
    )
    frame_path = get_relative_path(
        "https://w3c.github.io/json-ld-api/tests/vocab#frame"
    )
    expect_path = get_relative_path(
        "https://w3c.github.io/json-ld-api/tests/vocab#expect"
    )
    expect_error = get_value(
        "https://w3c.github.io/json-ld-api/tests/vocab#expectErrorCode"
    )

    # Extract options
    options = {}
    option_values = test.get("https://w3c.github.io/json-ld-api/tests/vocab#option", [])
    if option_values and len(option_values) > 0:
        opt = option_values[0]
        if isinstance(opt, dict):
            # Extract specific option values
            for key, vals in opt.items():
                if key.startswith("@"):
                    continue
                # Get the local name from the URI
                local_name = key.split("#")[-1] if "#" in key else key.split("/")[-1]
                if vals and len(vals) > 0:
                    val = vals[0]
                    if isinstance(val, dict):
                        options[local_name] = val.get("@value", val.get("@id"))
                    else:
                        options[local_name] = val

    return {
        "id": test_id,
        "name": name or "",
        "purpose": purpose or "",
        "is_positive": is_positive,
        "is_negative": is_negative,
        "input": input_path,
        "frame": frame_path,
        "expect": expect_path,
        "expectErrorCode": expect_error,
        "option": options,
    }


def extract_tests_from_expanded(
    expanded: List[Dict[str, Any]], base_url: str
) -> List[Dict[str, Any]]:
    """
    Extract test entries from the expanded JSON-LD manifest.
    """
    tests = []

    # The expanded document is a list of nodes
    for node in expanded:
        # Look for the sequence property (mf:entries or similar)
        sequence_key = (
            "http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#entries"
        )
        sequence = node.get(sequence_key, [])

        if sequence:
            # The sequence is a @list
            for item in sequence:
                if isinstance(item, dict) and "@list" in item:
                    for test_entry in item["@list"]:
                        if isinstance(test_entry, dict):
                            test_info = extract_test_info_from_expanded(
                                test_entry, base_url
                            )
                            tests.append(test_info)
                elif isinstance(item, dict):
                    test_info = extract_test_info_from_expanded(item, base_url)
                    tests.append(test_info)

    return tests


def extract_test_info(test: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant information from a test entry (fallback for non-expanded)."""
    test_id = test.get("@id", "").lstrip("#")
    test_type = test.get("@type", [])

    # Determine if it's a positive or negative evaluation test
    is_positive = "jld:PositiveEvaluationTest" in test_type
    is_negative = "jld:NegativeEvaluationTest" in test_type

    return {
        "id": test_id,
        "name": test.get("name", ""),
        "purpose": test.get("purpose", ""),
        "is_positive": is_positive,
        "is_negative": is_negative,
        "input": test.get("input"),
        "frame": test.get("frame"),
        "expect": test.get("expect"),
        "expectErrorCode": test.get("expectErrorCode"),
        "option": test.get("option", {}),
    }


def download_test_suite() -> Dict[str, Any]:
    """
    Download the complete JSON-LD framing test suite.

    Uses pyld and rdflib to properly parse the JSON-LD manifest.

    Returns:
        Dictionary containing test metadata and download status.
    """
    print(f"Downloading JSON-LD Frame test manifest from {FRAME_MANIFEST_URL}")

    # Download and parse the manifest as JSON-LD
    manifest_data = download_jsonld(FRAME_MANIFEST_URL)
    if not manifest_data:
        return {"success": False, "error": "Failed to download or parse manifest"}

    original_manifest = manifest_data["original"]
    expanded_manifest = manifest_data["expanded"]

    # Create test suite directory
    TEST_SUITE_DIR.mkdir(parents=True, exist_ok=True)

    # Save the original manifest
    manifest_path = TEST_SUITE_DIR / "frame-manifest.jsonld"
    with open(manifest_path, "w") as f:
        json.dump(original_manifest, f, indent=2)
    print(f"Saved manifest to {manifest_path}")

    # Also save the expanded form for debugging
    expanded_path = TEST_SUITE_DIR / "frame-manifest-expanded.json"
    with open(expanded_path, "w") as f:
        json.dump(expanded_manifest, f, indent=2)
    print(f"Saved expanded manifest to {expanded_path}")

    # Parse with rdflib for potential SPARQL queries
    try:
        g = parse_manifest_with_rdflib(FRAME_MANIFEST_URL, original_manifest)
        print(f"Parsed manifest into RDF graph with {len(g)} triples")
    except Exception as e:
        print(f"Warning: Could not parse manifest with rdflib: {e}")
        g = None

    # Extract tests from expanded JSON-LD
    tests = extract_tests_from_expanded(expanded_manifest, BASE_URL)

    if not tests:
        # Fallback: try to extract from original manifest if expanded didn't work
        print("Trying fallback extraction from original manifest...")
        tests = []
        for test in original_manifest.get("sequence", []):
            test_info = extract_test_info(test)
            tests.append(test_info)

    downloaded_tests: List[Dict[str, Any]] = []
    failed_downloads: List[str] = []

    print(f"\nFound {len(tests)} tests in manifest")
    print("Downloading test files...")

    for i, test_info in enumerate(tests):
        test_id = test_info["id"]

        # Download input file
        if test_info["input"]:
            input_url = BASE_URL + test_info["input"]
            input_path = TEST_SUITE_DIR / test_info["input"]
            if not download_file(input_url, input_path):
                failed_downloads.append(f"{test_id}-input")

        # Download frame file
        if test_info["frame"]:
            frame_url = BASE_URL + test_info["frame"]
            frame_path = TEST_SUITE_DIR / test_info["frame"]
            if not download_file(frame_url, frame_path):
                failed_downloads.append(f"{test_id}-frame")

        # Download expected output file
        if test_info["expect"]:
            expect_url = BASE_URL + test_info["expect"]
            expect_path = TEST_SUITE_DIR / test_info["expect"]
            if not download_file(expect_url, expect_path):
                failed_downloads.append(f"{test_id}-expect")

        downloaded_tests.append(test_info)

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Downloaded {i + 1}/{len(tests)} tests...")

    # Create a summary file
    summary = {
        "base_url": BASE_URL,
        "total_tests": len(tests),
        "downloaded_tests": len(downloaded_tests),
        "failed_downloads": failed_downloads,
        "tests": downloaded_tests,
    }

    summary_path = TEST_SUITE_DIR / "test_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved test summary to {summary_path}")

    return {
        "success": True,
        "total_tests": len(tests),
        "downloaded_tests": len(downloaded_tests),
        "failed_downloads": len(failed_downloads),
        "test_suite_dir": str(TEST_SUITE_DIR),
    }


def get_test_suite_dir() -> Path:
    """Get the path to the test suite directory."""
    return TEST_SUITE_DIR


def load_test_summary() -> Optional[Dict[str, Any]]:
    """Load the test summary if it exists."""
    summary_path = TEST_SUITE_DIR / "test_summary.json"
    if summary_path.exists():
        with open(summary_path, "r") as f:
            return json.load(f)
    return None


def is_test_suite_downloaded() -> bool:
    """Check if the test suite has already been downloaded."""
    summary_path = TEST_SUITE_DIR / "test_summary.json"
    return summary_path.exists()


def query_manifest_sparql(sparql_query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Query the downloaded manifest using SPARQL.

    This demonstrates how rdflib can be used for more complex queries.

    Example:
        # Get all positive evaluation tests
        results = query_manifest_sparql('''
            PREFIX mf: <http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#>
            PREFIX jld: <https://w3c.github.io/json-ld-api/tests/vocab#>
            SELECT ?test ?name WHERE {
                ?test a jld:PositiveEvaluationTest .
                ?test mf:name ?name .
            }
        ''')
    """
    manifest_path = TEST_SUITE_DIR / "frame-manifest.jsonld"
    if not manifest_path.exists():
        return None

    try:
        g = Graph()
        g.parse(manifest_path, format="json-ld", base=FRAME_MANIFEST_URL)
        results = g.query(sparql_query)
        return [dict(row.asdict()) for row in results]
    except Exception as e:
        print(f"SPARQL query error: {e}")
        return None


if __name__ == "__main__":
    result = download_test_suite()
    if result["success"]:
        print(f"\n✅ Successfully downloaded {result['downloaded_tests']} tests")
        print(f"   Test suite location: {result['test_suite_dir']}")
        if result["failed_downloads"] > 0:
            print(f"   ⚠️  {result['failed_downloads']} files failed to download")
    else:
        print(f"\n❌ Failed to download test suite: {result.get('error')}")
