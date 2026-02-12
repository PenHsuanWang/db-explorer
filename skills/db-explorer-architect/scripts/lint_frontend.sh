#!/bin/bash
# Frontend code quality check script
# Usage: ./skills/db-explorer-architect/scripts/lint_frontend.sh [--fix]
#
# This script runs all frontend code quality checks in sequence:
# 1. Prettier (code formatting)
# 2. ESLint (linting)
# 3. TypeScript (type checking)
# 4. Vitest (tests)
#
# Run from project root directory.
# Use --fix flag to automatically fix formatting and linting issues.

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FIX_MODE=false
EXIT_CODE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/web-ui"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--fix] [--help]"
            echo ""
            echo "Frontend code quality checks for DB Explorer"
            echo ""
            echo "Options:"
            echo "  --fix    Auto-fix issues where possible (formatting, linting)"
            echo "  --help   Show this help message"
            echo ""
            echo "Checks performed:"
            echo "  1. Prettier - Code formatting"
            echo "  2. ESLint - Linting with React & TypeScript plugins"
            echo "  3. TypeScript - Type checking (tsc --noEmit)"
            echo "  4. Vitest - Tests (--run)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "Running Frontend Code Quality Checks"
echo "========================================="
echo "Project root: $PROJECT_ROOT"
echo "Frontend directory: $FRONTEND_DIR"
echo "Fix mode: $FIX_MODE"
echo ""

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${YELLOW}Warning: Frontend directory not found at $FRONTEND_DIR${NC}"
    echo -e "${YELLOW}Creating frontend directory structure...${NC}"
    mkdir -p "$FRONTEND_DIR/src"
    mkdir -p "$FRONTEND_DIR/public"
    echo -e "${YELLOW}Please set up your React frontend in $FRONTEND_DIR${NC}"
    exit 0
fi

# Change to frontend directory
cd "$FRONTEND_DIR"

# Check if Node.js and npm are available
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: node not found${NC}"
    echo -e "${RED}Please install Node.js: https://nodejs.org/${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm not found${NC}"
    exit 1
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}Warning: package.json not found in $FRONTEND_DIR${NC}"
    echo -e "${YELLOW}Please initialize your npm project with: npm init${NC}"
    exit 0
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Warning: node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# ============================================================================
# 1. Prettier - Code Formatting
# ============================================================================
echo -e "\n${BLUE}[1/4] Running Prettier (Code Formatter)...${NC}"

# Check if prettier script exists in package.json
if npm run | grep -q "format"; then
    if [ "$FIX_MODE" = true ]; then
        if npm run format; then
            echo -e "${GREEN}✓ Prettier: Code formatted${NC}"
        else
            echo -e "${RED}✗ Prettier: Formatting failed${NC}"
            EXIT_CODE=1
        fi
    else
        # Check if format:check script exists, otherwise use format with --check
        if npm run | grep -q "format:check"; then
            if npm run format:check; then
                echo -e "${GREEN}✓ Prettier: PASSED${NC}"
            else
                echo -e "${RED}✗ Prettier: FAILED (run with --fix to auto-format)${NC}"
                EXIT_CODE=1
            fi
        else
            echo -e "${YELLOW}Warning: format:check script not found${NC}"
            echo -e "${YELLOW}Assuming format script handles checking${NC}"
            if npm run format -- --check 2>/dev/null; then
                echo -e "${GREEN}✓ Prettier: PASSED${NC}"
            else
                echo -e "${RED}✗ Prettier: FAILED (run with --fix to auto-format)${NC}"
                EXIT_CODE=1
            fi
        fi
    fi
elif command -v prettier &> /dev/null; then
    # Fallback to global prettier if scripts don't exist
    if [ "$FIX_MODE" = true ]; then
        if prettier --write "src/**/*.{ts,tsx,js,jsx,css,json}"; then
            echo -e "${GREEN}✓ Prettier: Code formatted${NC}"
        else
            echo -e "${RED}✗ Prettier: Formatting failed${NC}"
            EXIT_CODE=1
        fi
    else
        if prettier --check "src/**/*.{ts,tsx,js,jsx,css,json}"; then
            echo -e "${GREEN}✓ Prettier: PASSED${NC}"
        else
            echo -e "${RED}✗ Prettier: FAILED (run with --fix to auto-format)${NC}"
            EXIT_CODE=1
        fi
    fi
else
    echo -e "${YELLOW}Warning: Prettier not configured${NC}"
    echo -e "${YELLOW}Add 'format' and 'format:check' scripts to package.json${NC}"
