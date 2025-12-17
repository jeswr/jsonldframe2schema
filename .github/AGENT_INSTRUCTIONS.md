# Agent Instructions for jsonldframe2schema

This document provides comprehensive instructions for AI agents working on this codebase, including detailed overviews of the JSON-LD Framing and JSON Schema specifications.

## Project Overview

**jsonldframe2schema** is a Python library that converts JSON-LD 1.1 Frames into JSON Schema documents for validation purposes. The goal is to enable developers to define expected JSON-LD document structures using frames and automatically generate corresponding JSON Schema validators.

### Current Limitations

The codebase currently does not fully handle JSON-LD framing semantics. Key areas needing improvement include:

1. **`@reverse` properties** - Not fully implemented
2. **`@graph` containers** - Partial support
3. **Language maps** (`@language`) - Not properly handled
4. **Value objects** (`@value`) - Incomplete support
5. **Index containers** (`@index`) - Not implemented
6. **Nested contexts** - Limited support
7. **`@default` values** - Incomplete handling
8. **`@embed` values** (`@always`, `@once`, `@link`) - Partial support

---

## Part 1: JSON-LD 1.1 Framing Specification Overview

**Specification URL**: https://www.w3.org/TR/json-ld11-framing/

### 1.1 What is JSON-LD Framing?

JSON-LD Framing is an algorithm that takes:
- **Input**: A JSON-LD document (or expanded JSON-LD)
- **Frame**: A template describing the desired shape of the output

And produces:
- **Output**: A JSON-LD document reshaped according to the frame's structure

The frame acts as a "query" or "view" that selects and structures data from the input document.

### 1.2 Core Framing Concepts

#### 1.2.1 Frame Structure

A frame is a JSON-LD document that describes the expected structure of output. Frames can contain:

```json
{
  "@context": { ... },     // Context definitions (optional)
  "@type": "Person",       // Type constraint (matches nodes of this type)
  "@id": "...",            // ID constraint (matches specific node)
  "propertyName": {},      // Property expectations (empty = include if present)
  "nested": {              // Nested frame for embedded objects
    "@type": "Address"
  }
}
```

#### 1.2.2 Matching Frames (Section 3.3)

A frame matches a node if:

1. **Type matching**: If frame has `@type`:
   - String value: node must have that type
   - Array: node must have at least one of the types
   - Empty object `{}`: node must have some type (wildcard)
   - Empty array `[]`: matches nodes without explicit type
   - `@default`: any node matches

2. **ID matching**: If frame has `@id`:
   - String value: node must have that exact ID
   - Array: node must have one of those IDs
   - Empty object `{}`: node must have an ID (wildcard)

3. **Property matching**: Frame properties filter which nodes match
   - By default (`@requireAll: false`), node must match at least one property
   - With `@requireAll: true`, node must match all properties

### 1.3 Framing Flags (Section 3.4)

#### 1.3.1 `@embed` Flag

Controls how referenced objects are represented:

| Value | Behavior |
|-------|----------|
| `@always` | Always embed object (default for JSON-LD 1.0) |
| `@once` | Embed first occurrence, reference thereafter (JSON-LD 1.1 default) |
| `@never` | Never embed, always use node reference |
| `true` | Same as `@once` |
| `false` | Same as `@never` |
| `@link` | Use node reference (shows only `@id`) |

**Schema implications**:
- `@embed: true/@once/@always` → Full object schema
- `@embed: false/@never` → Schema allowing URI string OR `{"@id": "..."}` reference

#### 1.3.2 `@explicit` Flag

Controls whether properties not in the frame appear in output:

| Value | Behavior | Schema Mapping |
|-------|----------|----------------|
| `true` | Only frame properties in output | `"additionalProperties": false` |
| `false` (default) | All properties included | `"additionalProperties": true` |

#### 1.3.3 `@requireAll` Flag

Controls matching strictness:

| Value | Behavior | Schema Mapping |
|-------|----------|----------------|
| `true` | All frame properties must exist | All properties in `required` |
| `false` (default) | At least one must exist | Context-dependent required |

#### 1.3.4 `@omitDefault` Flag

Controls null value handling:

