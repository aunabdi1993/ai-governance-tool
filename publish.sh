#!/bin/bash
set -e

# AI Governance Tool - PyPI Publishing Script
# Usage:
#   ./publish.sh        - Publish to PyPI (production)
#   ./publish.sh test   - Publish to TestPyPI (testing)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine target
if [ "$1" == "test" ]; then
    TARGET="testpypi"
    TARGET_NAME="TestPyPI"
    TARGET_URL="https://test.pypi.org/simple/"
else
    TARGET="pypi"
    TARGET_NAME="PyPI"
    TARGET_URL="https://pypi.org/simple/"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Governance Tool - Publishing to $TARGET_NAME${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Get current version
VERSION=$(grep "__version__" ai_governance/__init__.py | cut -d'"' -f2)
echo -e "${YELLOW}Current version: $VERSION${NC}"
echo

# Confirm
read -p "Publish version $VERSION to $TARGET_NAME? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted.${NC}"
    exit 1
fi

# Step 1: Clean old builds
echo -e "${BLUE}[1/5] Cleaning old builds...${NC}"
rm -rf dist/ build/ *.egg-info
echo -e "${GREEN}✓ Cleaned${NC}"
echo

# Step 2: Check if required tools are installed
echo -e "${BLUE}[2/5] Checking required tools...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: python not found${NC}"
    exit 1
fi

if ! python -c "import build" &> /dev/null; then
    echo -e "${YELLOW}Installing build...${NC}"
    pip install --upgrade build
fi

if ! python -c "import twine" &> /dev/null; then
    echo -e "${YELLOW}Installing twine...${NC}"
    pip install --upgrade twine
fi
echo -e "${GREEN}✓ Tools ready${NC}"
echo

# Step 3: Build distribution packages
echo -e "${BLUE}[3/5] Building distribution packages...${NC}"
python -m build
echo -e "${GREEN}✓ Built${NC}"
echo

# Step 4: Check packages
echo -e "${BLUE}[4/5] Checking packages...${NC}"
python -m twine check dist/*
echo -e "${GREEN}✓ Packages OK${NC}"
echo

# Step 5: Upload to PyPI/TestPyPI
echo -e "${BLUE}[5/5] Uploading to $TARGET_NAME...${NC}"
if [ "$TARGET" == "testpypi" ]; then
    python -m twine upload --repository testpypi dist/*
else
    python -m twine upload dist/*
fi
echo -e "${GREEN}✓ Uploaded${NC}"
echo

# Success message
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Successfully published version $VERSION to $TARGET_NAME!${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Show installation command
if [ "$TARGET" == "testpypi" ]; then
    echo -e "${YELLOW}Test installation with:${NC}"
    echo -e "pip install --index-url https://test.pypi.org/simple/ --no-deps ai-governance"
else
    echo -e "${YELLOW}Users can now install with:${NC}"
    echo -e "pip install ai-governance"
    echo -e "  or"
    echo -e "pipx install ai-governance"
    echo
    echo -e "${YELLOW}Don't forget to:${NC}"
    echo "1. Create a git tag: git tag v$VERSION && git push origin v$VERSION"
    echo "2. Create a GitHub release with release notes"
fi
echo
