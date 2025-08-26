#!/bin/bash

# AuthentiCred Quick Start Script
# ===============================

echo "🚀 AuthentiCred Quick Start"
echo "=========================="

# Check if Python script exists
if [ ! -f "start_authenticred.py" ]; then
    echo "❌ Error: start_authenticred.py not found"
    echo "Please run this script from the AuthentiCred project directory"
    exit 1
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the Python automation script
echo "🔧 Starting AuthentiCred automation..."
python start_authenticred.py "$@"