| Value | Behavior | Schema Mapping |
|-------|----------|----------------|
| `true` | Omit properties with null/default | Properties not required |
| `false` (default) | Include with null value | May include `"null"` in type |

#### 1.3.5 `@default` Value

Provides default values for missing properties:

```json
{
  "@type": "Person",
  "name": { "@default": "Unknown" }
}
```

**Schema mapping**: Use `"default"` keyword in JSON Schema.

### 1.4 Special Frame Properties

#### 1.4.1 `@graph` Container

Frames a specific graph or the default graph:

```json
{
  "@graph": [{
    "@type": "Person",
    "name": {}
  }]
}
```

**Schema implications**: The root schema should have a `@graph` property with array items.

#### 1.4.2 `@reverse` Properties

Frame reverse relationships:

```json
{
  "@type": "Person",
  "@reverse": {
    "author": {
      "@type": "Book"
    }
  }
}
```

This matches a Person who is the `author` of Books (inverse relationship).

**Schema mapping**: `@reverse` becomes a property containing an object schema.

#### 1.4.3 `@included` (JSON-LD 1.1)

Includes related nodes that aren't directly embedded:

```json
{
  "@type": "Person",
  "@included": [{
    "@type": "Organization"
  }]
}
```

#### 1.4.4 `@nest` Properties

Groups properties under a synthetic object:

```json
{
  "@context": {
    "name": "http://schema.org/name",
    "address": {
      "@id": "http://schema.org/address",
      "@nest": "contactInfo"
    }
  }
}
```

### 1.5 Value Objects and Language Maps

#### 1.5.1 Value Objects

JSON-LD uses value objects to express typed/language-tagged literals:

```json
{
  "title": {
    "@value": "The Title",
    "@language": "en"
  }
}
```

Frame matching for value objects:

```json
{
  "title": {
    "@value": {},           // Match any value
    "@language": "en"       // But only English
  }
}
```

**Schema implications**:
- Value object → Schema for object with `@value`, optional `@type`/`@language`
- Language filtering → Add `@language` property with `const` or `enum`

#### 1.5.2 Language Maps

```json
{
  "@context": {
    "name": {
      "@id": "http://schema.org/name",
      "@container": "@language"
    }
  },
  "name": {
    "en": "John",
    "de": "Johann"
  }
}
```

**Schema implications**: `patternProperties` with language codes as keys.

### 1.6 Container Types

JSON-LD supports various container types that affect framing:

| Container | Description | Schema Pattern |
|-----------|-------------|----------------|
| `@list` | Ordered list | `"type": "array"` |
| `@set` | Unordered set | `"type": "array", "uniqueItems": true` |
| `@index` | Index map | `"type": "object", "additionalProperties": {...}` |
| `@language` | Language map | `"type": "object", "patternProperties": {...}` |
| `@graph` | Graph container | Nested graph structure |
| `@id` | ID map | `"type": "object", "additionalProperties": {...}` |
| `@type` | Type map | `"type": "object"` with type-based values |

---

## Part 2: JSON Schema Specification Overview

**Specification URL**: https://json-schema.org/specification.html

### 2.1 JSON Schema Basics

JSON Schema is a vocabulary for annotating and validating JSON documents.

