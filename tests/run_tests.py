#!/usr/bin/env python3
"""
Main test runner script.

This script runs all tests for the jsonldframe2schema library:
1. Downloads the W3C JSON-LD Frame test suite (if not already downloaded)
2. Runs unit tests against predefined expected schemas
3. Runs integration tests against W3C test suite frames

Usage:
    python tests/run_tests.py [--download-only] [--unit-only] [--integration-only]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Run jsonldframe2schema tests")
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the W3C test suite, don't run tests"
    )
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Only run unit tests (skip integration tests)"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Only run integration tests (skip unit tests)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Download test suite
    if args.download_only or args.integration_only or not args.unit_only:
        print("=" * 70)
        print("Step 1: Checking W3C JSON-LD Frame Test Suite")
        print("=" * 70)
        
        from tests.download_test_suite import (
            download_test_suite,
            is_test_suite_downloaded
        )
        
        if is_test_suite_downloaded():
            print("Test suite already downloaded.")
        else:
            print("Downloading test suite...")
            result = download_test_suite()
            if result["success"]:
                print(f"✅ Downloaded {result['downloaded_tests']} tests")
            else:
                print(f"❌ Failed to download: {result.get('error')}")
                if not args.unit_only:
                    print("Integration tests will be skipped.")
    
    if args.download_only:
        return 0
    
    results = {"unit": None, "integration": None}
    
    # Run unit tests
    if not args.integration_only:
        print("\n" + "=" * 70)
        print("Step 2: Running Unit Tests")
        print("=" * 70)
        
        try:
            from tests.test_converter import run_tests_verbose
            results["unit"] = run_tests_verbose()
        except ImportError as e:
            print(f"❌ Failed to import unit tests: {e}")
            print("Make sure 'deepdiff' is installed: pip install deepdiff")
            results["unit"] = False
    
    # Run integration tests
    if not args.unit_only:
        print("\n" + "=" * 70)
        print("Step 3: Running Integration Tests")
        print("=" * 70)
        
        try:
            from tests.test_w3c_integration import run_integration_tests
            results["integration"] = run_integration_tests()
        except ImportError as e:
            print(f"❌ Failed to import integration tests: {e}")
            results["integration"] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("Final Summary")
    print("=" * 70)
    
    all_passed = True
    
    if results["unit"] is not None:
        status = "✅ PASSED" if results["unit"] else "❌ FAILED"
        print(f"Unit Tests: {status}")
        all_passed = all_passed and results["unit"]
    
    if results["integration"] is not None:
        status = "✅ PASSED" if results["integration"] else "❌ FAILED"
        print(f"Integration Tests: {status}")
        all_passed = all_passed and results["integration"]
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
