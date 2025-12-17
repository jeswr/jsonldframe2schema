# JSON-LD Frame to Schema Playground

This is a web-based playground for converting JSON-LD 1.1 Frames to JSON Schema in real-time, running entirely in the browser.

## How It Works

The playground uses **[Pyodide](https://pyodide.org/)**, a Python distribution compiled to WebAssembly, to run the `jsonldframe2schema` converter directly in the browser without requiring a backend server.

### Architecture

1. **Pyodide Runtime**: Loads Python interpreter in WebAssembly
2. **Dependencies**: Automatically installs `pyld` and `jsonschema` using micropip
3. **Converter Code**: The entire `FrameToSchemaConverter` class is embedded in the HTML
4. **Real-time Conversion**: Input changes trigger conversion with 500ms debouncing

### Features

- ✅ **100% Client-Side**: No server needed, runs entirely in browser
- ✅ **Real-time Conversion**: See results as you type
- ✅ **6 Built-in Examples**: Quick-start templates for common use cases
- ✅ **Copy to Clipboard**: One-click copy of generated schema
- ✅ **Error Handling**: Clear error messages for invalid input
- ✅ **Responsive Design**: Works on desktop and mobile devices

## File Structure

```
playground/
├── index.html          # Main playground page (self-contained)
└── README.md          # This file
```

## Usage

The playground is deployed at: https://jeswr.github.io/jsonldframe2schema/playground/

To run locally:

```bash
# Serve the playground directory with any HTTP server
cd playground
python3 -m http.server 8080

# Open http://localhost:8080 in your browser
```

**Note**: The playground requires loading external resources (Pyodide CDN), so it must be served over HTTP/HTTPS, not opened directly as a file.

## Examples Included

1. **Basic Person**: Simple frame with typed properties
2. **Nested Address**: Nested object structures
3. **Array of Friends**: Array handling
4. **Explicit Mode**: Using `@explicit` flag
5. **Typed Properties**: XSD type coercion
6. **Non-Embedded Reference**: Using `@embed: false`

## Technical Details

### Dependencies Loaded

- **Pyodide**: v0.24.1 (Python 3.11 in WebAssembly)
- **pyld**: Latest version from PyPI
- **jsonschema**: Latest version from PyPI

### Performance

- Initial load: ~3-5 seconds (loading Pyodide and dependencies)
- Conversion: ~50-200ms depending on frame complexity
- Debounce delay: 500ms after typing stops

### Browser Compatibility

Works in all modern browsers that support:
- WebAssembly
- ES6 JavaScript
- Async/await

Tested on:
- Chrome/Edge 90+
- Firefox 89+
- Safari 14+

## Development

The playground is a single self-contained HTML file for easy deployment and maintenance. To modify:

1. Edit `index.html`
2. Test locally with an HTTP server
3. Run end-to-end tests: `python tests/test_playground_e2e.py`
4. Commit changes - GitHub Actions will deploy automatically

### Updating the Converter Code

The Python converter code is embedded in the HTML within a `<script>` tag. When updating the main library, the embedded code should be updated to match.

## Testing

The playground includes comprehensive end-to-end tests that verify:
- HTML structure and accessibility
- JavaScript functions and event handlers
- Embedded Python converter code
- Error handling and user feedback

See [TESTING.md](TESTING.md) for details on why the playground appears to fail in sandboxed environments but works correctly in production.

```bash
# Run tests
python tests/test_playground_e2e.py

# Or with pytest
pytest tests/test_playground_e2e.py -v
```

## Deployment

The playground is automatically deployed to GitHub Pages via the `.github/workflows/pages.yml` workflow whenever changes are pushed to the `main` branch.

## License

MIT License - Same as the main project