#### 2.1.1 Schema Structure

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schema.json",
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "integer" }
  },
  "required": ["name"]
}
```

### 2.2 Type Keywords

#### 2.2.1 Primitive Types

| Type | Description | JSON-LD Mapping |
|------|-------------|-----------------|
| `string` | Text values | `xsd:string`, plain literals |
| `number` | Any numeric | `xsd:float`, `xsd:double`, `xsd:decimal` |
| `integer` | Whole numbers | `xsd:integer`, `xsd:int`, `xsd:long` |
| `boolean` | true/false | `xsd:boolean` |
| `null` | null value | Null/missing values |
| `array` | Ordered list | `@list`, `@set`, multi-values |
| `object` | Key-value pairs | Nested nodes, blank nodes |

#### 2.2.2 Multiple Types

```json
{
  "type": ["string", "null"]
}
```

### 2.3 Validation Keywords

#### 2.3.1 String Validation

```json
{
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "pattern": "^[A-Z]",
  "format": "uri"          // For @type: @id
}
```

**Formats relevant to JSON-LD**:
- `uri` - For `@id` values
- `uri-reference` - For relative IRIs
- `date-time` - For `xsd:dateTime`
- `date` - For `xsd:date`
- `time` - For `xsd:time`

#### 2.3.2 Number Validation

```json
{
  "type": "number",
  "minimum": 0,
  "maximum": 100,
  "exclusiveMinimum": 0,
  "multipleOf": 0.01
}
```

#### 2.3.3 Object Validation

```json
{
  "type": "object",
  "properties": {
    "name": { "type": "string" }
  },
  "required": ["name"],
  "additionalProperties": false,
  "minProperties": 1,
  "maxProperties": 10,
  "propertyNames": { "pattern": "^[a-z]" },
  "patternProperties": {
    "^S_": { "type": "string" }
  }
}
```

**JSON-LD Mapping**:
- `additionalProperties` ← `@explicit` flag
- `required` ← `@requireAll` flag, property presence in frame
- `patternProperties` ← Language maps, index maps

#### 2.3.4 Array Validation

```json
{
  "type": "array",
  "items": { "type": "string" },
  "minItems": 1,
  "maxItems": 10,
  "uniqueItems": true,      // For @set container
  "contains": { "type": "object" },
  "prefixItems": [          // Tuple validation
    { "type": "string" },
    { "type": "number" }
  ]
}
```

### 2.4 Composition Keywords

#### 2.4.1 `allOf`

All schemas must validate:

```json
{
  "allOf": [
    { "type": "object" },
    { "required": ["name"] }
  ]
}
```

#### 2.4.2 `anyOf`

At least one schema must validate:

```json
{
  "anyOf": [
    { "type": "string" },
    { "type": "number" }
  ]
}
```

**JSON-LD use case**: Multiple possible types for a property.

#### 2.4.3 `oneOf`

Exactly one schema must validate:

```json
{
  "oneOf": [
    { "type": "string", "format": "uri" },
    { "type": "object", "properties": { "@id": {} } }
  ]
}
```

**JSON-LD use case**: `@embed: false` allows either URI string or node reference object.

#### 2.4.4 `not`

Schema must NOT validate:

```json
{
  "not": { "type": "null" }
}
```

### 2.5 Conditional Keywords

#### 2.5.1 `if`/`then`/`else`

```json
{
  "if": {
    "properties": { "@type": { "const": "Person" } }
  },
  "then": {
    "required": ["name"]
  },
  "else": {
    "required": ["title"]
  }
}
```

**JSON-LD use case**: Different validation based on `@type`.

#### 2.5.2 `dependentRequired`

```json
{
  "dependentRequired": {
    "creditCard": ["billingAddress"]
  }
}
```

#### 2.5.3 `dependentSchemas`

```json
{
  "dependentSchemas": {
    "creditCard": {
      "properties": {
        "billingAddress": { "type": "string" }
      }
    }
  }
}
```

### 2.6 Schema Reuse

#### 2.6.1 `$ref`

Reference another schema:

```json
{
  "$defs": {
    "person": {
      "type": "object",
      "properties": {
        "name": { "type": "string" }
      }
    }
  },
  "properties": {
    "author": { "$ref": "#/$defs/person" }
  }
}
```

**JSON-LD use case**: Reusable schemas for common types like `Person`, `Organization`.

#### 2.6.2 `$dynamicRef`

Dynamic reference resolution (useful for recursive structures):

```json
{
  "$dynamicAnchor": "node",
  "type": "object",
  "properties": {
    "children": {
      "type": "array",
      "items": { "$dynamicRef": "#node" }
    }
  }
}
```

### 2.7 Annotations

```json
{
  "title": "Person Schema",
  "description": "Schema for a person object",
  "default": {},
  "examples": [
    { "@type": "Person", "name": "John" }
  ],
  "deprecated": false,
  "readOnly": false,
  "writeOnly": false
}
```

---

## Part 3: Mapping JSON-LD Frames to JSON Schema

### 3.1 Core Mapping Table

| JSON-LD Frame | JSON Schema | Notes |
|---------------|-------------|-------|
| `{}` (empty frame) | `{}` or `{"type": "object"}` | Minimal validation |
| `{"@type": "T"}` | `{"properties": {"@type": {"const": "T"}}}` | Type constraint |
| `{"@type": ["A","B"]}` | `{"properties": {"@type": {"enum": ["A","B"]}}}` | Multiple types |
| `{"@type": {}}` | `{"properties": {"@type": {"type": "string"}}}` | Any type (wildcard) |
| `{"@id": "uri"}` | `{"properties": {"@id": {"const": "uri"}}}` | Specific ID |
| `{"@id": {}}` | `{"properties": {"@id": {"format": "uri"}}}` | Any ID |
| `{"prop": {}}` | `{"properties": {"prop": {"type": "string"}}}` | Property present |
| `{"@explicit": true}` | `{"additionalProperties": false}` | No extra props |
| `{"@requireAll": true}` | All props in `required` | All required |
| `{"@embed": false}` | `oneOf: [uri, {id object}]` | Reference only |

### 3.2 Complex Patterns

#### 3.2.1 Nested Objects

```json
// Frame
{
  "@type": "Person",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": {}
  }
}

