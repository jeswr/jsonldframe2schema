# Algorithm: JSON-LD Frame to JSON Schema Conversion

This document defines the algorithm for converting a JSON-LD 1.1 Frame into a JSON Schema document.

## Algorithm Overview

The conversion process consists of several phases:

1. **Parse Frame**: Parse and validate the JSON-LD Frame input
2. **Extract Context**: Extract type information from `@context` if present
3. **Process Frame Structure**: Recursively process the frame to build schema
4. **Apply Framing Flags**: Apply global framing flags to schema properties
5. **Generate Schema**: Output the complete JSON Schema document

## Algorithm Definition

### Input
- `frame`: A JSON-LD Frame object (as defined in JSON-LD 1.1 Framing specification)
- `schemaVersion`: (optional) JSON Schema version URI (default: "https://json-schema.org/draft/2020-12/schema")
- `graphOnly`: (optional) Boolean flag to output only the schema for @graph items (default: false)

### Output
- `schema`: A JSON Schema document (Draft 2020-12 or later)

### Algorithm Steps

```
function frameToSchema(frame, schemaVersion = "https://json-schema.org/draft/2020-12/schema", graphOnly = false):
    // Handle @graph wrapper if present
    frameContent = frame
    if "@graph" in frame:
        graphValue = frame["@graph"]
        if isArray(graphValue) and length(graphValue) > 0:
            frameContent = graphValue[0]
        else if isObject(graphValue):
            frameContent = graphValue
        
        // Preserve context from outer frame if inner doesn't have one
        if "@context" not in frameContent and "@context" in frame:
            frameContent = merge({ "@context": frame["@context"] }, frameContent)
    
    // Build the schema for graph items (the object schema)
    graphItemSchema = { "type": "object" }
    
    // Extract global framing flags
    flags = extractFramingFlags(frameContent)
    
    // Extract context for type information
    context = extractContext(frameContent)
    
    // Process the main frame object
    processFrameObject(frameContent, graphItemSchema, flags, context)
    
    // If graphOnly mode, return just the item schema
    if graphOnly:
        return merge({
            "$schema": schemaVersion
        }, graphItemSchema)
    
    // Build the full document schema with @context and @graph
    schema = {
        "$schema": schemaVersion,
        "type": "object",
        "properties": {
            "@context": {},
            "@graph": {
                "type": "array",
                "items": graphItemSchema
            }
        },
        "required": ["@context", "@graph"],
        "additionalProperties": true
    }
    
    return schema
```

### 1. Extract Framing Flags

```
function extractFramingFlags(frame):
    flags = {
        embed: frame["@embed"] ?? true,
        explicit: frame["@explicit"] ?? false,
        requireAll: frame["@requireAll"] ?? false,
        omitDefault: frame["@omitDefault"] ?? false
    }
    return flags
```

### 2. Extract Context

```
function extractContext(frame):
    if "@context" in frame:
        context = frame["@context"]
        return parseContext(context)
    return {}

function parseContext(context):
    // Parse JSON-LD context to extract type coercion information
    // This can use existing JSON-LD libraries
    typeMap = {}
    
    if isObject(context):
        for key, value in context:
            if key != "@vocab" and key != "@base":
                if isObject(value) and "@type" in value:
                    typeMap[key] = value["@type"]
    
    return typeMap
```

### 3. Process Frame Object

```
function processFrameObject(frame, schema, flags, context):
    properties = {}
    required = []
    
    // Process @type constraint
    if "@type" in frame:
        typeSchema = processTypeConstraint(frame["@type"])
        properties["@type"] = typeSchema
        if not isWildcard(frame["@type"]):
            required.push("@type")
    
    // Process @id constraint
    if "@id" in frame:
        idSchema = processIdConstraint(frame["@id"])
        properties["@id"] = idSchema
        if not isEmpty(frame["@id"]):
            required.push("@id")
    
    // Process regular properties
    for key, value in frame:
        if isFramingKeyword(key):
            continue  // Skip @context, @embed, @explicit, etc.
        
        propSchema = processProperty(key, value, flags, context)
        properties[key] = propSchema
        
        // Determine if property should be required
        if shouldBeRequired(key, value, flags):
            required.push(key)
    
    // Set schema properties
    schema["properties"] = properties
    
    if length(required) > 0:
        schema["required"] = required
    
    // Apply @explicit flag
    if flags.explicit:
        schema["additionalProperties"] = false
    else:
        schema["additionalProperties"] = true
    
    return schema
```

