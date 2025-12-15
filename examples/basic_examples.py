"""
Example: Basic Person Frame to Schema Conversion

This example demonstrates converting a simple JSON-LD Frame for a Person
into a JSON Schema.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jsonldframe2schema import frame_to_schema


def example_basic_person():
    """Convert a basic Person frame to schema."""
    print("=" * 70)
    print("Example 1: Basic Person Frame")
    print("=" * 70)
    
    frame = {
        "@context": {
            "name": "http://schema.org/name",
            "age": {
                "@id": "http://schema.org/age",
                "@type": "xsd:integer"
            }
        },
        "@type": "Person",
        "name": {},
        "age": {}
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def example_nested_address():
    """Convert a Person frame with nested address to schema."""
    print("=" * 70)
    print("Example 2: Person with Nested Address")
    print("=" * 70)
    
    frame = {
        "@type": "Person",
        "@explicit": True,
        "name": {},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": {},
            "addressLocality": {},
            "postalCode": {}
        }
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def example_array_properties():
    """Convert a frame with array properties to schema."""
    print("=" * 70)
    print("Example 3: Person with Array of Friends")
    print("=" * 70)
    
    frame = {
        "@type": "Person",
        "name": {},
        "knows": [{
            "@type": "Person",
            "name": {}
        }]
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def example_non_embedded_reference():
    """Convert a frame with non-embedded references to schema."""
    print("=" * 70)
    print("Example 4: Non-Embedded Reference")
    print("=" * 70)
    
    frame = {
        "@type": "Article",
        "title": {},
        "author": {
            "@embed": False,
            "@type": "Person"
        }
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def example_multiple_types():
    """Convert a frame with multiple type options to schema."""
    print("=" * 70)
    print("Example 5: Multiple Type Options")
    print("=" * 70)
    
    frame = {
        "@type": ["Person", "Organization"],
        "name": {},
        "@id": {}
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


if __name__ == "__main__":
    example_basic_person()
    example_nested_address()
    example_array_properties()
    example_non_embedded_reference()
    example_multiple_types()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
