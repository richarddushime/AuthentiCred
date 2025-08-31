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
if [ ! -f "authenticred_setup.py" ]; then
    echo -e "${RED}❌ Error: authenticred_setup.py not found${NC}"
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
python authenticred_setup.py "$@"

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AuthentiCred started successfully!${NC}"
    
    # Start MkDocs documentation server
    echo -e "${BLUE}📚 Starting MkDocs documentation server...${NC}"
    
    # Check if MkDocs is installed
    if ! command -v mkdocs &> /dev/null; then
        echo -e "${YELLOW}⚠️  MkDocs not found, installing...${NC}"
        pip install mkdocs mkdocs-material
    fi
    
    # Check if mkdocs.yml exists
    if [ -f "mkdocs.yml" ]; then
        echo -e "${GREEN}📖 Found mkdocs.yml configuration${NC}"
        
        # Generate API references first
        echo -e "${BLUE}🔧 Generating API references...${NC}"
        cd docs
        python generate_api_refs.py
        cd ..
        
        # Start MkDocs server in background
        echo -e "${GREEN}🚀 Starting MkDocs server on http://localhost:8080${NC}"
        echo -e "${BLUE}📖 Documentation will be available at: http://localhost:8080${NC}"
        echo -e "${YELLOW}💡 Press Ctrl+C to stop all services${NC}"
        
        # Start MkDocs in background and capture PID
        mkdocs serve -a 0.0.0.0:8080 &
        MKDOCS_PID=$!
        
        # Save PID to file for easy stopping
        echo $MKDOCS_PID > .mkdocs.pid
        
        echo -e "${GREEN}✅ MkDocs started with PID: $MKDOCS_PID${NC}"
        echo -e "${BLUE}📚 Documentation server is running in background${NC}"
        
    else
        echo -e "${YELLOW}⚠️  mkdocs.yml not found, skipping documentation server${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 All services are now running!${NC}"
    echo -e "${BLUE}🌐 Django App: http://localhost:8000${NC}"
    echo -e "${BLUE}📚 Documentation: http://localhost:8080${NC}"
    echo -e "${BLUE}🔗 Ganache: http://localhost:8545${NC}"
    echo ""
    echo -e "${YELLOW}💡 To stop all services, press Ctrl+C${NC}"
    echo -e "${YELLOW}💡 To stop only MkDocs: kill \$(cat .mkdocs.pid)${NC}"
    
else
    echo -e "${RED}❌ AuthentiCred failed to start${NC}"
    exit 1
fi
