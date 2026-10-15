# jsonldframe2schema

A Python library that converts JSON-LD 1.1 Frames into JSON Schema documents for validation purposes.

> ⚠️ **Warning:** This library is under active development and unstable. Additionally, it has been largely implemented by AI copilots and remains largely unreviewed by humans at this stage. Use with caution.

## 🎮 Try it Online!

**[Launch Web Playground](https://jeswr.github.io/jsonldframe2schema/playground/)** - Convert frames to schemas in real-time directly in your browser!

## Overview

This library maps [JSON-LD 1.1 Framing](https://www.w3.org/TR/json-ld11-framing/) concepts to [JSON Schema](https://json-schema.org/) validation constructs. It allows you to define the expected structure of JSON-LD documents using frames and automatically generate corresponding JSON Schema documents.

## Features

- ✅ Convert JSON-LD Frames to JSON Schema
- ✅ **Web Playground** for real-time conversion powered by WebAssembly (Pyodide)
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
        "xsd": "http://www.w3.org/2001/XMLSchema#",
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
#     "age": {
#       "type": ["integer", "string"],
#       "minimum": -9007199254740991,
#       "maximum": 9007199254740991,
#       "pattern": "^[+-]?[0-9]+(?![\\s\\S])"
#     }
#   },
#   "required": ["@type", "name", "age"],
#   "additionalProperties": true
# }
```

## Usage Examples

Context-coerced integer properties accept safe JSON integers or exact signed
ASCII digit strings. Larger values must use strings, with the datatype supplied
by the context (for example, `"@type": "xsd:integer"`).

| Context datatype | Accepted JSON integers | Accepted digit strings |
| --- | --- | --- |
| `xsd:integer` | -9007199254740991 through 9007199254740991 | Unbounded integer magnitude |
| `xsd:int` | -2147483648 through 2147483647 | The same signed 32-bit range |
| `xsd:long` | -9007199254740991 through 9007199254740991 | -9223372036854775808 through 9223372036854775807 |

This intentionally rejects previously accepted unsafe numeric values. For example,
`9007199254740992` is rejected as an `xsd:integer` number, while
`"9007199254740992"` is accepted exactly. Both numeric and string representations
outside the `xsd:int` or `xsd:long` value range are rejected. Signs, negative zero
and leading zeros are accepted string forms. Fractions, exponents, whitespace
and trailing newlines are rejected. Standard JSON Schema bounds apply to numbers;
patterns enforce string ranges without converting strings to numbers.

Callers must create strings before any lossy numeric parsing, retain the context
datatype coercion, and keep those strings exact downstream. When importing RDF
with PyLD, use `jsonld.from_rdf(dataset, {"useNativeTypes": False})` to retain
literal strings. This converter generates schemas; it does not transform input
data or recover an original value that was already rounded. These bounds apply
to inference from context for wildcard property frames (`"count": {}`). Existing
literal-default inference, even with context coercion, and explicit `@value`
object validation remain unchanged and do not enforce this precision policy.
Other numeric datatypes remain unchanged. The integer patterns require a regex
engine supporting ECMA-262 lookahead, as used by the tested Python validator and
JavaScript RegExp engine; engines such as Go's RE2-based `regexp` do not support these patterns.

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

## Command-Line Interface

The library includes a CLI tool for converting frames to schemas from the command line.

### Basic Usage

```bash
# Convert frame from file and print to stdout
python -m jsonldframe2schema frame.json

# Convert frame and save to file
python -m jsonldframe2schema frame.json schema.json

# Read from stdin and write to stdout
cat frame.json | python -m jsonldframe2schema
```

### CLI Options

```bash
python -m jsonldframe2schema --help

Options:
  -h, --help            Show help message
  --schema-version SCHEMA_VERSION
                        JSON Schema version URI (default: draft 2020-12)
  --indent INDENT       JSON indentation (default: 2)
  --compact             Output compact JSON (no indentation)
```

### CLI Examples

```bash
# Use specific JSON Schema version
python -m jsonldframe2schema frame.json --schema-version https://json-schema.org/draft-07/schema

# Output compact JSON
python -m jsonldframe2schema frame.json --compact

# Custom indentation
python -m jsonldframe2schema frame.json --indent 4
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

- **[Web Playground](https://jeswr.github.io/jsonldframe2schema/playground/)** - Interactive browser-based converter
- [Formal Specification](https://jeswr.github.io/jsonldframe2schema/spec/) - W3C-style ReSpec specification of the algorithm
- [MAPPING.md](MAPPING.md) - Formal mapping between JSON-LD Framing and JSON Schema
- [ALGORITHM.md](ALGORITHM.md) - Algorithmic definition of the conversion process

## Development

### Requirements

- Python 3.8+
- pyld >= 2.0.3 (2.x on Python before 3.10; PyLD 3.x requires Python 3.10+)
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
