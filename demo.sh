#!/bin/bash

# AI Governance Tool - Demo Script
# Demonstrates security controls and features

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}AI Governance Tool - Interactive Demo${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Check if installed
if ! command -v ai-governance &> /dev/null; then
    echo -e "${YELLOW}Installing ai-governance tool...${NC}"
    pip install -e . > /dev/null 2>&1
    echo -e "${GREEN}✅ Installation complete${NC}"
    echo ""
fi

# Run Python demo script
echo -e "${CYAN}Running security scanning demo...${NC}"
echo ""
python demo.py

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}Demo Complete!${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Offer to run interactive examples
echo -e "${YELLOW}Would you like to try interactive refactoring? (requires API key)${NC}"
echo -e "Press Enter to skip, or type 'yes' to continue..."
read -r response

if [ "$response" = "yes" ] || [ "$response" = "y" ]; then
    # Check for API key
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}ANTHROPIC_API_KEY not set. Please set it in .env or environment.${NC}"
        exit 1
    fi

    echo ""
    echo -e "${CYAN}Attempting to refactor a clean file (should succeed)...${NC}"
    echo ""
    ai-governance refactor demo/legacy_code/utils.py --target "add type hints and modernize to Python 3.10+" --dry-run

    echo ""
    echo -e "${CYAN}Attempting to refactor a blocked file (should fail)...${NC}"
    echo ""
    ai-governance refactor demo/legacy_code/user_service.py --target "refactor to FastAPI async" --dry-run

    echo ""
    echo -e "${GREEN}View full audit logs with: ai-governance audit${NC}"
fi

echo ""
echo -e "${GREEN}Demo script complete! Check README.md for more information.${NC}"
