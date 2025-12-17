# JSON-LD Frame to JSON Schema Algorithm Specification

This directory contains the formal specification for the JSON-LD Frame to JSON Schema conversion algorithm, written using [ReSpec](https://respec.org/).

## Viewing the Specification

### Online (GitHub Pages)

The specification is automatically deployed to GitHub Pages and can be viewed at:
**https://jeswr.github.io/jsonldframe2schema/spec/**

### Locally

To view the specification locally:

1. Start a local web server in this directory:
   ```bash
   python -m http.server 8000
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/index.html
   ```

The ReSpec script will automatically format the specification with proper W3C styling.

## Structure

- `index.html` - The main ReSpec specification document

## Building and Deployment

The specification is automatically deployed to GitHub Pages via the `.github/workflows/pages.yml` workflow whenever changes are pushed to the main branch.

No build step is required - ReSpec processes the specification client-side in the browser.

## Contributing

To make changes to the specification:

1. Edit `index.html`
2. Test locally using a web server
3. Commit and push changes
4. The specification will be automatically deployed

## References

This specification follows the structure and conventions used by other W3C specifications:

- [W3C RDF Dataset Canonicalization](https://w3c.github.io/rdf-canon/spec/)
- [W3C JSON-LD 1.1 Processing Algorithms and API](https://w3c.github.io/json-ld-api/)
- [ReSpec Documentation](https://respec.org/docs/)
