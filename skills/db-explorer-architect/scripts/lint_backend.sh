#!/bin/bash
# Backend code quality check script
# Usage: ./skills/db-explorer-architect/scripts/lint_backend.sh [--fix]
#
# This script runs all backend code quality checks in sequence:
# 1. Black (code formatting)
# 2. isort (import sorting)
# 3. Mypy (type checking)
# 4. Ruff (linting)
# 5. Pytest (tests with coverage)
#
# Run from project root directory.
# Use --fix flag to automatically fix formatting and import issues.

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
BACKEND_DIR="$PROJECT_ROOT/backend"

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
            echo "Backend code quality checks for DB Explorer"
            echo ""
            echo "Options:"
            echo "  --fix    Auto-fix issues where possible (formatting, imports)"
            echo "  --help   Show this help message"
            echo ""
            echo "Checks performed:"
            echo "  1. Black - Code formatting (line-length 100)"
            echo "  2. isort - Import sorting (--profile black)"
            echo "  3. Mypy - Type checking (--strict)"
            echo "  4. Ruff - Fast linting"
            echo "  5. Pytest - Tests with coverage (--cov=src --cov-report=term-missing)"
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
echo "Running Backend Code Quality Checks"
echo "========================================="
echo "Project root: $PROJECT_ROOT"
echo "Backend directory: $BACKEND_DIR"
echo "Fix mode: $FIX_MODE"
echo ""

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${YELLOW}Warning: Backend directory not found at $BACKEND_DIR${NC}"
    echo -e "${YELLOW}Creating backend directory structure...${NC}"
    mkdir -p "$BACKEND_DIR/src"
    mkdir -p "$BACKEND_DIR/tests"
    echo -e "${YELLOW}Please set up your Python backend in $BACKEND_DIR${NC}"
    exit 0
fi

# Change to backend directory
cd "$BACKEND_DIR"

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
    echo -e "${YELLOW}Install with: pip install black${NC}"
else
    if [ -d "src" ] || [ -d "tests" ]; then
        TARGETS=""
        [ -d "src" ] && TARGETS="$TARGETS src/"
        [ -d "tests" ] && TARGETS="$TARGETS tests/"
        
        if [ "$FIX_MODE" = true ]; then
            if black $TARGETS --line-length 100; then
                echo -e "${GREEN}✓ Black: Code formatted${NC}"
            else
                echo -e "${RED}✗ Black: Formatting failed${NC}"
                EXIT_CODE=1
            fi
        else
            if black $TARGETS --check --line-length 100; then
                echo -e "${GREEN}✓ Black: PASSED${NC}"
            else
                echo -e "${RED}✗ Black: FAILED (run with --fix to auto-format)${NC}"
                EXIT_CODE=1
            fi
        fi
    else
        echo -e "${YELLOW}Warning: No src/ or tests/ directories found${NC}"
    fi
fi

# ============================================================================
# 2. isort - Import Sorting
# ============================================================================
echo -e "\n${BLUE}[2/5] Running isort (Import Sorter)...${NC}"

if ! command -v isort &> /dev/null; then
    echo -e "${YELLOW}Warning: isort not installed, skipping${NC}"
    echo -e "${YELLOW}Install with: pip install isort${NC}"
else
    if [ -d "src" ] || [ -d "tests" ]; then
        TARGETS=""
        [ -d "src" ] && TARGETS="$TARGETS src/"
        [ -d "tests" ] && TARGETS="$TARGETS tests/"
        
        if [ "$FIX_MODE" = true ]; then
            if isort $TARGETS --profile black --line-length 100; then
                echo -e "${GREEN}✓ isort: Imports sorted${NC}"
            else
                echo -e "${RED}✗ isort: Sorting failed${NC}"
                EXIT_CODE=1
            fi
        else
            if isort $TARGETS --profile black --line-length 100 --check-only; then
                echo -e "${GREEN}✓ isort: PASSED${NC}"
            else
                echo -e "${RED}✗ isort: FAILED (run with --fix to auto-sort)${NC}"
                EXIT_CODE=1
            fi
        fi
    else
        echo -e "${YELLOW}Warning: No src/ or tests/ directories found${NC}"
    fi
fi

# ============================================================================
# 3. Mypy - Type Checking
# ============================================================================
echo -e "\n${BLUE}[3/5] Running Mypy (Type Checker)...${NC}"

if ! command -v mypy &> /dev/null; then
    echo -e "${YELLOW}Warning: mypy not installed, skipping${NC}"
    echo -e "${YELLOW}Install with: pip install mypy${NC}"
else
    # Note: mypy doesn't have auto-fix, so FIX_MODE doesn't apply
    if [ -d "src" ]; then
        if mypy src/ --strict --ignore-missing-imports; then
            echo -e "${GREEN}✓ Mypy: PASSED${NC}"
        else
            echo -e "${RED}✗ Mypy: FAILED${NC}"
            EXIT_CODE=1
        fi
    else
        echo -e "${YELLOW}Warning: No src/ directory found${NC}"
    fi
fi

# ============================================================================
# 4. Ruff - Fast Python Linter
# ============================================================================
echo -e "\n${BLUE}[4/5] Running Ruff (Linter)...${NC}"

if ! command -v ruff &> /dev/null; then
    echo -e "${YELLOW}Warning: ruff not installed, skipping${NC}"
    echo -e "${YELLOW}Install with: pip install ruff${NC}"
else
    if [ -d "src" ] || [ -d "tests" ]; then
        TARGETS=""
        [ -d "src" ] && TARGETS="$TARGETS src/"
        [ -d "tests" ] && TARGETS="$TARGETS tests/"
        
        if [ "$FIX_MODE" = true ]; then
            if ruff check $TARGETS --fix; then
                echo -e "${GREEN}✓ Ruff: Issues fixed${NC}"
            else
                echo -e "${RED}✗ Ruff: Some issues remain${NC}"
                EXIT_CODE=1
            fi
        else
            if ruff check $TARGETS; then
                echo -e "${GREEN}✓ Ruff: PASSED${NC}"
            else
                echo -e "${RED}✗ Ruff: FAILED${NC}"
                EXIT_CODE=1
            fi
        fi
    else
        echo -e "${YELLOW}Warning: No src/ or tests/ directories found${NC}"
    fi
fi

# ============================================================================
# 5. Pytest - Tests with Coverage
# ============================================================================
echo -e "\n${BLUE}[5/5] Running Pytest (Tests with Coverage)...${NC}"

if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}Warning: pytest not installed, skipping${NC}"
    echo -e "${YELLOW}Install with: pip install pytest pytest-cov${NC}"
else
    if [ -d "tests" ]; then
        if pytest tests/ --cov=src --cov-report=term-missing; then
            echo -e "${GREEN}✓ Pytest: PASSED${NC}"
        else
            echo -e "${RED}✗ Pytest: FAILED${NC}"
            EXIT_CODE=1
        fi
    else
        echo -e "${YELLOW}Warning: No tests/ directory found${NC}"
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "\n========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All backend checks passed! ✓${NC}"
else
    echo -e "${RED}Some backend checks failed. Please fix the issues above.${NC}"
    if [ "$FIX_MODE" = false ]; then
        echo -e "${YELLOW}Tip: Run with --fix to auto-fix formatting and import issues${NC}"
    fi
fi
echo "========================================="

exit $EXIT_CODE
