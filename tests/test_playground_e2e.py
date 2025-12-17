#!/usr/bin/env python3
"""
End-to-end test for the web playground.

This test validates that the playground HTML structure is correct,
all JavaScript functions are defined, and the UI elements are accessible.
"""

import os
import re
import unittest
from pathlib import Path


class TestPlaygroundE2E(unittest.TestCase):
    """End-to-end tests for the web playground."""

    @classmethod
    def setUpClass(cls):
        """Load the playground HTML file."""
        playground_path = Path(__file__).parent.parent / "playground" / "index.html"
        with open(playground_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

    def test_html_structure_valid(self):
        """Test that the HTML has proper structure."""
        # Check for required meta tags
        self.assertIn('<meta charset="UTF-8">', self.html_content)
        self.assertIn('<meta name="viewport"', self.html_content)
        
        # Check for title
        self.assertIn('<title>JSON-LD Frame to Schema Playground</title>', self.html_content)
        
        # Check for main header
        self.assertIn('<h1>JSON-LD Frame to Schema Playground</h1>', self.html_content)

    def test_accessibility_attributes_present(self):
        """Test that accessibility attributes are present."""
        # Check textareas have aria-label
        self.assertIn('aria-label="JSON-LD Frame input"', self.html_content)
        self.assertIn('aria-label="JSON Schema output"', self.html_content)
        
        # Check status element has proper ARIA attributes
        self.assertIn('role="status"', self.html_content)
        self.assertIn('aria-live="polite"', self.html_content)

    def test_required_ui_elements_present(self):
        """Test that all required UI elements are present."""
        # Check for input textarea
        self.assertIn('id="frameInput"', self.html_content)
        
        # Check for output textarea
        self.assertIn('id="schemaOutput"', self.html_content)
        
        # Check for example selector
        self.assertIn('id="exampleSelect"', self.html_content)
        
        # Check for copy button
        self.assertIn('id="copyBtn"', self.html_content)
        
        # Check for status indicator
        self.assertIn('id="status"', self.html_content)

    def test_pyodide_script_tag_present(self):
        """Test that Pyodide script is loaded."""
        # Check for Pyodide CDN script
        self.assertIn('pyodide/v0.26.4/full/pyodide.js', self.html_content)
        
        # Check for crossorigin attribute for security
        self.assertIn('crossorigin="anonymous"', self.html_content)

    def test_example_frames_defined(self):
        """Test that example frames are defined in JavaScript."""
        # Check for examples object
        self.assertIn('const examples = {', self.html_content)
        
        # Check for specific examples
        required_examples = ['basic', 'nested', 'array', 'explicit', 'typed', 'embed']
        for example in required_examples:
            self.assertIn(f'{example}:', self.html_content)

    def test_javascript_functions_defined(self):
        """Test that required JavaScript functions are defined."""
        required_functions = [
            'initPyodide',
            'convertFrame',
            'loadExample',
            'setStatus',
        ]
        
        for func in required_functions:
            # Check for function definition (async or regular)
            pattern = f'(async )?function {func}|{func} = (async )?function|(async )?{func} ='
            self.assertTrue(
                re.search(pattern, self.html_content),
                f"Function '{func}' not found in HTML"
            )

    def test_python_converter_class_embedded(self):
        """Test that the Python converter class is embedded."""
        # Check for FrameToSchemaConverter class
        self.assertIn('class FrameToSchemaConverter:', self.html_content)
        
        # Check for key methods
        required_methods = [
            'def convert',
            'def _extract_framing_flags',
            'def _process_frame_object',
            'def _process_property',
        ]
        
        for method in required_methods:
            self.assertIn(method, self.html_content)

    def test_error_handling_present(self):
        """Test that error handling is implemented."""
        # Check for Exception handling (not bare except)
        self.assertIn('except Exception:', self.html_content)
        
        # Check for copy failure feedback
        self.assertIn("'Failed to copy'", self.html_content)

    def test_event_listeners_attached(self):
        """Test that event listeners are attached to UI elements."""
        # Check for input event listener (debounced)
        self.assertIn("frameInput.addEventListener('input'", self.html_content)
        
        # Check for example selector change listener
        self.assertIn("exampleSelect.addEventListener('change'", self.html_content)
        
        # Check for copy button click listener
        self.assertIn("copyBtn.addEventListener('click'", self.html_content)

    def test_css_styles_present(self):
        """Test that CSS styles are defined."""
        # Check for basic styles
        self.assertIn('<style>', self.html_content)
        self.assertIn('</style>', self.html_content)
        
        # Check for responsive design
        self.assertIn('@media', self.html_content)

    def test_no_inline_event_handlers(self):
        """Test that no inline event handlers are used (security best practice)."""
        # Check for common inline handlers
        inline_handlers = ['onclick=', 'onload=', 'onerror=', 'onchange=']
        
        for handler in inline_handlers:
            self.assertNotIn(handler, self.html_content.lower(),
                           f"Inline event handler '{handler}' found (security risk)")

    def test_conversion_function_structure(self):
        """Test that the conversion function has proper structure."""
        # Check for frame_to_schema Python function
        self.assertIn('def frame_to_schema(', self.html_content)
        
        # Check for convert_frame_to_schema wrapper
        self.assertIn('def convert_frame_to_schema(', self.html_content)
        
        # Check for graph_only parameter with comment
        self.assertIn('graph_only=True', self.html_content)

    def test_footer_links_present(self):
        """Test that footer links are present."""
        # Check for GitHub repository link
        self.assertIn('github.com/jeswr/jsonldframe2schema', self.html_content)
        
        # Check for MAPPING.md link
        self.assertIn('MAPPING.md', self.html_content)
        
        # Check for ALGORITHM.md link
        self.assertIn('ALGORITHM.md', self.html_content)


class TestDocsIndexE2E(unittest.TestCase):
    """End-to-end tests for the docs landing page."""

    @classmethod
    def setUpClass(cls):
        """Load the docs index HTML file."""
        docs_path = Path(__file__).parent.parent / "docs" / "index.html"
        with open(docs_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

    def test_landing_page_structure(self):
        """Test that the landing page has proper structure."""
        # Check for title
        self.assertIn('jsonldframe2schema', self.html_content)
        
        # Check for main heading
        self.assertIn('<h1>jsonldframe2schema</h1>', self.html_content)

    def test_card_links_present(self):
        """Test that card links to playground and spec are present."""
        # Check for playground link
        self.assertIn('href="playground/"', self.html_content)
        
        # Check for spec link
        self.assertIn('href="spec/"', self.html_content)

    def test_card_accessibility(self):
        """Test that cards have proper accessibility attributes."""
        # Check for aria-label on playground card
        self.assertIn('aria-label="Open Web Playground"', self.html_content)
        
        # Check for aria-label on spec card
        self.assertIn('aria-label="Open Specification"', self.html_content)


def run_tests():
    """Run all end-to-end tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPlaygroundE2E))
    suite.addTests(loader.loadTestsFromTestCase(TestDocsIndexE2E))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
