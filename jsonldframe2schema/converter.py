"""
Core converter module for transforming JSON-LD Frames to JSON Schema.

This module implements the algorithm defined in ALGORITHM.md to convert
JSON-LD 1.1 Frames into JSON Schema documents.
"""

from typing import Any, Dict, List, Optional, Union
import copy
from pyld import jsonld


class FrameToSchemaConverter:
    """
    Converts JSON-LD Frames to JSON Schema documents.

    This class implements the algorithm for mapping JSON-LD framing concepts
    to JSON Schema validation constructs as defined in MAPPING.md and ALGORITHM.md.
    """

    # JSON-LD to JSON Schema type mappings
    # Maps expanded type URIs to JSON Schema types
    # Note: Contexts should properly define prefixes (e.g., "xsd": "http://www.w3.org/2001/XMLSchema#")
    # for pyld to expand them correctly
    TYPE_MAPPINGS = {
        "@id": {"type": "string", "format": "uri"},
        "http://www.w3.org/2001/XMLSchema#string": {"type": "string"},
        "http://www.w3.org/2001/XMLSchema#integer": {"type": "integer"},
        "http://www.w3.org/2001/XMLSchema#int": {"type": "integer"},
        "http://www.w3.org/2001/XMLSchema#long": {"type": "integer"},
        "http://www.w3.org/2001/XMLSchema#boolean": {"type": "boolean"},
        "http://www.w3.org/2001/XMLSchema#double": {"type": "number"},
        "http://www.w3.org/2001/XMLSchema#float": {"type": "number"},
        "http://www.w3.org/2001/XMLSchema#decimal": {"type": "number"},
        "http://www.w3.org/2001/XMLSchema#dateTime": {
            "type": "string",
            "format": "date-time",
        },
        "http://www.w3.org/2001/XMLSchema#date": {"type": "string", "format": "date"},
        "http://www.w3.org/2001/XMLSchema#time": {"type": "string", "format": "time"},
    }

    FRAMING_KEYWORDS = {
        "@context",
        "@embed",
        "@explicit",
        "@requireAll",
        "@omitDefault",
        "@graph",
        "@reverse",
    }

    def __init__(
        self,
        schema_version: str = "https://json-schema.org/draft/2020-12/schema",
        graph_only: bool = False,
    ):
        """
        Initialize the converter.

        Args:
            schema_version: JSON Schema version URI to use in output
            graph_only: If True, output only the schema for @graph items (without
                       @context and @graph wrapper). Default is False, which outputs
                       a full document schema with @context and @graph.
        """
        self.schema_version = schema_version
        self.graph_only = graph_only

    def convert(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a JSON-LD Frame to JSON Schema.

        Args:
            frame: JSON-LD Frame object

        Returns:
            JSON Schema document. By default, this is a full document schema with
            @context and @graph properties. If graph_only=True was set during
            initialization, returns only the schema for objects within @graph.
        """
        # Check if frame has @graph - if so, use the content from @graph
        frame_content = frame
        if "@graph" in frame:
            graph_value = frame["@graph"]
            # Handle both array and single object in @graph
            if isinstance(graph_value, list) and len(graph_value) > 0:
                frame_content = graph_value[0]
            elif isinstance(graph_value, dict):
                frame_content = graph_value
            # Preserve context from outer frame if inner doesn't have one
            if "@context" not in frame_content and "@context" in frame:
                frame_content = {"@context": frame["@context"], **frame_content}

        # Build the schema for graph items (the object schema)
        graph_item_schema: Dict[str, Any] = {"type": "object"}

        # Extract global framing flags
        flags = self._extract_framing_flags(frame_content)

        # Extract context for type information
        context = self._extract_context(frame_content)

        # Process the main frame object
        self._process_frame_object(frame_content, graph_item_schema, flags, context)

        # If graph_only mode, return just the item schema with $schema
        if self.graph_only:
            return {"$schema": self.schema_version, **graph_item_schema}

        # Build the full document schema with @context and @graph
        schema: Dict[str, Any] = {
            "$schema": self.schema_version,
            "type": "object",
            "properties": {
                "@context": {},
                "@graph": {
                    "type": "array",
                    "items": graph_item_schema,
                },
            },
            "required": ["@context", "@graph"],
            "additionalProperties": True,
        }

        return schema

    def _extract_framing_flags(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract framing flags from the frame.

        Args:
            frame: JSON-LD Frame object

        Returns:
            Dictionary of framing flags
        """
        return {
            "embed": frame.get("@embed", True),
            "explicit": frame.get("@explicit", False),
            "requireAll": frame.get("@requireAll", False),
            "omitDefault": frame.get("@omitDefault", False),
        }

    def _extract_context(self, frame: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Extract type and container information from @context.

        Args:
            frame: JSON-LD Frame object

        Returns:
            Dictionary mapping property names to their type URIs or container info
        """
        context = frame.get("@context")
        if not context:
            return {}

        return self._parse_context(context)

    def _parse_context(
        self, context: Union[str, Dict, List]
    ) -> Dict[str, Optional[str]]:
        """
        Parse JSON-LD context to extract type coercion and container information.

        This method uses only pyld's expand() function to extract type information,
        without any custom context parsing logic. It also captures @container values.

        Args:
            context: JSON-LD context (string, dict, or list)

        Returns:
            Dictionary mapping property names to their type URIs or container types
        """
        type_map: Dict[str, Optional[str]] = {}

        if not context:
            return type_map

        try:
            # Process dictionary contexts
            if isinstance(context, dict):
                for key, value in context.items():
                    # Skip JSON-LD keywords
                    if key.startswith("@"):
                        continue

                    # Skip simple string mappings (both prefix definitions and simple property URIs)
                    if isinstance(value, str):
                        continue

                    # Check if this property definition has @container
                    if isinstance(value, dict) and "@container" in value:
                        # Store container type with special prefix
                        container_type = value["@container"]
                        type_map[key] = f"@container:{container_type}"
                    # Check if this property definition has type coercion
                    elif isinstance(value, dict) and "@type" in value:
                        # Use pyld.expand() to resolve the type URI
                        test_doc = {"@context": context, key: "test_value"}
                        try:
                            expanded = jsonld.expand(test_doc)
                            # Extract type from expanded document
                            if expanded and len(expanded) > 0:
                                for prop_uri, prop_values in expanded[0].items():
                                    if not prop_uri.startswith("@"):
                                        if (
                                            prop_values
                                            and isinstance(prop_values, list)
                                            and len(prop_values) > 0
                                            and isinstance(prop_values[0], dict)
                                        ):
                                            type_uri = prop_values[0].get("@type")
                                            if type_uri:
                                                type_map[key] = type_uri
                                                break
                        except (jsonld.JsonLdError, ValueError, TypeError):
                            # If pyld cannot process this property, store None
                            type_map[key] = None
                    elif isinstance(value, dict):
                        # Property definition without type coercion or container
                        type_map[key] = None

            # Process array contexts (recursively)
            elif isinstance(context, list):
                for ctx in context:
                    type_map.update(self._parse_context(ctx))

        except (jsonld.JsonLdError, ValueError, TypeError, KeyError):
            # If context processing fails entirely, return empty type map
            pass

        return type_map

    def _process_frame_object(
        self,
        frame: Dict[str, Any],
        schema: Dict[str, Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> None:
        """
        Process a frame object and populate the schema.

        Args:
            frame: JSON-LD Frame object
            schema: Schema object to populate
            flags: Framing flags
            context: Type context mapping
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []

        # Process @type constraint
        if "@type" in frame:
            type_schema = self._process_type_constraint(frame["@type"])
            properties["@type"] = type_schema
            if not self._is_wildcard(frame["@type"]):
                required.append("@type")

        # Process @id constraint
        if "@id" in frame:
            id_schema = self._process_id_constraint(frame["@id"])
            properties["@id"] = id_schema
            if not self._is_empty(frame["@id"]):
                required.append("@id")

        # Process @reverse constraint
        if "@reverse" in frame:
            reverse_schema = self._process_reverse_property(frame["@reverse"], flags, context)
            properties["@reverse"] = reverse_schema
            required.append("@reverse")

        # Process regular properties
        for key, value in frame.items():
            if key in self.FRAMING_KEYWORDS:
                continue
            if key in ("@type", "@id"):
                continue

            prop_schema = self._process_property(key, value, flags, context)
            properties[key] = prop_schema

            # Determine if property should be required
            if self._should_be_required(key, value, flags):
                required.append(key)

        # Set schema properties
        if properties:
            schema["properties"] = properties

        if required:
            schema["required"] = required

        # Apply @explicit flag
        schema["additionalProperties"] = not flags["explicit"]

    def _process_type_constraint(self, type_value: Any) -> Dict[str, Any]:
        """
        Process @type constraint from frame.

        Args:
            type_value: The @type value from the frame

        Returns:
            JSON Schema type constraint
        """
        if isinstance(type_value, str):
            # Single type
            return {"const": type_value}
        elif isinstance(type_value, list):
            if len(type_value) == 0:
                # Empty array means any type
                return {"type": "string"}
            elif len(type_value) == 1:
                return {"const": type_value[0]}
            else:
                # Multiple types - use enum
                return {"enum": type_value}
        elif self._is_empty(type_value):
            # {} means @type must be present but any value
            return {"type": "string"}

        return {"type": "string"}

    def _process_id_constraint(self, id_value: Any) -> Dict[str, Any]:
        """
        Process @id constraint from frame.

        Args:
            id_value: The @id value from the frame

        Returns:
            JSON Schema ID constraint
        """
        if isinstance(id_value, str):
            # Specific ID value
            return {"const": id_value}
        elif self._is_empty(id_value):
            # {} means @id must be present
            return {"type": "string", "format": "uri"}
        elif isinstance(id_value, dict) and "@id" in id_value:
            # Nested @id specification
            return self._process_id_constraint(id_value["@id"])

        return {"type": "string", "format": "uri"}

    def _process_property(
        self,
        key: str,
        value: Any,
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        Process a property from the frame.

        Args:
            key: Property name
            value: Property value from frame
            flags: Framing flags
            context: Type context mapping

        Returns:
            JSON Schema property definition
        """
        # Get type information from context if available
        context_type = context.get(key)

        if self._is_empty(value):
            # {} means property must be present
            return self._infer_type_from_context(key, context_type)
        elif isinstance(value, (str, int, float, bool)):
            # Literal value - use as default
            return {"type": self._infer_json_type(value), "default": value}
        elif isinstance(value, list):
            # Array frame
            return self._process_array_frame(value, flags, context)
        elif isinstance(value, dict):
            # Check if this dict has @default (but not other frame keywords)
            if "@default" in value and not ("@value" in value or "@type" in value or "@id" in value):
                # Property with default value
                schema = self._infer_type_from_context(key, context_type)
                schema["default"] = value["@default"]
                return schema
            # Check if this is a value object frame
            if "@value" in value:
                return self._process_value_object_frame(value, flags, context)
            # Nested object frame
            return self._process_nested_frame(value, flags, context)

        return {}

    def _infer_type_from_context(
        self, key: str, context_type: Optional[str]
    ) -> Dict[str, Any]:
        """
        Infer JSON Schema type from JSON-LD context type or container.

        Args:
            key: Property name
            context_type: Type from context, container spec, or None

        Returns:
            JSON Schema type definition
        """
        if context_type is None:
            return {"type": "string"}

        # Check if this is a container specification
        if context_type.startswith("@container:"):
            container_type = context_type.replace("@container:", "")
            
            if container_type == "@language":
                # Language map: allows string or object with language codes as keys
                return {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "patternProperties": {
                                "^[a-z]{2}(-[A-Z]{2})?$": {"type": "string"}
                            },
                            "additionalProperties": False,
                        },
                    ]
                }
            elif container_type == "@index":
                # Index container: object with arbitrary keys
                return {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                }
            elif container_type == "@set":
                # Set container: array with unique items
                return {"type": "array", "uniqueItems": True}
            elif container_type == "@list":
                # List container: ordered array
                return {"type": "array"}

        # Map JSON-LD types to JSON Schema types
        if context_type in self.TYPE_MAPPINGS:
            return copy.deepcopy(self.TYPE_MAPPINGS[context_type])

        return {"type": "string"}

    def _process_array_frame(
        self,
        array_value: List[Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        Process an array frame.

        Args:
            array_value: Array from frame
            flags: Framing flags
            context: Type context mapping

        Returns:
            JSON Schema array definition
        """
        if len(array_value) == 0:
            # Empty array frame
            return {"type": "array", "items": {}}

        # Process first element as item schema
        item_frame = array_value[0]
        if isinstance(item_frame, dict):
            item_schema = self._process_nested_frame(item_frame, flags, context)
        else:
            item_schema = {"type": self._infer_json_type(item_frame)}

        return {"type": "array", "items": item_schema}

    def _process_nested_frame(
        self,
        frame_obj: Dict[str, Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        Process a nested frame object.

        Args:
            frame_obj: Nested frame object
            flags: Parent framing flags
            context: Type context mapping

        Returns:
            JSON Schema nested object definition
        """
        # Extract nested framing flags (can override parent)
        nested_flags = {
            "embed": frame_obj.get("@embed", flags["embed"]),
            "explicit": frame_obj.get("@explicit", flags["explicit"]),
            "requireAll": frame_obj.get("@requireAll", flags["requireAll"]),
            "omitDefault": frame_obj.get("@omitDefault", flags["omitDefault"]),
        }

        # Check @embed flag
        embed_value = nested_flags["embed"]
        if embed_value is False or embed_value == "@never":
            # Only reference, not embedded
            return {
                "oneOf": [
                    {"type": "string", "format": "uri"},
                    {
                        "type": "object",
                        "properties": {"@id": {"type": "string", "format": "uri"}},
                        "required": ["@id"],
                        "additionalProperties": False,
                    },
                ]
            }

        # Embedded object
        nested_schema: Dict[str, Any] = {"type": "object"}
        self._process_frame_object(frame_obj, nested_schema, nested_flags, context)

        return nested_schema

    def _process_reverse_property(
        self,
        reverse_obj: Dict[str, Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        Process @reverse frame property.

        Args:
            reverse_obj: The @reverse object from the frame
            flags: Framing flags
            context: Type context mapping

        Returns:
            JSON Schema for reverse property definition
        """
        reverse_schema: Dict[str, Any] = {"type": "object", "properties": {}}

        for prop_name, prop_frame in reverse_obj.items():
            # Process the nested frame for this reverse property
            prop_schema = self._process_nested_frame(prop_frame, flags, context)

            # Allow single object or array of objects
            reverse_schema["properties"][prop_name] = {
                "oneOf": [
                    prop_schema,
                    {"type": "array", "items": prop_schema},
                ]
            }

        return reverse_schema

    def _process_value_object_frame(
        self,
        value_frame: Dict[str, Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        Process value object frame (contains @value, @language, or @type).

        Args:
            value_frame: Frame containing value object pattern
            flags: Framing flags
            context: Type context mapping

        Returns:
            JSON Schema that allows string OR value object
        """
        schemas = []

        # Allow simple string value
        schemas.append({"type": "string"})

        # Build value object schema
        value_obj_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {"@value": {}},
            "required": ["@value"],
        }

        # Handle @language constraint
        if "@language" in value_frame:
            lang = value_frame["@language"]
            if isinstance(lang, str):
                # Specific language required
                value_obj_schema["properties"]["@language"] = {"const": lang}
            elif self._is_empty(lang):
                # Any language allowed
                value_obj_schema["properties"]["@language"] = {"type": "string"}

        # Handle @type constraint for typed literals
        if "@type" in value_frame:
            type_val = value_frame["@type"]
            if isinstance(type_val, str):
                value_obj_schema["properties"]["@type"] = {"const": type_val}
            elif self._is_empty(type_val):
                value_obj_schema["properties"]["@type"] = {"type": "string"}

        schemas.append(value_obj_schema)

        return {"oneOf": schemas}

    def _should_be_required(self, key: str, value: Any, flags: Dict[str, Any]) -> bool:
        """
        Determine if a property should be required.

        Args:
            key: Property name
            value: Property value from frame
            flags: Framing flags

        Returns:
            True if property should be required
        """
        # If @requireAll is true, all properties are required
        if flags["requireAll"]:
            return True

        # If @omitDefault is true, properties are optional
        if flags["omitDefault"]:
            return False

        # If value is {}, property is required
        if self._is_empty(value):
            return True

        # For nested objects and arrays, typically required
        if isinstance(value, (dict, list)):
            return True

        return False

    def _is_empty(self, value: Any) -> bool:
        """Check if value is an empty dict."""
        return isinstance(value, dict) and len(value) == 0

    def _is_wildcard(self, value: Any) -> bool:
        """Check if value is a wildcard (empty dict or array)."""
        return self._is_empty(value) or (isinstance(value, list) and len(value) == 0)

    def _infer_json_type(self, value: Any) -> str:
        """
        Infer JSON type from a Python value.

        Args:
            value: Python value

        Returns:
            JSON type string
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        elif value is None:
            return "null"

        return "string"


def frame_to_schema(
    frame: Dict[str, Any],
    schema_version: str = "https://json-schema.org/draft/2020-12/schema",
    graph_only: bool = False,
) -> Dict[str, Any]:
    """
    Convert a JSON-LD Frame to JSON Schema.

    This is a convenience function that creates a converter and performs
    the conversion in one step.

    Args:
        frame: JSON-LD Frame object
        schema_version: JSON Schema version URI to use
        graph_only: If True, output only the schema for @graph items (without
                   @context and @graph wrapper). Default is False, which outputs
                   a full document schema with @context and @graph.

    Returns:
        JSON Schema document

    Example:
        >>> frame = {
        ...     "@type": "Person",
        ...     "name": {},
        ...     "age": {}
        ... }
        >>> schema = frame_to_schema(frame)
        >>> schema["properties"]["@graph"]["items"]["properties"]["@type"]
        {'const': 'Person'}
        >>> # For graph-only output (just the object schema):
        >>> schema = frame_to_schema(frame, graph_only=True)
        >>> schema["properties"]["@type"]
        {'const': 'Person'}
    """
    converter = FrameToSchemaConverter(
        schema_version=schema_version, graph_only=graph_only
    )
    return converter.convert(frame)