### 4. Process Type Constraint

```
function processTypeConstraint(typeValue):
    if isString(typeValue):
        // Single type
        return { "const": typeValue }
    
    else if isArray(typeValue):
        if length(typeValue) == 0:
            // Empty array means any type
            return { "type": "string" }
        else if length(typeValue) == 1:
            return { "const": typeValue[0] }
        else:
            // Multiple types - use enum
            return { "enum": typeValue }
    
    else if isEmpty(typeValue):
        // {} means @type must be present but any value
        return { "type": "string" }
    
    else if isWildcard(typeValue):
        // Wildcard type
        return { "type": "string" }
    
    return { "type": "string" }
```

### 5. Process ID Constraint

```
function processIdConstraint(idValue):
    if isString(idValue):
        // Specific ID value
        return { "const": idValue }
    
    else if isEmpty(idValue):
        // {} means @id must be present
        return { 
            "type": "string",
            "format": "uri"
        }
    
    else if isObject(idValue) and "@id" in idValue:
        // Nested @id specification
        return processIdConstraint(idValue["@id"])
    
    return { "type": "string", "format": "uri" }
```

### 6. Process Property

```
function processProperty(key, value, flags, context):
    // Get type information from context if available
    contextType = context[key] ?? null
    
    if isEmpty(value):
        // {} means property must be present
        return inferTypeFromContext(key, contextType)
    
    else if isString(value) or isNumber(value) or isBoolean(value):
        // Literal value - use as default/const
        return {
            "type": inferJsonType(value),
            "default": value
        }
    
    else if isArray(value):
        // Array frame
        return processArrayFrame(value, flags, context)
    
    else if isObject(value):
        // Nested object frame
        return processNestedFrame(value, flags, context)
    
    return {}
```

### 7. Infer Type from Context

```
function inferTypeFromContext(key, contextType):
    if contextType == null:
        return { "type": "string" }
    
    // Map JSON-LD types to JSON Schema types
    typeMapping = {
        "@id": { "type": "string", "format": "uri" },
        "xsd:string": { "type": "string" },
        "xsd:integer": { "type": "integer" },
        "xsd:int": { "type": "integer" },
        "xsd:long": { "type": "integer" },
        "xsd:boolean": { "type": "boolean" },
        "xsd:double": { "type": "number" },
        "xsd:float": { "type": "number" },
        "xsd:decimal": { "type": "number" },
        "xsd:dateTime": { "type": "string", "format": "date-time" },
        "xsd:date": { "type": "string", "format": "date" },
        "xsd:time": { "type": "string", "format": "time" }
    }
    
    if contextType in typeMapping:
        return typeMapping[contextType]
    
    return { "type": "string" }
```

### 8. Process Array Frame

```
function processArrayFrame(arrayValue, flags, context):
    if length(arrayValue) == 0:
        // Empty array frame
        return {
            "type": "array",
            "items": {}
        }
    
    // Process first element as item schema
    itemFrame = arrayValue[0]
    itemSchema = processProperty("_item", itemFrame, flags, context)
    
    return {
        "type": "array",
        "items": itemSchema
    }
```

### 9. Process Nested Frame

```
function processNestedFrame(frameObj, flags, context):
    // Extract nested framing flags (can override parent)
    nestedFlags = {
        embed: frameObj["@embed"] ?? flags.embed,
        explicit: frameObj["@explicit"] ?? flags.explicit,
        requireAll: frameObj["@requireAll"] ?? flags.requireAll,
        omitDefault: frameObj["@omitDefault"] ?? flags.omitDefault
    }
    
    // Check @embed flag
    if nestedFlags.embed == false or nestedFlags.embed == "@never":
        // Only reference, not embedded
        return {
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
    
    // Embedded object
    nestedSchema = { "type": "object" }
    processFrameObject(frameObj, nestedSchema, nestedFlags, context)
    
    return nestedSchema
```

### 10. Determine Required Status

