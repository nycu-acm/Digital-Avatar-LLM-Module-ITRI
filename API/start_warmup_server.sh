#!/bin/bash

# Model Warmup Server Startup Script
# This script starts the model warmup server with proper configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/model_warmup_server.py"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Model Warmup Server${NC}"
echo -e "${BLUE}📁 Script Directory: ${SCRIPT_DIR}${NC}"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}❌ Error: model_warmup_server.py not found at ${PYTHON_SCRIPT}${NC}"
    exit 1
fi

# Default configuration
API_URL="http://localhost:5002"
INTERVAL="10"
TEST_MODE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --test)
            TEST_MODE="--test"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --api-url URL     API service URL (default: http://localhost:5002)"
            echo "  --interval MIN    Warmup interval in minutes (default: 10)"
            echo "  --test            Run single test warmup and exit"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Use default settings"
            echo "  $0 --interval 5             # Warmup every 5 minutes"
            echo "  $0 --test                   # Run test warmup"
            echo "  $0 --api-url http://localhost:5003 --interval 15"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}📡 API URL: ${API_URL}${NC}"
echo -e "${BLUE}⏰ Interval: ${INTERVAL} minutes${NC}"

if [ -n "$TEST_MODE" ]; then
    echo -e "${YELLOW}🧪 Running in test mode${NC}"
fi

# Change to script directory
cd "$SCRIPT_DIR" || exit 1

# Check if we're in the right environment
if [ ! -f "client_utils.py" ]; then
    echo -e "${RED}❌ Error: client_utils.py not found. Make sure you're in the correct directory.${NC}"
    exit 1
fi

# Start the Python server
echo -e "${GREEN}🔥 Starting warmup server...${NC}"
python3 "$PYTHON_SCRIPT" --api-url "$API_URL" --interval "$INTERVAL" $TEST_MODE

# Check exit code
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Warmup server stopped gracefully${NC}"
else
    echo -e "${RED}❌ Warmup server exited with error code: ${exit_code}${NC}"
fi

exit $exit_code
