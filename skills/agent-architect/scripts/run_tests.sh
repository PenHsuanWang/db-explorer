#!/bin/bash
# Comprehensive test runner script
# Usage: ./scripts/run_tests.sh [OPTIONS]
#
# This script provides a convenient way to run tests with various options:
# - Run all tests, unit tests only, or integration tests only
# - Generate coverage reports
# - Skip slow tests for quick feedback
# - Verbose or quiet output

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
FAIL_FAST=false
MARKERS=""
PYTEST_ARGS=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            MARKERS="-m unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            MARKERS="-m integration"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --fast)
            MARKERS="-m 'not slow'"
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fail-fast|-x)
            FAIL_FAST=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --coverage      Generate coverage report"
            echo "  --fast          Skip slow tests"
            echo "  --verbose, -v   Verbose output"
            echo "  --fail-fast, -x Exit on first test failure"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Run all tests"
            echo "  $0 --unit --coverage    # Run unit tests with coverage"
            echo "  $0 --integration -v     # Run integration tests verbosely"
            echo "  $0 --fast               # Quick test run (skip slow tests)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

echo "========================================="
echo "Running Tests: $TEST_TYPE"
echo "========================================="
echo "Project root: $PROJECT_ROOT"
echo "Coverage: $COVERAGE"
echo "Verbose: $VERBOSE"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Install with: pip install pytest pytest-cov pytest-mock"
    exit 1
fi

# ============================================================================
# Build pytest command
# ============================================================================
PYTEST_CMD="pytest tests/"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -ra"  # Show summary of all test outcomes
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Add fail-fast
if [ "$FAIL_FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
fi

# ============================================================================
# Pre-test checks
# ============================================================================
echo -e "${BLUE}Pre-test checks...${NC}"

# Check if test directory exists
if [ ! -d "tests" ]; then
    echo -e "${YELLOW}Warning: tests/ directory not found${NC}"
    echo "Creating tests/ directory..."
    mkdir -p tests
fi

# Check if src directory exists
if [ ! -d "src" ]; then
    echo -e "${YELLOW}Warning: src/ directory not found${NC}"
fi

# ============================================================================
# Run tests
# ============================================================================
echo -e "\n${BLUE}Running: $PYTEST_CMD${NC}\n"

# Run pytest and capture exit code
if $PYTEST_CMD; then
    TEST_EXIT_CODE=0
else
    TEST_EXIT_CODE=$?
fi

# ============================================================================
# Post-test reporting
# ============================================================================
echo ""

if [ "$COVERAGE" = true ]; then
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Coverage Report${NC}"
    echo -e "${BLUE}=========================================${NC}"
    
    # Show coverage summary
    if [ -f ".coverage" ]; then
        echo -e "${GREEN}Coverage reports generated:${NC}"
        echo "  - Terminal: (shown above)"
        
        if [ -d "htmlcov" ]; then
            echo "  - HTML: htmlcov/index.html"
            # Try to find the coverage percentage
            if command -v coverage &> /dev/null; then
                COVERAGE_PCT=$(coverage report --precision=2 | grep TOTAL | awk '{print $NF}')
                echo "  - Total coverage: $COVERAGE_PCT"
            fi
        fi
        
        if [ -f "coverage.xml" ]; then
            echo "  - XML: coverage.xml"
        fi
    else
        echo -e "${YELLOW}Warning: No coverage data generated${NC}"
    fi
fi

# ============================================================================
# Test statistics
# ============================================================================
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}=========================================${NC}"
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo -e "${GREEN}=========================================${NC}"
else
    echo -e "\n${RED}=========================================${NC}"
    echo -e "${RED}Some tests failed. ✗${NC}"
    echo -e "${RED}=========================================${NC}"
    
    # Provide helpful suggestions
    echo -e "\n${YELLOW}Tips:${NC}"
    echo "  - Run with -v for verbose output to see more details"
    echo "  - Run with -x to stop on first failure"
    echo "  - Run specific test: pytest tests/test_file.py::test_name"
    echo "  - Run tests matching pattern: pytest -k 'test_pattern'"
fi

# ============================================================================
# Quick commands reference
# ============================================================================
if [ $TEST_EXIT_CODE -ne 0 ] && [ "$VERBOSE" = false ]; then
    echo -e "\n${BLUE}Quick commands:${NC}"
    echo "  pytest tests/test_file.py         # Run specific file"
    echo "  pytest tests/test_file.py::test_name  # Run specific test"
    echo "  pytest -k 'pattern'               # Run tests matching pattern"
    echo "  pytest --lf                       # Run last failed tests"
    echo "  pytest --ff                       # Run failures first"
fi

exit $TEST_EXIT_CODE