```
function shouldBeRequired(key, value, flags):
    // If @requireAll is true, all properties are required
    if flags.requireAll:
        return true
    
    // If @omitDefault is true, properties are optional
    if flags.omitDefault:
        return false
    
    // If value is {}, property is required
    if isEmpty(value):
        return true
    
    // For nested objects and arrays, typically required
    if isObject(value) or isArray(value):
        return true
    
    return false
```

### 11. Helper Functions

```
function isFramingKeyword(key):
    framingKeywords = [
        "@context", "@embed", "@explicit", "@requireAll", 
        "@omitDefault", "@graph", "@reverse"
    ]
    return key in framingKeywords

function isEmpty(value):
    return isObject(value) and length(keys(value)) == 0

function isWildcard(value):
    return value == {} or value == []

function inferJsonType(value):
    if isString(value):
        return "string"
    else if isNumber(value):
        if isInteger(value):
            return "integer"
        return "number"
    else if isBoolean(value):
        return "boolean"
    else if isNull(value):
        return "null"
    else if isArray(value):
        return "array"
    else if isObject(value):
        return "object"
    return "string"
```

## Complete Algorithm Example

### Example 1: Simple Frame

**Input Frame:**
```json
{
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
```

**Algorithm Execution:**

1. Extract flags: `{embed: true, explicit: false, requireAll: false, omitDefault: false}`
2. Extract context: `{name: null, age: "xsd:integer"}`
3. Process @type: Creates `"@type": {"const": "Person"}` and adds to required
4. Process "name": Creates `"name": {"type": "string"}` and adds to required
5. Process "age": Uses context to create `"age": {"type": "integer"}` and adds to required
6. Apply flags: Sets `additionalProperties: true`

**Output Schema (with graphOnly=true):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "@type": {"const": "Person"},
    "name": {"type": "string"},
    "age": {"type": "integer"}
  },
  "required": ["@type", "name", "age"],
  "additionalProperties": true
}
```

**Output Schema (default, graphOnly=false):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "@context": {},
    "@graph": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "@type": {"const": "Person"},
          "name": {"type": "string"},
          "age": {"type": "integer"}
        },
        "required": ["@type", "name", "age"],
        "additionalProperties": true
      }
    }
  },
  "required": ["@context", "@graph"],
  "additionalProperties": true
}
```

### Example 2: Nested Frame with Embedding

**Input Frame:**
```json
{
  "@type": "Person",
  "@explicit": true,
  "name": {},
  "address": {
    "@type": "PostalAddress",
    "streetAddress": {},
    "addressLocality": {}
  }
}
```

**Algorithm Execution:**

1. Extract flags: `{embed: true, explicit: true, requireAll: false, omitDefault: false}`
2. Process @type: Creates `"@type": {"const": "Person"}`
3. Process "name": Creates `"name": {"type": "string"}`
4. Process "address": 
   - Detects nested object
   - Recursively processes with nested flags
   - Creates nested schema with PostalAddress type
5. Apply explicit flag: Sets `additionalProperties: false`

**Output Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "@type": {"const": "Person"},
    "name": {"type": "string"},
    "address": {
      "type": "object",
      "properties": {
        "@type": {"const": "PostalAddress"},
        "streetAddress": {"type": "string"},
        "addressLocality": {"type": "string"}
      },
      "required": ["@type", "streetAddress", "addressLocality"],
      "additionalProperties": true
    }
  },
  "required": ["@type", "name", "address"],
  "additionalProperties": false
}
```

## Complexity Analysis

- **Time Complexity**: O(n) where n is the number of properties in the frame (including nested)
- **Space Complexity**: O(d) where d is the maximum depth of nested frames

## Extension Points

The algorithm can be extended to handle:

1. **Custom Type Mappings**: Allow users to define custom mappings from JSON-LD types to JSON Schema formats
2. **Validation Rules**: Extract additional validation rules from frame annotations
3. **Schema Composition**: Use `allOf`, `anyOf`, `oneOf` for complex type constraints
4. **References**: Generate `$ref` for reusable schema components

## Implementation Notes

When implementing this algorithm:

1. Use existing JSON-LD libraries for context processing
2. Handle circular references carefully
3. Provide clear error messages for invalid frames
4. Support both JSON-LD 1.0 and 1.1 frame syntax
5. Allow configuration of JSON Schema draft version
6. Validate generated schemas against JSON Schema meta-schema
