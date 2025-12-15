# jsonldframe2schema

A Python library that converts JSON-LD 1.1 Frames into JSON Schema documents for validation purposes.

## Overview

This library maps [JSON-LD 1.1 Framing](https://www.w3.org/TR/json-ld11-framing/) concepts to [JSON Schema](https://json-schema.org/) validation constructs. It allows you to define the expected structure of JSON-LD documents using frames and automatically generate corresponding JSON Schema documents.

## Features

- ✅ Convert JSON-LD Frames to JSON Schema
- ✅ Support for JSON-LD framing flags (`@embed`, `@explicit`, `@requireAll`, `@omitDefault`)
- ✅ Type inference from `@context` definitions
- ✅ Nested object and array handling
- ✅ Support for `@type` and `@id` constraints
- ✅ Configurable JSON Schema draft version

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### From source

```bash
git clone https://github.com/jeswr/jsonldframe2schema.git
cd jsonldframe2schema
pip install -e .
```

## Quick Start

```python
from jsonldframe2schema import frame_to_schema

# Define a JSON-LD Frame
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

# Convert to JSON Schema
schema = frame_to_schema(frame)

print(schema)
# Output:
# {
#   "$schema": "https://json-schema.org/draft/2020-12/schema",
#   "type": "object",
#   "properties": {
#     "@type": {"const": "Person"},
#     "name": {"type": "string"},
#     "age": {"type": "integer"}
#   },
#   "required": ["@type", "name", "age"],
#   "additionalProperties": true
# }
```

## Usage Examples

### Example 1: Simple Person Frame

```python
from jsonldframe2schema import frame_to_schema

frame = {
    "@type": "Person",
    "name": {},
    "email": {}
}

schema = frame_to_schema(frame)
```

### Example 2: Nested Objects

```python
frame = {
    "@type": "Person",
    "name": {},
    "address": {
        "@type": "PostalAddress",
        "streetAddress": {},
        "addressLocality": {}
    }
}

schema = frame_to_schema(frame)
```

### Example 3: Arrays

```python
frame = {
    "@type": "Person",
    "name": {},
    "knows": [{
        "@type": "Person",
        "name": {}
    }]
}

schema = frame_to_schema(frame)
```

### Example 4: Using Framing Flags

```python
# Explicit mode - only specified properties allowed
frame = {
    "@type": "Person",
    "@explicit": True,
    "name": {},
    "age": {}
}

schema = frame_to_schema(frame)
# additionalProperties will be false
```

### Example 5: Non-Embedded References

```python
frame = {
    "@type": "Article",
    "title": {},
    "author": {
        "@embed": False,
        "@type": "Person"
    }
}

schema = frame_to_schema(frame)
# author will accept either a URI string or object with @id
```

## API Reference

### `frame_to_schema(frame, schema_version)`

Convert a JSON-LD Frame to JSON Schema.

**Parameters:**
- `frame` (dict): JSON-LD Frame object
- `schema_version` (str, optional): JSON Schema version URI. Default: `"https://json-schema.org/draft/2020-12/schema"`

**Returns:**
- dict: JSON Schema document

### `FrameToSchemaConverter`

Class-based interface for frame-to-schema conversion.

```python
from jsonldframe2schema import FrameToSchemaConverter

converter = FrameToSchemaConverter(
    schema_version="https://json-schema.org/draft/2020-12/schema"
)
schema = converter.convert(frame)
```

## Formal Mapping

The library implements a formal mapping between JSON-LD Framing and JSON Schema concepts:

- **Frame Objects** → Schema Objects with `type: "object"`
- **@type Constraints** → Type validation with `const` or `enum`
- **@id Constraints** → URI format validation
- **Property Frames** → Property schemas with appropriate types
- **@embed** → Nested object vs reference schemas
- **@explicit** → `additionalProperties` control
- **@omitDefault** → Optional vs required properties
- **@requireAll** → All properties in `required` array
- **Arrays** → Array schemas with item definitions
- **Context Type Coercion** → JSON Schema type inference

For detailed mapping specifications, see [MAPPING.md](MAPPING.md).

## Algorithm

The conversion algorithm follows these steps:

1. Extract framing flags from the frame
2. Extract type information from `@context`
3. Process frame structure recursively
4. Apply framing flags to schema properties
5. Generate complete JSON Schema document

For the complete algorithmic definition, see [ALGORITHM.md](ALGORITHM.md).

## Running Examples

```bash
python examples/basic_examples.py
```

This will run several examples demonstrating different features of the library.

## Documentation

- [MAPPING.md](MAPPING.md) - Formal mapping between JSON-LD Framing and JSON Schema
- [ALGORITHM.md](ALGORITHM.md) - Algorithmic definition of the conversion process

## Development

### Requirements

- Python 3.8+
- pyld >= 2.0.3
- jsonschema >= 4.0.0

### Development Setup

```bash
pip install -r requirements-dev.txt
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Jesse Wright

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## References

- [JSON-LD 1.1 Framing Specification](https://www.w3.org/TR/json-ld11-framing/)
- [JSON Schema Specification](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
