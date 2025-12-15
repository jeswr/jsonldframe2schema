#!/usr/bin/env python3
"""
Command-line interface for jsonldframe2schema.

Usage:
    python -m jsonldframe2schema.cli <input_frame.json> [output_schema.json]
    cat frame.json | python -m jsonldframe2schema.cli
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from .converter import frame_to_schema


def main(argv: Optional[list] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        argv: Command-line arguments (default: sys.argv)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Convert JSON-LD Frames to JSON Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert frame from file and print to stdout
  %(prog)s frame.json
  
  # Convert frame and save to file
  %(prog)s frame.json schema.json
  
  # Read from stdin and write to stdout
  cat frame.json | %(prog)s
        """
    )
    
    parser.add_argument(
        "input",
        nargs="?",
        help="Input JSON-LD Frame file (default: stdin)"
    )
    
    parser.add_argument(
        "output",
        nargs="?",
        help="Output JSON Schema file (default: stdout)"
    )
    
    parser.add_argument(
        "--schema-version",
        default="https://json-schema.org/draft/2020-12/schema",
        help="JSON Schema version URI (default: draft 2020-12)"
    )
    
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation (default: 2)"
    )
    
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON (no indentation)"
    )
    
    args = parser.parse_args(argv)
    
    # Determine output file
    output_file = args.output
    
    try:
        # Read input frame
        if args.input:
            with open(args.input, 'r') as f:
                frame = json.load(f)
        else:
            # Read from stdin
            frame = json.load(sys.stdin)
        
        # Convert to schema
        schema = frame_to_schema(frame, schema_version=args.schema_version)
        
        # Format output
        indent = None if args.compact else args.indent
        schema_json = json.dumps(schema, indent=indent)
        
        # Write output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(schema_json)
                f.write('\n')
            print(f"Schema written to {output_file}", file=sys.stderr)
        else:
            print(schema_json)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
