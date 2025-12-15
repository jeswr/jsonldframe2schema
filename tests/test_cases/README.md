# JSON-LD Frame to JSON Schema Test Cases

This directory contains manually written test cases for the JSON-LD Frame to JSON Schema converter.

## File Naming Convention

Each test case consists of two files with the same base name:
- `<test-name>.jsonld` - The JSON-LD Frame input
- `<test-name>.json` - The expected JSON Schema output

## Test Cases

| Test Case | Description |
|-----------|-------------|
| `array-frame` | Frame with array-based nested objects |
| `basic-type` | Simple frame with a single @type constraint |
| `embed-false` | Frame with @embed: false - reference only, no embedding |
| `empty-frame` | Empty frame - matches anything |
| `explicit-false` | Frame with @explicit: false - additional properties allowed |
| `explicit-true` | Frame with @explicit: true - only specified properties allowed |
| `graph-container` | Frame using @graph container for multiple nodes |
| `id-coercion` | Frame with @context that coerces property to @id |
| `language-filter` | Frame filtering by @language |
| `multi-nested` | Frame with multiple nested objects at same level |
| `multiple-types` | Frame matching multiple @type values using an array |
| `nested-explicit` | Nested frames with @explicit at different levels |
| `nested-object` | Simple nested object frame |
| `omit-default` | Frame with @omitDefault and @default values |
| `require-all` | Frame with @requireAll: true - all properties required |
| `reverse-frame` | Frame with @reverse for inverse relationships |
| `specific-id` | Frame with a specific @id value constraint |
| `typed-properties` | Frame with XSD type annotations (dateTime, integer) |
| `value-object` | Frame with @value object for literal values |
| `wildcard-id` | Frame with @id: {} - matches any IRI |
| `wildcard-type` | Frame with @type: {} - matches any type |

## Running Tests

These test cases are automatically loaded and tested by:
```bash
python -m pytest tests/test_test_cases.py -v
```

## Adding New Test Cases

To add a new test case:

1. Create a `.jsonld` file with the JSON-LD Frame input
2. Create a matching `.json` file with the expected JSON Schema output
3. Use the same base name for both files
4. The tests will automatically discover and run the new case

## Schema Version

All expected schemas use JSON Schema Draft 2020-12:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```
