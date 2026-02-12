#!/bin/bash
# Comprehensive code quality check script
# Usage: ./scripts/lint_check.sh [--fix]
#
# This script runs all code quality checks in sequence:
# 1. Black (code formatting)
# 2. isort (import sorting)
# 3. Ruff (fast linting)
# 4. Mypy (type checking)
# 5. Safety (security vulnerability check)

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
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
            echo "Options:"
            echo "  --fix    Auto-fix issues where possible (formatting, imports)"
            echo "  --help   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

echo "========================================="
echo "Running Code Quality Checks"
echo "========================================="
echo "Project root: $PROJECT_ROOT"
echo "Fix mode: $FIX_MODE"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# ============================================================================
# 1. Black - Code Formatting
# ============================================================================
echo -e "\n${BLUE}[1/5] Running Black (Code Formatter)...${NC}"

if ! command -v black &> /dev/null; then
    echo -e "${YELLOW}Warning: black not installed, skipping${NC}"
else
    if [ "$FIX_MODE" = true ]; then
        if black src/ tests/ --line-length 100; then
            echo -e "${GREEN}✓ Black: Code formatted${NC}"
        else
            echo -e "${RED}✗ Black: Formatting failed${NC}"
            EXIT_CODE=1
        fi
    else
        if black src/ tests/ --check --line-length 100; then
            echo -e "${GREEN}✓ Black: PASSED${NC}"
        else
            echo -e "${RED}✗ Black: FAILED (run with --fix to auto-format)${NC}"
            EXIT_CODE=1
        fi
    fi
fi

# ============================================================================
# 2. isort - Import Sorting
# ============================================================================
echo -e "\n${BLUE}[2/5] Running isort (Import Sorter)...${NC}"

if ! command -v isort &> /dev/null; then
    echo -e "${YELLOW}Warning: isort not installed, skipping${NC}"
else
    if [ "$FIX_MODE" = true ]; then
        if isort src/ tests/ --profile black --line-length 100; then
            echo -e "${GREEN}✓ isort: Imports sorted${NC}"
        else
            echo -e "${RED}✗ isort: Sorting failed${NC}"
            EXIT_CODE=1
        fi
    else
        if isort src/ tests/ --profile black --line-length 100 --check-only; then
            echo -e "${GREEN}✓ isort: PASSED${NC}"
        else
            echo -e "${RED}✗ isort: FAILED (run with --fix to auto-sort)${NC}"
            EXIT_CODE=1
        fi
    fi
fi

# ============================================================================
# 3. Ruff - Fast Python Linter
# ============================================================================
echo -e "\n${BLUE}[3/5] Running Ruff (Linter)...${NC}"

if ! command -v ruff &> /dev/null; then
    echo -e "${YELLOW}Warning: ruff not installed, skipping${NC}"
else
    if [ "$FIX_MODE" = true ]; then
        if ruff check src/ tests/ --fix; then
            echo -e "${GREEN}✓ Ruff: Issues fixed${NC}"
        else
            echo -e "${RED}✗ Ruff: Some issues remain${NC}"
            EXIT_CODE=1
        fi
    else
        if ruff check src/ tests/; then
            echo -e "${GREEN}✓ Ruff: PASSED${NC}"
        else
            echo -e "${RED}✗ Ruff: FAILED${NC}"
            EXIT_CODE=1
        fi
    fi
fi

# ============================================================================
# 4. Mypy - Type Checking
# ============================================================================
echo -e "\n${BLUE}[4/5] Running Mypy (Type Checker)...${NC}"

if ! command -v mypy &> /dev/null; then
    echo -e "${YELLOW}Warning: mypy not installed, skipping${NC}"
else
    # Note: mypy doesn't have auto-fix, so FIX_MODE doesn't apply
    if mypy src/ --strict --ignore-missing-imports; then
        echo -e "${GREEN}✓ Mypy: PASSED${NC}"
    else
        echo -e "${RED}✗ Mypy: FAILED${NC}"
        EXIT_CODE=1
    fi
fi

# ============================================================================
# 5. Safety - Security Vulnerability Check
# ============================================================================
echo -e "\n${BLUE}[5/5] Running Safety (Security Scanner)...${NC}"

if ! command -v safety &> /dev/null; then
    echo -e "${YELLOW}Warning: safety not installed, skipping${NC}"
else
    # Check if requirements.txt or poetry.lock exists
    if [ -f "requirements.txt" ] || [ -f "poetry.lock" ]; then
        if safety check; then
            echo -e "${GREEN}✓ Safety: PASSED${NC}"
        else
            echo -e "${YELLOW}⚠ Safety: Vulnerabilities found${NC}"
            # Don't fail build on safety warnings, just warn
            # EXIT_CODE=1
        fi
    else
        echo -e "${YELLOW}Warning: No requirements.txt or poetry.lock found, skipping${NC}"
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "\n========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    if [ "$FIX_MODE" = false ]; then
        echo -e "${YELLOW}Tip: Run with --fix to auto-fix formatting and import issues${NC}"
    fi
fi
echo "========================================="

exit $EXIT_CODE
