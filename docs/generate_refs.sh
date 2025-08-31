#!/bin/bash

# Generate API Reference Documentation
# This script runs the Python script to generate API reference pages

echo "Generating API Reference Documentation..."

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Run the Python script
python generate_api_refs.py

echo "API Reference generation complete!"
echo "Check the docs/api/ directory for generated files."
