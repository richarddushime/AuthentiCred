# API Reference Generation

This directory contains tools to automatically generate API reference documentation from the Django codebase.

## Quick Start

### Generate API Reference Documentation

```bash
# From the docs directory
./generate_refs.sh

# Or directly with Python
python generate_api_refs.py
```

### What Gets Generated

The script automatically analyzes your Django apps and generates:

- **Models**: Field definitions, types, constraints, and methods
- **Views**: Class-based and function-based views with HTTP methods
- **Forms**: Form fields, validation rules, and help text
- **App Overview**: Complete documentation for each Django app

## Files

- `generate_api_refs.py` - Main Python script for generating documentation
- `generate_refs.sh` - Shell script wrapper for easy execution
- `api/` - Directory containing generated API reference files
- `api/index.md` - Main index page linking to all app documentation

## How It Works

1. **App Discovery**: Scans `INSTALLED_APPS` in Django settings
2. **Code Analysis**: Uses Python introspection to analyze models, views, and forms
3. **Documentation Generation**: Creates markdown files with structured documentation
4. **Integration**: Automatically integrates with MkDocs navigation

## Customization

### Adding New App Types

To document additional Django components, modify the script:

```python
def analyze_admin(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze Django admin configurations."""
    # Add your custom analysis logic here
    pass
```

### Customizing Output Format

Modify the `generate_markdown()` function to change the documentation structure and styling.

## Integration with CI/CD

The API reference generation is automatically integrated with the GitHub Actions workflow:

1. **On Commit**: Documentation is automatically generated
2. **On Push to Main**: Documentation is deployed to GitHub Pages
3. **Always Up-to-Date**: API docs stay synchronized with code changes

## Requirements

- Python 3.13+
- Django 5.2.5+
- Access to Django settings and models

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Django is properly configured and apps are accessible
2. **Permission Errors**: Make sure the shell script is executable (`chmod +x generate_refs.sh`)
3. **Missing Dependencies**: Install required packages from `requirements.txt`

### Debug Mode

Add debug output to the script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new Django apps or components:

1. Add proper docstrings to your models, views, and forms
2. Test the documentation generation locally
3. Ensure the generated docs are clear and accurate
