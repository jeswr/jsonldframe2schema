# Contributing to jsonldframe2schema

Thank you for your interest in contributing to jsonldframe2schema! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jeswr/jsonldframe2schema.git
cd jsonldframe2schema
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Run tests:
```bash
python -m pytest tests/ -v
```

## Commit Message Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated semantic versioning and changelog generation.

### Commit Message Format

Each commit message should follow this structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature (triggers **minor** version bump, e.g., 0.1.0 → 0.2.0)
- **fix**: A bug fix (triggers **patch** version bump, e.g., 0.1.0 → 0.1.1)
- **perf**: A performance improvement (triggers **patch** version bump)
- **docs**: Documentation only changes (no version bump)
- **style**: Changes that don't affect code meaning (formatting, etc.) (no version bump)
- **refactor**: Code change that neither fixes a bug nor adds a feature (no version bump)
- **test**: Adding or updating tests (no version bump)
- **build**: Changes to build system or dependencies (no version bump)
- **ci**: Changes to CI configuration (no version bump)
- **chore**: Other changes that don't modify src or test files (no version bump)
- **revert**: Reverts a previous commit (no version bump)

### Breaking Changes

To trigger a **major** version bump (e.g., 0.1.0 → 1.0.0), you can:

1. Add `!` after the type/scope:
```
feat!: change frame_to_schema return type
```

2. Add `BREAKING CHANGE:` in the footer:
```
feat: add new validation options

BREAKING CHANGE: The schema_version parameter now requires a full URI
```

### Examples

```bash
# Feature addition (minor bump)
feat: add support for JSON Schema draft-07

# Bug fix (patch bump)
fix: correct handling of null values in frames

# Performance improvement (patch bump)
perf: optimize schema generation for large frames

# Documentation update (no bump)
docs: add examples for nested object handling

# Breaking change (major bump)
feat!: redesign API to use builder pattern

BREAKING CHANGE: frame_to_schema function signature has changed.
Use FrameToSchemaConverter class instead.
```

## Pull Request Process

1. Fork the repository and create a new branch from `main`
2. Make your changes following the commit message guidelines
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Run linters:
   - `black jsonldframe2schema tests examples`
   - `flake8 jsonldframe2schema tests --max-line-length=120`
   - `mypy jsonldframe2schema --ignore-missing-imports`
5. Submit a pull request with a clear description of your changes

## Automated Releases

When commits are merged to the `main` branch:

1. Python Semantic Release analyzes commit messages
2. Determines the next version based on conventional commits
3. Updates version in `jsonldframe2schema/__init__.py`
4. Creates a git tag and GitHub release
5. Builds and publishes the package to PyPI

**Note**: Only repository maintainers can trigger releases by merging to `main`.

### Required Secrets

The release workflow requires the following secrets to be configured:

- **`RELEASE_TOKEN`**: A workflow-scoped GitHub token (PAT or GitHub App token) with `contents: write` and `id-token: write` permissions
- **`PYPI_API_TOKEN`**: A PyPI API token for publishing packages

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Include type hints where appropriate
- Add docstrings to public functions and classes

## Testing

- Write tests for new features and bug fixes
- Ensure all existing tests pass
- Aim for high test coverage

## Questions?

Feel free to open an issue for any questions or clarifications needed.
