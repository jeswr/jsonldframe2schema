# Formal Mapping: JSON-LD 1.1 Framing to JSON Schema

This document defines the formal mapping between JSON-LD 1.1 Framing concepts (as defined in [W3C JSON-LD 1.1 Framing](https://www.w3.org/TR/json-ld11-framing/)) and JSON Schema constructs (as defined in [JSON Schema](https://json-schema.org/)).

## Overview

JSON-LD Frames describe the desired structure of JSON-LD documents, while JSON Schema describes the validation rules for JSON documents. This mapping allows us to translate frame definitions into schema definitions.

## Core Concept Mappings

### 1. Frame Structure → Schema Object

**JSON-LD Framing Spec Reference:** [Section 3.1 - Framing](https://www.w3.org/TR/json-ld11-framing/#framing)

**JSON Schema Reference:** [Core Schema Object](https://json-schema.org/understanding-json-schema/reference/object.html)

- A JSON-LD Frame object maps to a JSON Schema object with `type: "object"`
- Frame properties become schema `properties`
- The frame's `@context` informs type coercion and semantics but is not directly mapped to schema

**Mapping:**
```
Frame Object → { "type": "object", "properties": {...} }
```

### 2. @type Constraint → Type Validation

**JSON-LD Framing Spec Reference:** [Section 3.3 - Matching Frames](https://www.w3.org/TR/json-ld11-framing/#matching-frames)

**JSON Schema Reference:** [Properties and Required](https://json-schema.org/understanding-json-schema/reference/object.html#properties)

- A frame's `@type` constraint maps to a required property validation in JSON Schema
- When `@type` is specified in a frame, it indicates the framed output must include that type
- Multiple types in an array indicate alternatives (use `oneOf` or `anyOf`)

**Mapping:**
```
Frame: { "@type": "Person" } 
→ Schema: { 
    "type": "object",
    "properties": {
      "@type": { "const": "Person" }
    },
    "required": ["@type"]
  }

Frame: { "@type": ["Person", "Organization"] }
→ Schema: {
    "type": "object",
    "properties": {
      "@type": { "enum": ["Person", "Organization"] }
    },
    "required": ["@type"]
  }
```

### 3. @id Constraint → ID Pattern

**JSON-LD Framing Spec Reference:** [Section 3.3 - Matching Frames](https://www.w3.org/TR/json-ld11-framing/#matching-frames)

**JSON Schema Reference:** [String Format](https://json-schema.org/understanding-json-schema/reference/string.html#format)

- Frame `@id` with a specific value maps to a constant
- Frame `@id` with pattern or requirement maps to string format validation

**Mapping:**
```
Frame: { "@id": "http://example.org/person/1" }
→ Schema: {
    "type": "object",
    "properties": {
      "@id": { "const": "http://example.org/person/1" }
    }
  }

Frame: { "@id": {} }  (requires @id be present)
→ Schema: {
    "type": "object",
    "properties": {
      "@id": { "type": "string", "format": "uri" }
    },
    "required": ["@id"]
  }
```

### 4. Property Frames → Property Schemas

**JSON-LD Framing Spec Reference:** [Section 3.2 - Frame Objects](https://www.w3.org/TR/json-ld11-framing/#frame-objects)

**JSON Schema Reference:** [Object Properties](https://json-schema.org/understanding-json-schema/reference/object.html#properties)

- Each property in a frame maps to a corresponding property in the schema
- Nested frame objects map to nested schema objects
- Property presence in frame indicates expected presence in output

**Mapping:**
```
Frame: { "name": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    },
    "required": ["name"]
  }

Frame: { "address": { "@type": "PostalAddress" } }
→ Schema: {
    "type": "object",
    "properties": {
      "address": {
        "type": "object",
        "properties": {
          "@type": { "const": "PostalAddress" }
        },
        "required": ["@type"]
      }
    },
    "required": ["address"]
  }
```

### 5. @embed → Nested Object Schema

**JSON-LD Framing Spec Reference:** [Section 3.4.1 - Embedding](https://www.w3.org/TR/json-ld11-framing/#embedding)

**JSON Schema Reference:** [Nested Objects](https://json-schema.org/understanding-json-schema/reference/object.html)

- `@embed: true` (default) indicates referenced objects should be embedded
- `@embed: false` indicates only references (IDs) should be included
- `@embed: @always` forces embedding even when circular
- `@embed: @never` prevents embedding, only node references
- `@embed: @once` embeds first occurrence, references after

**Mapping:**
```
Frame: { "author": { "@embed": true, "@type": "Person" } }
→ Schema: {
    "properties": {
      "author": {
        "type": "object",
        "properties": {
          "@type": { "const": "Person" }
        }
      }
    }
  }

Frame: { "author": { "@embed": false } }
→ Schema: {
    "properties": {
      "author": {
        "oneOf": [
          { "type": "string", "format": "uri" },
          { 
            "type": "object",
            "properties": {
              "@id": { "type": "string", "format": "uri" }
            },
            "required": ["@id"],
            "additionalProperties": false
          }
        ]
      }
    }
  }
```

### 6. @explicit → Additional Properties

**JSON-LD Framing Spec Reference:** [Section 3.4.2 - Explicit Inclusion](https://www.w3.org/TR/json-ld11-framing/#explicit-inclusion-flag)

**JSON Schema Reference:** [additionalProperties](https://json-schema.org/understanding-json-schema/reference/object.html#additional-properties)

- `@explicit: true` means only properties explicitly listed in frame are included
- `@explicit: false` (default) means all properties may be included

**Mapping:**
```
Frame: { "@explicit": true, "name": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    },
    "additionalProperties": false
  }

Frame: { "@explicit": false, "name": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    },
    "additionalProperties": true
  }
```

### 7. @omitDefault → Optional Properties

**JSON-LD Framing Spec Reference:** [Section 3.4.3 - Omit Default Flag](https://www.w3.org/TR/json-ld11-framing/#omit-default-flag)

**JSON Schema Reference:** [Required Properties](https://json-schema.org/understanding-json-schema/reference/object.html#required-properties)

- `@omitDefault: true` omits properties with null values from output
- `@omitDefault: false` (default) includes properties even if null
- This affects whether properties should be in the `required` array

**Mapping:**
```
Frame: { "@omitDefault": true, "name": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" }
    }
    // name is not in required array
  }

Frame: { "@omitDefault": false, "name": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": ["string", "null"] }
    },
    "required": ["name"]
  }
```

### 8. @requireAll → All Properties Required

**JSON-LD Framing Spec Reference:** [Section 3.4.4 - Require All Flag](https://www.w3.org/TR/json-ld11-framing/#require-all-flag)

**JSON Schema Reference:** [Required Properties](https://json-schema.org/understanding-json-schema/reference/object.html#required-properties)

- `@requireAll: true` requires all properties in frame match for a node to be framed
- `@requireAll: false` (default) requires only one property match

**Mapping:**
```
Frame: { "@requireAll": true, "name": {}, "age": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "age": { "type": "number" }
    },
    "required": ["name", "age"]
  }

Frame: { "@requireAll": false, "name": {}, "age": {} }
→ Schema: {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "age": { "type": "number" }
    }
    // Not all properties required
  }
```

### 9. Array Frames → Array Schemas

**JSON-LD Framing Spec Reference:** [Section 3.2 - Frame Objects](https://www.w3.org/TR/json-ld11-framing/#frame-objects)

**JSON Schema Reference:** [Arrays](https://json-schema.org/understanding-json-schema/reference/array.html)

- Array notation in frames indicates array values in output
- Frame items define schema for array elements

**Mapping:**
```
Frame: { "knows": [{ "@type": "Person" }] }
→ Schema: {
    "type": "object",
    "properties": {
      "knows": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "@type": { "const": "Person" }
          },
          "required": ["@type"]
        }
      }
    }
  }
```

### 10. Default Values → Default in Schema

**JSON-LD Framing Spec Reference:** [Section 3.4 - Framing Flags](https://www.w3.org/TR/json-ld11-framing/#framing-flags)

**JSON Schema Reference:** [Default Values](https://json-schema.org/understanding-json-schema/reference/generic.html#generic-keywords)

- Default values specified in frame can map to JSON Schema default keyword
- However, frame defaults affect processing, not validation, so this mapping is informational

**Mapping:**
```
Frame: { "status": "active" }
→ Schema: {
    "type": "object",
    "properties": {
      "status": { 
        "type": "string",
        "default": "active"
      }
    }
  }
```

## Context-Aware Type Mappings

### 11. Type Coercion from @context

**JSON-LD Framing Spec Reference:** [Section 2 - Terminology](https://www.w3.org/TR/json-ld11-framing/#terminology)

**JSON Schema Reference:** [Type Validation](https://json-schema.org/understanding-json-schema/reference/type.html)

When a frame includes an `@context` with type coercion, the schema can infer JSON types:

- `@type: @id` → URI string
- `@type: xsd:string` → string
- `@type: xsd:integer` → integer
- `@type: xsd:boolean` → boolean
- `@type: xsd:dateTime` → string with date-time format

**Mapping:**
```
Context: { "age": { "@type": "xsd:integer" } }
Frame: { "age": {} }
→ Schema: {
    "properties": {
      "age": { "type": "integer" }
    }
  }
```

## Special Cases and Limitations

### Limitations of Direct Mapping

1. **Semantic Meaning**: JSON Schema validates structure, not semantics. The semantic meaning from JSON-LD is not fully preserved.

2. **Dynamic Behavior**: JSON-LD Framing is a transformation process, while JSON Schema is a validation specification. The schema describes the output structure, not the transformation logic.

3. **@graph Handling**: Frame `@graph` containers require special handling as they represent collections of nodes.

4. **Language Maps**: JSON-LD language maps don't have direct JSON Schema equivalents.

5. **Reverse Properties**: Frame reverse properties (`@reverse`) require complex schema patterns.

## Schema Generation Strategy

The mapping should follow these principles:

1. **Conservative Validation**: Generate schemas that validate the expected frame output, not overly restrictive
2. **Type Safety**: Use JSON Schema types that match JSON-LD value representations
3. **Extensibility**: Allow for additional properties unless `@explicit: true` is specified
4. **Documentation**: Include descriptions in schemas referencing the frame structure

## References

- [JSON-LD 1.1 Framing](https://www.w3.org/TR/json-ld11-framing/)
- [JSON Schema Core](https://json-schema.org/specification.html)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
