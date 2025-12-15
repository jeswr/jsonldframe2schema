"""
Advanced Example: Schema Validation

This example demonstrates using the generated JSON Schema to validate
JSON-LD documents that have been framed.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jsonldframe2schema import frame_to_schema
from jsonschema import validate, ValidationError


def validate_person_document():
    """Example: Validate a person document against generated schema."""
    print("=" * 70)
    print("Validation Example: Person Document")
    print("=" * 70)
    
    # Define frame
    frame = {
        "@context": {
            "name": "http://schema.org/name",
            "email": "http://schema.org/email",
            "age": {
                "@id": "http://schema.org/age",
                "@type": "xsd:integer"
            }
        },
        "@type": "Person",
        "name": {},
        "email": {},
        "age": {}
    }
    
    # Generate schema
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    
    # Valid document
    valid_doc = {
        "@type": "Person",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age": 30
    }
    
    print("\n--- Validating Valid Document ---")
    print(json.dumps(valid_doc, indent=2))
    
    try:
        validate(instance=valid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    # Invalid document - missing required field
    invalid_doc_1 = {
        "@type": "Person",
        "name": "Bob Jones"
        # Missing email and age
    }
    
    print("\n--- Validating Invalid Document (missing fields) ---")
    print(json.dumps(invalid_doc_1, indent=2))
    
    try:
        validate(instance=invalid_doc_1, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    # Invalid document - wrong type for age
    invalid_doc_2 = {
        "@type": "Person",
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "age": "thirty"  # Should be integer
    }
    
    print("\n--- Validating Invalid Document (wrong type) ---")
    print(json.dumps(invalid_doc_2, indent=2))
    
    try:
        validate(instance=invalid_doc_2, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    print()


def validate_explicit_frame():
    """Example: Validate with explicit flag."""
    print("=" * 70)
    print("Validation Example: Explicit Frame")
    print("=" * 70)
    
    # Frame with @explicit: true
    frame = {
        "@type": "Product",
        "@explicit": True,
        "name": {},
        "price": {}
    }
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema (with @explicit: true):")
    print(json.dumps(schema, indent=2))
    
    # Valid document - only specified properties
    valid_doc = {
        "@type": "Product",
        "name": "Laptop",
        "price": 999.99
    }
    
    print("\n--- Validating Valid Document ---")
    print(json.dumps(valid_doc, indent=2))
    
    try:
        validate(instance=valid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    # Invalid document - additional property
    invalid_doc = {
        "@type": "Product",
        "name": "Laptop",
        "price": 999.99,
        "description": "A great laptop"  # Not in frame, @explicit is true
    }
    
    print("\n--- Validating Invalid Document (extra property) ---")
    print(json.dumps(invalid_doc, indent=2))
    
    try:
        validate(instance=invalid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    print()


def validate_nested_objects():
    """Example: Validate nested objects."""
    print("=" * 70)
    print("Validation Example: Nested Objects")
    print("=" * 70)
    
    frame = {
        "@type": "Person",
        "name": {},
        "worksFor": {
            "@type": "Organization",
            "name": {},
            "url": {}
        }
    }
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    
    # Valid nested document
    valid_doc = {
        "@type": "Person",
        "name": "Diana Prince",
        "worksFor": {
            "@type": "Organization",
            "name": "Justice League",
            "url": "https://justiceleague.example.com"
        }
    }
    
    print("\n--- Validating Valid Nested Document ---")
    print(json.dumps(valid_doc, indent=2))
    
    try:
        validate(instance=valid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    # Invalid - missing nested property
    invalid_doc = {
        "@type": "Person",
        "name": "Eve Adams",
        "worksFor": {
            "@type": "Organization",
            "name": "Acme Corp"
            # Missing url
        }
    }
    
    print("\n--- Validating Invalid Document (missing nested property) ---")
    print(json.dumps(invalid_doc, indent=2))
    
    try:
        validate(instance=invalid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    print()


def validate_arrays():
    """Example: Validate array properties."""
    print("=" * 70)
    print("Validation Example: Array Properties")
    print("=" * 70)
    
    frame = {
        "@type": "Person",
        "name": {},
        "knows": [{
            "@type": "Person",
            "name": {}
        }]
    }
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    
    # Valid document with array
    valid_doc = {
        "@type": "Person",
        "name": "Frank Miller",
        "knows": [
            {"@type": "Person", "name": "Grace Hopper"},
            {"@type": "Person", "name": "Henry Ford"}
        ]
    }
    
    print("\n--- Validating Valid Document with Array ---")
    print(json.dumps(valid_doc, indent=2))
    
    try:
        validate(instance=valid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    # Invalid - array item missing property
    invalid_doc = {
        "@type": "Person",
        "name": "Isabel Jones",
        "knows": [
            {"@type": "Person", "name": "Jack Ryan"},
            {"@type": "Person"}  # Missing name
        ]
    }
    
    print("\n--- Validating Invalid Document (array item missing property) ---")
    print(json.dumps(invalid_doc, indent=2))
    
    try:
        validate(instance=invalid_doc, schema=schema)
        print("✓ Validation passed!")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.message}")
    
    print()


if __name__ == "__main__":
    validate_person_document()
    validate_explicit_frame()
    validate_nested_objects()
    validate_arrays()
    
    print("=" * 70)
    print("All validation examples completed!")
    print("=" * 70)