// Schema
{
  "type": "object",
  "properties": {
    "@type": { "const": "Person" },
    "address": {
      "type": "object",
      "properties": {
        "@type": { "const": "PostalAddress" },
        "streetAddress": { "type": "string" }
      }
    }
  }
}
```

#### 3.2.2 Arrays

```json
// Frame
{
  "knows": [{ "@type": "Person" }]
}

// Schema
{
  "properties": {
    "knows": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "@type": { "const": "Person" }
        }
      }
    }
  }
}
```

#### 3.2.3 Reverse Properties

```json
// Frame
{
  "@type": "Person",
  "@reverse": {
    "author": { "@type": "Book" }
  }
}

// Schema
{
  "type": "object",
  "properties": {
    "@type": { "const": "Person" },
    "@reverse": {
      "type": "object",
      "properties": {
        "author": {
          "oneOf": [
            { "type": "object", "properties": { "@type": { "const": "Book" } } },
            { "type": "array", "items": { "type": "object", "properties": { "@type": { "const": "Book" } } } }
          ]
        }
      }
    }
  }
}
```

#### 3.2.4 Value Objects

```json
// Frame
{
  "title": {
    "@value": {},
    "@language": "en"
  }
}

// Schema
{
  "properties": {
    "title": {
      "oneOf": [
        { "type": "string" },
        {
          "type": "object",
          "properties": {
            "@value": { "type": "string" },
            "@language": { "const": "en" }
          },
          "required": ["@value"]
        }
      ]
    }
  }
}
```

#### 3.2.5 Language Maps

```json
// Frame with language container (from context)
{
  "@context": {
    "name": { "@container": "@language" }
  },
  "name": {}
}

// Schema
{
  "properties": {
    "name": {
      "oneOf": [
        { "type": "string" },
        {
          "type": "object",
          "patternProperties": {
            "^[a-z]{2}(-[A-Z]{2})?$": { "type": "string" }
          },
          "additionalProperties": false
        }
      ]
    }
  }
}
```

#### 3.2.6 Graph Containers

```json
// Frame
{
  "@graph": [{
    "@type": "Person",
    "name": {}
  }]
}

