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
    
    # JSON-LD to JSON Schema type mappings (using expanded URIs only)
    # These mappings use the full URIs that pyld expands to
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
        "http://www.w3.org/2001/XMLSchema#dateTime": {"type": "string", "format": "date-time"},
        "http://www.w3.org/2001/XMLSchema#date": {"type": "string", "format": "date"},
        "http://www.w3.org/2001/XMLSchema#time": {"type": "string", "format": "time"},
    }
    
    FRAMING_KEYWORDS = {
        "@context", "@embed", "@explicit", "@requireAll", 
        "@omitDefault", "@graph", "@reverse"
    }
    
    def __init__(self, schema_version: str = "https://json-schema.org/draft/2020-12/schema"):
        """
        Initialize the converter.
        
        Args:
            schema_version: JSON Schema version URI to use in output
        """
        self.schema_version = schema_version
    
    def convert(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a JSON-LD Frame to JSON Schema.
        
        Args:
            frame: JSON-LD Frame object
            
        Returns:
            JSON Schema document
        """
        schema: Dict[str, Any] = {
            "$schema": self.schema_version,
            "type": "object"
        }
        
        # Extract global framing flags
        flags = self._extract_framing_flags(frame)
        
        # Extract context for type information
        context = self._extract_context(frame)
        
        # Process the main frame object
        self._process_frame_object(frame, schema, flags, context)
        
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
        Extract type information from @context.
        
        Args:
            frame: JSON-LD Frame object
            
        Returns:
            Dictionary mapping property names to their type URIs
        """
        context = frame.get("@context")
        if not context:
            return {}
        
        return self._parse_context(context)
    
    def _parse_context(self, context: Union[str, Dict, List]) -> Dict[str, Optional[str]]:
        """
        Parse JSON-LD context to extract type coercion information using pyld.
        
        This method uses pyld to properly expand the context, handling custom
        prefixes and namespaces correctly. It automatically adds common prefixes
        like 'xsd' if they are used but not defined.
        
        Args:
            context: JSON-LD context (string, dict, or list)
            
        Returns:
            Dictionary mapping property names to their expanded type URIs
        """
        type_map: Dict[str, Optional[str]] = {}
        
        if not context:
            return type_map
        
        try:
            # Ensure context is a dict we can work with
            working_context = context
            
            # If it's a dict, check if we need to add common prefixes
            if isinstance(context, dict):
                # Check if xsd prefix is used but not defined
                needs_xsd = False
                for key, value in context.items():
                    if isinstance(value, dict) and "@type" in value:
                        type_val = value["@type"]
                        if isinstance(type_val, str) and type_val.startswith("xsd:"):
                            if "xsd" not in context:
                                needs_xsd = True
                                break
                
                # Add xsd prefix if needed
                if needs_xsd:
                    working_context = copy.deepcopy(context)
                    working_context["xsd"] = "http://www.w3.org/2001/XMLSchema#"
            
            # Process the context
            if isinstance(working_context, dict):
                for key, value in working_context.items():
                    if key in ("@vocab", "@base", "@language", "@version", "xsd", "rdf", "rdfs"):
                        continue
                    
                    # Check if this property has type coercion defined
                    if isinstance(value, dict) and "@type" in value:
                        # Create a test document with this property
                        prop_doc = {
                            "@context": working_context,
                            key: "test_value"
                        }
                        
                        try:
                            # Expand to get the full URI for the type
                            expanded = jsonld.expand(prop_doc)
                            if expanded and len(expanded) > 0:
                                # Find the property in the expanded document
                                for prop_uri, prop_values in expanded[0].items():
                                    if prop_uri.startswith("@"):
                                        continue
                                    # Check if the value has type information
                                    if prop_values and isinstance(prop_values, list) and len(prop_values) > 0:
                                        if isinstance(prop_values[0], dict) and "@type" in prop_values[0]:
                                            # Store the expanded type URI
                                            type_map[key] = prop_values[0]["@type"]
                        except (jsonld.JsonLdError, ValueError, TypeError):
                            # If expansion fails for this property, fall back to storing None
                            type_map[key] = None
                    elif isinstance(value, str):
                        # Simple string mapping, no type info
                        type_map[key] = None
            elif isinstance(working_context, list):
                # Process each context in the array
                for ctx in working_context:
                    type_map.update(self._parse_context(ctx))
        except (jsonld.JsonLdError, ValueError, TypeError, KeyError):
            # If context processing fails entirely, return empty type map
            # This handles malformed contexts gracefully
            pass
        
        return type_map
    
    def _process_frame_object(
        self, 
        frame: Dict[str, Any], 
        schema: Dict[str, Any], 
        flags: Dict[str, Any], 
        context: Dict[str, Optional[str]]
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
        context: Dict[str, Optional[str]]
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
            return {
                "type": self._infer_json_type(value),
                "default": value
            }
        elif isinstance(value, list):
            # Array frame
            return self._process_array_frame(value, flags, context)
        elif isinstance(value, dict):
            # Nested object frame
            return self._process_nested_frame(value, flags, context)
        
        return {}
    
    def _infer_type_from_context(
        self, 
        key: str, 
        context_type: Optional[str]
    ) -> Dict[str, Any]:
        """
        Infer JSON Schema type from JSON-LD context type.
        
        Args:
            key: Property name
            context_type: Type from context or None
            
        Returns:
            JSON Schema type definition
        """
        if context_type is None:
            return {"type": "string"}
        
        # Map JSON-LD types to JSON Schema types
        if context_type in self.TYPE_MAPPINGS:
            return copy.deepcopy(self.TYPE_MAPPINGS[context_type])
        
        return {"type": "string"}
    
    def _process_array_frame(
        self,
        array_value: List[Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]]
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
            return {
                "type": "array",
                "items": {}
            }
        
        # Process first element as item schema
        item_frame = array_value[0]
        if isinstance(item_frame, dict):
            item_schema = self._process_nested_frame(item_frame, flags, context)
        else:
            item_schema = {
                "type": self._infer_json_type(item_frame)
            }
        
        return {
            "type": "array",
            "items": item_schema
        }
    
    def _process_nested_frame(
        self,
        frame_obj: Dict[str, Any],
        flags: Dict[str, Any],
        context: Dict[str, Optional[str]]
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
                        "properties": {
                            "@id": {"type": "string", "format": "uri"}
                        },
                        "required": ["@id"],
                        "additionalProperties": False
                    }
                ]
            }
        
        # Embedded object
        nested_schema: Dict[str, Any] = {"type": "object"}
        self._process_frame_object(frame_obj, nested_schema, nested_flags, context)
        
        return nested_schema
    
    def _should_be_required(
        self, 
        key: str, 
        value: Any, 
        flags: Dict[str, Any]
    ) -> bool:
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
    schema_version: str = "https://json-schema.org/draft/2020-12/schema"
) -> Dict[str, Any]:
    """
    Convert a JSON-LD Frame to JSON Schema.
    
    This is a convenience function that creates a converter and performs
    the conversion in one step.
    
    Args:
        frame: JSON-LD Frame object
        schema_version: JSON Schema version URI to use
        
    Returns:
        JSON Schema document
        
    Example:
        >>> frame = {
        ...     "@type": "Person",
        ...     "name": {},
        ...     "age": {}
        ... }
        >>> schema = frame_to_schema(frame)
        >>> schema["type"]
        'object'
    """
    converter = FrameToSchemaConverter(schema_version=schema_version)
    return converter.convert(frame)
