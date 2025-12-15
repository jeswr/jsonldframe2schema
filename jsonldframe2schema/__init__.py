"""
jsonldframe2schema - Convert JSON-LD Frames to JSON Schema

This package provides functionality to convert JSON-LD 1.1 Frames into
JSON Schema documents for validation purposes.
"""

__version__ = "0.1.0"
__author__ = "Jesse Wright"

from .converter import FrameToSchemaConverter, frame_to_schema
from .cli import main as cli_main

__all__ = ["FrameToSchemaConverter", "frame_to_schema", "cli_main"]