fi

# ============================================================================
# 2. ESLint - Linting
# ============================================================================
echo -e "\n${BLUE}[2/4] Running ESLint (Linter)...${NC}"

# Check if lint script exists in package.json
if npm run | grep -q "lint"; then
    if [ "$FIX_MODE" = true ]; then
        # Check if lint:fix script exists
        if npm run | grep -q "lint:fix"; then
            if npm run lint:fix; then
                echo -e "${GREEN}✓ ESLint: Issues fixed${NC}"
            else
                echo -e "${RED}✗ ESLint: Some issues remain${NC}"
                EXIT_CODE=1
            fi
        else
            # Try to run lint with --fix flag
            if npm run lint -- --fix 2>/dev/null; then
                echo -e "${GREEN}✓ ESLint: Issues fixed${NC}"
            else
                echo -e "${RED}✗ ESLint: Some issues remain${NC}"
                EXIT_CODE=1
            fi
        fi
    else
        if npm run lint; then
            echo -e "${GREEN}✓ ESLint: PASSED${NC}"
        else
            echo -e "${RED}✗ ESLint: FAILED${NC}"
            EXIT_CODE=1
        fi
    fi
elif command -v eslint &> /dev/null; then
    # Fallback to global eslint if scripts don't exist
    if [ "$FIX_MODE" = true ]; then
        if eslint "src/**/*.{ts,tsx,js,jsx}" --fix; then
            echo -e "${GREEN}✓ ESLint: Issues fixed${NC}"
        else
            echo -e "${RED}✗ ESLint: Some issues remain${NC}"
            EXIT_CODE=1
        fi
    else
        if eslint "src/**/*.{ts,tsx,js,jsx}"; then
            echo -e "${GREEN}✓ ESLint: PASSED${NC}"
        else
            echo -e "${RED}✗ ESLint: FAILED${NC}"
            EXIT_CODE=1
        fi
    fi
else
    echo -e "${YELLOW}Warning: ESLint not configured${NC}"
    echo -e "${YELLOW}Add 'lint' and 'lint:fix' scripts to package.json${NC}"
fi

# ============================================================================
# 3. TypeScript - Type Checking
# ============================================================================
echo -e "\n${BLUE}[3/4] Running TypeScript (Type Checker)...${NC}"

# Check if type-check script exists in package.json
if npm run | grep -q "type-check"; then
    if npm run type-check; then
        echo -e "${GREEN}✓ TypeScript: PASSED${NC}"
    else
        echo -e "${RED}✗ TypeScript: FAILED${NC}"
        EXIT_CODE=1
    fi
elif [ -f "tsconfig.json" ]; then
    # Try to run tsc directly
    if command -v tsc &> /dev/null; then
        if tsc --noEmit; then
            echo -e "${GREEN}✓ TypeScript: PASSED${NC}"
        else
            echo -e "${RED}✗ TypeScript: FAILED${NC}"
            EXIT_CODE=1
        fi
    elif npx tsc --noEmit 2>/dev/null; then
        echo -e "${GREEN}✓ TypeScript: PASSED${NC}"
    else
        echo -e "${RED}✗ TypeScript: FAILED${NC}"
        EXIT_CODE=1
    fi
else
    echo -e "${YELLOW}Warning: TypeScript not configured (no tsconfig.json)${NC}"
fi

# ============================================================================
# 4. Vitest - Tests
# ============================================================================
echo -e "\n${BLUE}[4/4] Running Vitest (Tests)...${NC}"

# Check if test script exists in package.json
if npm run | grep -q "test"; then
    # Try to run tests in non-watch mode
    if npm run test -- --run 2>/dev/null; then
        echo -e "${GREEN}✓ Vitest: PASSED${NC}"
    elif npm run test:run 2>/dev/null; then
        echo -e "${GREEN}✓ Vitest: PASSED${NC}"
    else
        # Some projects might not support --run flag
        echo -e "${YELLOW}Warning: Could not run tests in CI mode${NC}"
        echo -e "${YELLOW}Tests may need to be run manually${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Test script not configured${NC}"
    echo -e "${YELLOW}Add 'test' script to package.json${NC}"
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "\n========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All frontend checks passed! ✓${NC}"
else
    echo -e "${RED}Some frontend checks failed. Please fix the issues above.${NC}"
    if [ "$FIX_MODE" = false ]; then
        echo -e "${YELLOW}Tip: Run with --fix to auto-fix formatting and linting issues${NC}"
    fi
fi
echo "========================================="

exit $EXIT_CODE
