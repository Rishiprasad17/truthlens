#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

ok()   { echo -e "  ${GREEN}[OK]${NC}  $1"; }
err()  { echo -e "  ${RED}[!!]${NC}  $1"; }
info() { echo -e "  ${BLUE}[->]${NC}  $1"; }
warn() { echo -e "  ${YELLOW}[??]${NC}  $1"; }

echo ""
echo -e "  ${BOLD}============================================${NC}"
echo -e "  ${BOLD} TruthLens - AI Trust and Evaluation Layer${NC}"
echo -e "  ${BOLD} v0.4.0${NC}"
echo -e "  ${BOLD}============================================${NC}"
echo ""

# Check Python
python3 --version &>/dev/null || { err "Python not found. Install from https://python.org"; exit 1; }
ok "Python found"

# Check Node
node --version &>/dev/null || { err "Node.js not found. Install from https://nodejs.org"; exit 1; }
ok "Node.js found"

# Check/start Ollama
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama is running"
else
    warn "Ollama not running. Attempting to start..."
    ollama serve &>/dev/null &
    sleep 4
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama started"
    else
        err "Could not start Ollama. Install from https://ollama.ai"
        err "Then run: ollama pull llama3"
        exit 1
    fi
fi

# Install Python packages if needed
python3 -c "import fastapi" &>/dev/null || {
    info "Installing Python packages..."
    pip3 install -r requirements.txt --quiet
    ok "Python packages installed"
}
ok "Python packages ready"

# Install dashboard packages if needed
if [ ! -d "dashboard/node_modules" ]; then
    info "Installing dashboard packages (first time only)..."
    cd dashboard && npm install --silent && cd ..
    ok "Dashboard packages installed"
fi
ok "Dashboard packages ready"

# Kill any existing processes on our ports
kill $(lsof -ti:8000) 2>/dev/null || true
kill $(lsof -ti:8001) 2>/dev/null || true
kill $(lsof -ti:5173) 2>/dev/null || true
sleep 1

# Start API
info "Starting TruthLens API..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &>/tmp/truthlens_api.log &
API_PID=$!

# Wait for API
for i in {1..15}; do
    curl -s http://localhost:8000/health &>/dev/null && break
    sleep 1
done
ok "API running at http://localhost:8000"

# Start Proxy
info "Starting TruthLens Proxy..."
python3 -m uvicorn proxy.server:app --host 0.0.0.0 --port 8001 &>/tmp/truthlens_proxy.log &
PROXY_PID=$!
sleep 2
ok "Proxy running at http://localhost:8001"

# Start Dashboard
info "Starting Dashboard..."
cd dashboard && npm run dev &>/tmp/truthlens_dash.log &
DASH_PID=$!
cd ..
sleep 3
ok "Dashboard running at http://localhost:5173"

# Open browser
info "Opening browser..."
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5173" &>/dev/null &
elif command -v open &>/dev/null; then
    open "http://localhost:5173"
fi

echo ""
echo -e "  ${BOLD}============================================${NC}"
echo -e "  ${GREEN}${BOLD} TruthLens is running!${NC}"
echo -e "  ${BOLD}============================================${NC}"
echo ""
echo "   Dashboard  ->  http://localhost:5173"
echo "   API        ->  http://localhost:8000"
echo "   Proxy      ->  http://localhost:8001"
echo "   API Docs   ->  http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop TruthLens"
echo ""
echo -e "  ${BOLD}============================================${NC}"
echo ""

# Wait and handle Ctrl+C
cleanup() {
    echo ""
    info "Stopping TruthLens..."
    kill $API_PID $PROXY_PID $DASH_PID 2>/dev/null || true
    kill $(lsof -ti:8000) 2>/dev/null || true
    kill $(lsof -ti:8001) 2>/dev/null || true
    kill $(lsof -ti:5173) 2>/dev/null || true
    ok "TruthLens stopped. Goodbye."
    exit 0
}

trap cleanup INT TERM
wait $API_PID
