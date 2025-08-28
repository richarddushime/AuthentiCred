#!/bin/bash

# AuthentiCred Quick Start Script
# ===============================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AuthentiCred Quick Start${NC}"
echo "=========================="

# Check if Python script exists
if [ ! -f "start_authenticred.py" ]; then
    echo -e "${RED}❌ Error: start_authenticred.py not found${NC}"
    echo "Please run this script from the AuthentiCred project directory"
    exit 1
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo -e "${GREEN}📦 Activating virtual environment...${NC}"
    source .venv/bin/activate
    
    # Verify activation
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${RED}❌ Failed to activate virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Not in virtual environment${NC}"
    exit 1
fi

# Run the Python automation script
echo -e "${BLUE}🔧 Starting AuthentiCred automation...${NC}"
echo ""

# Pass all arguments to the Python script
python start_authenticred.py "$@"

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AuthentiCred started successfully!${NC}"
else
    echo -e "${RED}❌ AuthentiCred failed to start${NC}"
    exit 1
fi
