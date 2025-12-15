"""
Real-World Example: Schema.org Person and Organization

This example demonstrates converting JSON-LD Frames for Schema.org
vocabulary types into JSON Schemas.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jsonldframe2schema import frame_to_schema


def schema_org_person():
    """Schema.org Person frame to schema."""
    print("=" * 70)
    print("Schema.org Person Example")
    print("=" * 70)
    
    frame = {
        "@context": {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "@vocab": "http://schema.org/",
            "birthDate": {
                "@id": "http://schema.org/birthDate",
                "@type": "xsd:date"
            },
            "age": {
                "@id": "http://schema.org/age",
                "@type": "xsd:integer"
            }
        },
        "@type": "Person",
        "@id": {},
        "name": {},
        "email": {},
        "birthDate": {},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": {},
            "addressLocality": {},
            "addressRegion": {},
            "postalCode": {},
            "addressCountry": {}
        }
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def schema_org_organization():
    """Schema.org Organization frame to schema."""
    print("=" * 70)
    print("Schema.org Organization Example")
    print("=" * 70)
    
    frame = {
        "@context": {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "@vocab": "http://schema.org/",
            "foundingDate": {
                "@id": "http://schema.org/foundingDate",
                "@type": "xsd:date"
            }
        },
        "@type": "Organization",
        "@id": {},
        "name": {},
        "url": {},
        "logo": {},
        "foundingDate": {},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": {},
            "addressLocality": {},
            "addressCountry": {}
        },
        "member": [{
            "@type": "Person",
            "name": {},
            "jobTitle": {}
        }]
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def schema_org_article():
    """Schema.org Article with non-embedded author."""
    print("=" * 70)
    print("Schema.org Article Example (with references)")
    print("=" * 70)
    
    frame = {
        "@context": {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "@vocab": "http://schema.org/",
            "datePublished": {
                "@id": "http://schema.org/datePublished",
                "@type": "xsd:dateTime"
            },
            "wordCount": {
                "@id": "http://schema.org/wordCount",
                "@type": "xsd:integer"
            }
        },
        "@type": "Article",
        "@explicit": True,
        "@id": {},
        "headline": {},
        "alternativeHeadline": {},
        "author": {
            "@embed": False,
            "@type": "Person"
        },
        "publisher": {
            "@embed": False,
            "@type": "Organization"
        },
        "datePublished": {},
        "wordCount": {}
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


def schema_org_event():
    """Schema.org Event with complex structure."""
    print("=" * 70)
    print("Schema.org Event Example")
    print("=" * 70)
    
    frame = {
        "@context": {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "@vocab": "http://schema.org/",
            "startDate": {
                "@id": "http://schema.org/startDate",
                "@type": "xsd:dateTime"
            },
            "endDate": {
                "@id": "http://schema.org/endDate",
                "@type": "xsd:dateTime"
            }
        },
        "@type": "Event",
        "@id": {},
        "name": {},
        "description": {},
        "startDate": {},
        "endDate": {},
        "location": {
            "@type": ["Place", "VirtualLocation"],
            "name": {},
            "address": {
                "@type": "PostalAddress",
                "streetAddress": {},
                "addressLocality": {}
            }
        },
        "organizer": {
            "@type": ["Person", "Organization"],
            "name": {}
        },
        "performer": [{
            "@type": ["Person", "PerformingGroup"],
            "name": {}
        }]
    }
    
    print("\nInput Frame:")
    print(json.dumps(frame, indent=2))
    
    schema = frame_to_schema(frame)
    
    print("\nGenerated Schema:")
    print(json.dumps(schema, indent=2))
    print()


if __name__ == "__main__":
    schema_org_person()
    schema_org_organization()
    schema_org_article()
    schema_org_event()
    
    print("=" * 70)
    print("All Schema.org examples completed!")
    print("=" * 70)