// Schema
{
  "type": "object",
  "properties": {
    "@graph": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "@type": { "const": "Person" },
          "name": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Part 4: Implementation Guidelines

### 4.1 Code Structure

```
jsonldframe2schema/
├── __init__.py          # Public API exports
├── __main__.py          # CLI entry point
├── cli.py               # Command-line interface
├── converter.py         # Core conversion logic (MAIN FILE)
```

### 4.2 Key Classes and Functions

#### 4.2.1 `FrameToSchemaConverter` Class

The main converter class in `converter.py`:

```python
class FrameToSchemaConverter:
    TYPE_MAPPINGS = {...}       # XSD → JSON Schema type mappings
    FRAMING_KEYWORDS = {...}    # JSON-LD frame keywords to skip
    
    def convert(frame) → schema
    def _extract_framing_flags(frame) → flags
    def _extract_context(frame) → context
    def _process_frame_object(frame, schema, flags, context)
    def _process_type_constraint(type_value) → schema
    def _process_id_constraint(id_value) → schema
    def _process_property(key, value, flags, context) → schema
    def _process_array_frame(array, flags, context) → schema
    def _process_nested_frame(frame, flags, context) → schema
```

### 4.3 Areas Needing Implementation

#### 4.3.1 HIGH PRIORITY: `@reverse` Support

Current state: Not implemented
Required changes:
1. Add `@reverse` to FRAMING_KEYWORDS
2. Detect `@reverse` in frame processing
3. Generate schema with `@reverse` property containing nested schemas
4. Handle array vs single object cases

```python
def _process_reverse_property(self, reverse_obj, flags, context):
    """Process @reverse frame property."""
    reverse_schema = {"type": "object", "properties": {}}
    
    for prop_name, prop_frame in reverse_obj.items():
        prop_schema = self._process_nested_frame(prop_frame, flags, context)
        # Allow single object or array
        reverse_schema["properties"][prop_name] = {
            "oneOf": [
                prop_schema,
                {"type": "array", "items": prop_schema}
            ]
        }
    
    return reverse_schema
```

#### 4.3.2 HIGH PRIORITY: `@graph` Container Support

Current state: Partially implemented (in FRAMING_KEYWORDS but not processed)
Required changes:
1. Detect `@graph` in root frame
2. Generate schema with `@graph` property
3. Process array of frames within `@graph`

```python
def _process_graph_container(self, graph_value, flags, context):
    """Process @graph container."""
    if isinstance(graph_value, list):
        if len(graph_value) == 0:
            return {"type": "array", "items": {}}
        
        # Process first frame as item template
        item_frame = graph_value[0]
        item_schema = self._process_nested_frame(item_frame, flags, context)
        return {"type": "array", "items": item_schema}
    
    return {"type": "array"}
```

#### 4.3.3 MEDIUM PRIORITY: Value Objects

Current state: Not implemented
Required:
1. Detect value object patterns (`@value`, `@type`, `@language`)
2. Generate schemas allowing string OR value object
3. Support language filtering

```python
def _process_value_object_frame(self, value_frame, flags, context):
    """Process value object frame."""
    schemas = []
    
    # Allow simple string
    schemas.append({"type": "string"})
    
    # Allow value object
    value_obj_schema = {
        "type": "object",
        "properties": {"@value": {}},
        "required": ["@value"]
    }
    
    if "@language" in value_frame:
        lang = value_frame["@language"]
        if isinstance(lang, str):
            value_obj_schema["properties"]["@language"] = {"const": lang}
        elif isinstance(lang, dict) and len(lang) == 0:
            value_obj_schema["properties"]["@language"] = {"type": "string"}
    
    if "@type" in value_frame:
        # Typed value object
        value_obj_schema["properties"]["@type"] = {"type": "string"}
    
    schemas.append(value_obj_schema)
    
    return {"oneOf": schemas}
```

#### 4.3.4 MEDIUM PRIORITY: Language Maps

Current state: Not implemented
Required:
1. Parse `@container: @language` from context
2. Generate `patternProperties` for language codes

#### 4.3.5 MEDIUM PRIORITY: Index Containers

Current state: Not implemented
Required:
1. Parse `@container: @index` from context
2. Generate schema with `additionalProperties` for indexed values

#### 4.3.6 LOW PRIORITY: `@default` Values

Current state: Partial (default values work, but not `@default` keyword)
Required:
1. Detect `@default` in property frames
2. Map to JSON Schema `default` keyword

#### 4.3.7 LOW PRIORITY: `@nest` Properties

Current state: Not implemented
Required:
1. Parse `@nest` from context
2. Restructure schema to group nested properties

### 4.4 Testing Strategy

1. **Unit tests** (`tests/test_converter.py`): Test individual mapping rules
2. **Integration tests** (`tests/test_w3c_integration.py`): Test against W3C frames
3. **Test cases** (`tests/test_cases/`): Pairs of `.jsonld` frames and `.json` expected schemas
4. **Framing validation tests** (`tests/test_framing_validation.py`): End-to-end validation using W3C test suite

#### 4.4.1 Framing Validation Tests (End-to-End)

The `test_framing_validation.py` file provides comprehensive end-to-end testing that:

1. **Downloads** W3C JSON-LD framing test suite data
2. **Frames** input documents using pyld's framing algorithm
3. **Generates** JSON Schema from the frame using our converter
4. **Validates** that framed output conforms to the generated schema

This is the gold standard for testing because it validates the entire pipeline: frame → schema → validation.

**Current pass rate: ~62% of W3C positive tests**

The remaining failures are due to:
- Complex patterns (`oneOf`, `@container`, `@embed: false`)
- pyld framing errors (not our fault)
- Advanced features not yet implemented

**To run the validation tests:**
```bash
pytest tests/test_framing_validation.py -v
```

**To see detailed results:**
```bash
pytest tests/test_framing_validation.py::TestFramingSchemaConformance::test_all_positive_tests_validate -v -s
```

#### 4.4.2 W3C Test Suite Location

The W3C framing test suite is downloaded to:
- `tests/jsonld_test_suite/frame/` - Frame files
- `tests/jsonld_test_suite/frame-manifest.jsonld` - Test manifest

Input and output files are automatically downloaded on first run.

When adding features:
1. Add test case in `tests/test_cases/` with frame and expected schema
2. Add unit test in `tests/test_converter.py`
3. Implement feature
4. Verify W3C test suite doesn't regress
5. Check if W3C validation pass rate improves

**IMPORTANT: Always include `@context` in test cases!**

Every test case frame MUST include a `@context` to be valid JSON-LD:

```json
{
  "@context": {
    "@vocab": "http://schema.org/"
  },
  "@type": "Person",
  "name": {}
}
```

Or with explicit namespace prefixes:

```json
{
  "@context": {
    "ex": "http://example.org/vocab#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ex:Person",
  "ex:name": {}
}
```

Without `@context`:
- Property names have no semantic meaning
- Type coercion cannot be resolved
- The frame cannot be properly expanded by pyld
- Tests may pass incorrectly or give misleading results

### 4.5 Dependencies

- **pyld**: JSON-LD processing library (context expansion)
- **jsonschema**: JSON Schema validation (for testing generated schemas)
- **deepdiff**: Schema comparison in tests

---

## Part 5: Common Pitfalls and Edge Cases

### 5.1 Frame vs Schema Semantics

**Key distinction**: 
- Frame = "what I want to extract/match"
- Schema = "what valid output looks like"

A frame `{"name": {}}` means "include name if present", but the schema should validate that name exists and is valid.

### 5.2 Property Multiplicity

In JSON-LD, any property can be an array or single value:

```json
// Both valid:
{"knows": {"@id": "person1"}}
{"knows": [{"@id": "person1"}, {"@id": "person2"}]}
```

Schema should often allow both:
```json
{
  "knows": {
    "oneOf": [
      { "$ref": "#/$defs/person" },
      { "type": "array", "items": { "$ref": "#/$defs/person" } }
    ]
  }
}
```

### 5.3 Blank Nodes

Blank nodes have `@id` starting with `_:`. Schema should:
- Allow `_:` prefix for blank node IDs
- Not require `format: uri` for blank nodes

```json
{
  "@id": {
    "oneOf": [
      { "type": "string", "format": "uri" },
      { "type": "string", "pattern": "^_:" }
    ]
  }
}
```

### 5.4 Compact vs Expanded Form

The converter should handle both compact and expanded JSON-LD:

```json
// Compact
{"name": "John"}

// Expanded
{"http://schema.org/name": [{"@value": "John"}]}
```

Currently, the converter primarily handles compact form. Consider using `pyld.jsonld.expand()` for normalization.

### 5.5 Context Scoping

Nested objects can have their own `@context`:

```json
{
  "@context": {"name": "http://schema.org/name"},
  "name": "John",
  "address": {
    "@context": {"street": "http://schema.org/streetAddress"},
    "street": "123 Main St"
  }
}
```

The converter needs to track context scope when processing nested frames.

---

## Part 6: Quick Reference

### 6.1 JSON-LD Keywords in Frames

| Keyword | Purpose | Schema Impact |
|---------|---------|---------------|
| `@context` | Define vocabulary | Type inference |
| `@type` | Type constraint | `const` or `enum` |
| `@id` | ID constraint | `const` or `format: uri` |
| `@embed` | Embedding behavior | Object vs reference |
| `@explicit` | Property filtering | `additionalProperties` |
| `@requireAll` | Match strictness | `required` array |
| `@omitDefault` | Null handling | Optional properties |
| `@default` | Default values | `default` keyword |
| `@graph` | Graph container | Nested array schema |
| `@reverse` | Reverse properties | Nested object schema |
| `@value` | Value object | Value object schema |
| `@language` | Language tag | `const` constraint |
| `@container` | Container type | Array/object patterns |
| `@list` | Ordered list | Array schema |
| `@set` | Unordered set | Array + uniqueItems |
| `@index` | Index map | Object + additionalProps |

### 6.2 XSD to JSON Schema Type Mapping

| XSD Type | JSON Schema |
|----------|-------------|
| `xsd:string` | `{"type": "string"}` |
| `xsd:integer` | `{"type": "integer"}` |
| `xsd:int` | `{"type": "integer"}` |
| `xsd:long` | `{"type": "integer"}` |
| `xsd:boolean` | `{"type": "boolean"}` |
| `xsd:double` | `{"type": "number"}` |
| `xsd:float` | `{"type": "number"}` |
| `xsd:decimal` | `{"type": "number"}` |
| `xsd:dateTime` | `{"type": "string", "format": "date-time"}` |
| `xsd:date` | `{"type": "string", "format": "date"}` |
| `xsd:time` | `{"type": "string", "format": "time"}` |
| `xsd:anyURI` | `{"type": "string", "format": "uri"}` |
| `@id` | `{"type": "string", "format": "uri"}` |

---

## Part 7: Resources

### 7.1 Specifications
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)
- [JSON-LD 1.1 Framing](https://www.w3.org/TR/json-ld11-framing/)
- [JSON-LD 1.1 API](https://www.w3.org/TR/json-ld11-api/)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core)
- [JSON Schema Validation](https://json-schema.org/draft/2020-12/json-schema-validation)

### 7.2 Test Suites
- [W3C JSON-LD Framing Tests](https://w3c.github.io/json-ld-framing/tests/)
- [JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite)

### 7.3 Libraries
- [pyld](https://github.com/digitalbazaar/pyld) - Python JSON-LD library
- [jsonschema](https://github.com/python-jsonschema/jsonschema) - Python JSON Schema library

---

## Appendix A: Decision Log

When making changes, document decisions here:

| Date | Decision | Rationale |
|------|----------|-----------|
| Initial | Use `oneOf` for embed=false | Allows URI string or ID object |
| Initial | Default to additionalProperties: true | Matches @explicit: false default |
| Initial | Property in frame = required | Frame implies expectation |

---

## Appendix B: Known Issues

1. **Issue**: Circular references not handled
   - **Impact**: Stack overflow on recursive structures
   - **Workaround**: Use `$ref` with `$defs` for recursive types

2. **Issue**: Context with remote URLs not resolved
   - **Impact**: Type information lost
   - **Workaround**: Inline context definitions

3. **Issue**: Multiple types for single property not supported
   - **Impact**: Union types in JSON-LD not validated
   - **Workaround**: Use `anyOf` in schema manually

---

## Appendix C: Linting and Code Quality

**IMPORTANT**: Before completing any task, agents MUST run the linting tools from CI to ensure code quality and that CI will pass.

### C.1 Required Linting Steps

At the end of every coding session, run the following linting tools in order:

#### C.1.1 Code Formatting with Black

First, check formatting:
```bash
black --check jsonldframe2schema tests examples
```

If formatting issues are found, fix them automatically:
```bash
black jsonldframe2schema tests examples
```

#### C.1.2 Code Linting with Flake8

Check for code quality issues:
```bash
flake8 jsonldframe2schema tests --max-line-length=120
```

Fix any issues reported by flake8 manually.

#### C.1.3 Type Checking with Mypy

Check for type errors:
```bash
mypy jsonldframe2schema --ignore-missing-imports
```

Fix any type errors reported by mypy.

### C.2 Linting Workflow

1. **After making code changes**: Run all three linting tools
2. **Fix all issues**: Do not leave linting errors unfixed
3. **Commit fixes**: Use `report_progress` to commit linting fixes
4. **Verify CI**: Ensure all linting checks will pass in CI

### C.3 Installing Linting Tools

If linting tools are not installed, install them first:
```bash
pip install -r requirements-dev.txt
```

### C.4 Pre-Commit Checklist

Before finalizing any task:
- [ ] Run `black` to format code
- [ ] Run `flake8` and fix all issues
- [ ] Run `mypy` and fix all type errors
- [ ] Verify no linting errors remain
- [ ] Commit all changes including linting fixes

---

## Appendix D: Documentation Updates

**CRITICAL**: Whenever there are code changes that affect the algorithm, behavior, or functionality of the library, agents MUST update the corresponding documentation files.

### D.1 Documentation Files That Must Be Updated

#### D.1.1 ALGORITHM.md

The `ALGORITHM.md` file in the repository root contains the formal algorithm definition for converting JSON-LD frames to JSON Schema.

**When to update**:
- When adding new features or capabilities to the converter
- When changing how existing features work
- When fixing bugs that affect the algorithm behavior
- When adding support for new JSON-LD framing keywords
- When modifying the type mapping or schema generation logic

**What to update**:
- Update the algorithm steps to reflect new or changed behavior
- Add new sections for new features
- Update examples to demonstrate the changes
- Ensure the pseudocode accurately represents the implementation
- Update the complexity analysis if performance characteristics change

**Example scenarios**:
- If you add support for `@reverse` properties, update the algorithm to include steps for processing reverse properties
- If you change how `@embed` flags are handled, update the corresponding algorithm sections
- If you add new type mappings, update the type mapping tables

#### D.1.2 ReSpec Specification Document (spec/index.html)

The `spec/index.html` file is a formal specification document written using the W3C ReSpec format. It provides the authoritative technical specification for the conversion algorithm.

**When to update**:
- When adding new features or capabilities to the converter
- When changing how existing features work
- When fixing bugs that affect the specification
- When adding support for new JSON-LD framing keywords
- When the algorithm behavior changes in any way

**What to update**:
- Update the algorithm definition sections to reflect changes
- Add new sections for new features or capabilities
- Update examples to demonstrate the changes
- Ensure all algorithm steps are accurately documented
- Update any references or citations if needed
- Maintain consistency with ALGORITHM.md

**Important notes about ReSpec**:
- The spec uses ReSpec, a W3C tool for creating specifications
- Maintain the existing HTML structure and ReSpec classes
- Keep the technical writing style consistent (formal, precise)
- Ensure examples are complete and valid JSON-LD/JSON Schema
- Test that the spec still renders correctly after changes

### D.2 Documentation Update Workflow

When making code changes that affect functionality:

1. **Make code changes first**: Implement and test your code changes
2. **Update ALGORITHM.md**: Reflect the changes in the algorithm documentation
3. **Update spec/index.html**: Update the formal specification to match
4. **Ensure consistency**: Verify that both documentation files are consistent with each other and with the code
5. **Review examples**: Ensure all examples in both files are accurate and working
6. **Commit together**: Commit code changes and documentation updates together

### D.3 Documentation Quality Standards

All documentation updates must:
- Be technically accurate and match the implementation
- Use clear, precise language
- Include examples where appropriate
- Maintain consistency with existing documentation style
- Be comprehensive (don't leave gaps or incomplete sections)

### D.4 Documentation Review Checklist

Before finalizing any task with code changes:
- [ ] Check if code changes affect the algorithm or behavior
- [ ] Update ALGORITHM.md if changes affect the conversion process
- [ ] Update spec/index.html if changes affect the specification
- [ ] Verify consistency between code, ALGORITHM.md, and spec/index.html
- [ ] Test that all examples in documentation still work
- [ ] Ensure documentation is complete and accurate
- [ ] Commit documentation updates with code changes
