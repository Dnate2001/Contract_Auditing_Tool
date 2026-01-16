#!/bin/bash
#
# Secure ngrok Demo Launcher
# Starts demo server with ngrok tunnel and HTTP Basic Auth
#
# Usage: bash scripts/start_ngrok_demo.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Contract Auditor - ngrok Demo Mode${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Load .env if exists
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading .env configuration"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠${NC}  No .env file found - using environment variables"
fi

# Validate required variables
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo -e "${RED}❌ NGROK_AUTHTOKEN not set${NC}"
    echo ""
    echo "To get your ngrok authtoken:"
    echo "  1. Sign up at https://ngrok.com"
    echo "  2. Get token from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  3. Add to .env: NGROK_AUTHTOKEN=your_token_here"
    echo ""
    exit 1
fi

if [ -z "$DEMO_USER" ] || [ -z "$DEMO_PASS" ]; then
    echo -e "${RED}❌ DEMO_USER or DEMO_PASS not set${NC}"
    echo "Add to .env:"
    echo "  DEMO_USER=your_username"
    echo "  DEMO_PASS=strong_password_here"
    exit 1
fi

# Warn if using default password
if [ "$DEMO_PASS" == "change_me_strong_password" ]; then
    echo -e "${YELLOW}⚠  WARNING: Using default DEMO_PASS${NC}"
    echo -e "${YELLOW}   Please set a strong password in .env${NC}\n"
fi

# Set defaults
DEMO_MODE=${DEMO_MODE:-true}
DEMO_TTL_SECONDS=${DEMO_TTL_SECONDS:-10800}
PORT=${PORT:-8080}

# Build CIDR flags for ngrok
CIDR_FLAGS=""
if [ -n "$DEMO_CIDR_ALLOW" ]; then
    echo -e "${GREEN}✓${NC} CIDR allow-list configured: $DEMO_CIDR_ALLOW"
    CIDR_FLAGS="--cidr-allow \"$DEMO_CIDR_ALLOW\""
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok not found${NC}"
    echo ""
    echo "Install ngrok:"
    echo "  macOS: brew install ngrok"
    echo "  Linux: snap install ngrok"
    echo "  Or download from: https://ngrok.com/download"
    echo ""
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}❌ Port $PORT already in use${NC}"
    echo "Stop the existing service or change PORT in .env"
    exit 1
fi

# Start demo server
echo -e "${GREEN}🚀 Starting demo server...${NC}"
DEMO_MODE=true python3 demo_server.py &
SERVER_PID=$!

# Wait for server to start
echo "   Waiting for server startup..."
sleep 5

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}❌ Demo server failed to start${NC}"
    echo "Check the error messages above"
    exit 1
fi

echo -e "${GREEN}✓${NC} Demo server running (PID: $SERVER_PID)"

# Start ngrok tunnel
echo -e "${GREEN}🌐 Starting ngrok tunnel...${NC}"

# Build ngrok command
NGROK_CMD="ngrok http $PORT --authtoken \"$NGROK_AUTHTOKEN\" --basic-auth \"$DEMO_USER:$DEMO_PASS\""
if [ -n "$CIDR_FLAGS" ]; then
    NGROK_CMD="$NGROK_CMD $CIDR_FLAGS"
fi

# Start ngrok in background
eval $NGROK_CMD > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo "   Waiting for ngrok tunnel..."
sleep 3

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" == "null" ]; then
    echo -e "${RED}❌ Failed to get ngrok URL${NC}"
    echo "Cleaning up..."
    kill $SERVER_PID $NGROK_PID 2>/dev/null
    exit 1
fi

# Print success info
echo -e "${GREEN}✓${NC} ngrok tunnel established"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Demo server running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}📍 Public URL:${NC} $NGROK_URL"
echo -e "${YELLOW}🔐 Username:${NC} $DEMO_USER"
echo -e "${YELLOW}🔐 Password:${NC} $DEMO_PASS"
echo -e "${YELLOW}⏰ Auto-shutdown:${NC} ${DEMO_TTL_SECONDS}s ($(($DEMO_TTL_SECONDS / 60)) minutes)"
echo ""
echo -e "${BLUE}Test endpoints:${NC}"
echo "  Health: curl -u $DEMO_USER:$DEMO_PASS $NGROK_URL/health"
echo "  Audit:  curl -u $DEMO_USER:$DEMO_PASS -X POST $NGROK_URL/audit -F 'file=@contract.sol'"
echo ""
echo -e "${YELLOW}⚠  Security Reminders:${NC}"
echo "  • Share URL and credentials only with trusted reviewers"
echo "  • Do NOT use real API keys in demo mode"
echo "  • Tunnel will auto-close after TTL"
echo "  • Artifacts isolated to /tmp/artifacts_demo/"
echo ""
echo -e "${BLUE}To stop manually:${NC}"
echo "  kill $SERVER_PID $NGROK_PID"
echo "  Or: pkill -f 'demo_server|ngrok'"
echo ""
echo -e "${BLUE}========================================${NC}"

# Set up auto-shutdown
(
    sleep $DEMO_TTL_SECONDS
    echo -e "\n${YELLOW}⏰ TTL expired - shutting down demo${NC}"
    kill $SERVER_PID $NGROK_PID 2>/dev/null
) &
AUTO_SHUTDOWN_PID=$!

# Wait for processes (will be killed by auto-shutdown or manual interrupt)
wait $SERVER_PID 2>/dev/null
wait $NGROK_PID 2>/dev/null

echo -e "\n${GREEN}✓${NC} Demo server stopped"
