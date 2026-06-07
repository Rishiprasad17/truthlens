#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
err()  { echo -e "  ${RED}✗${NC}  $1"; exit 1; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
info() { echo -e "  →  $1"; }

echo ""
echo "  TruthLens Installer"
echo "  ==================="
echo ""

# Python
python3 --version &>/dev/null || err "Python 3 not found. Install from https://python.org"
ok "Python found"

# Node
node --version &>/dev/null || err "Node.js not found. Install from https://nodejs.org"
ok "Node.js found"

# Python packages
info "Installing Python packages..."
pip install -r requirements.txt --quiet
ok "Python packages installed"

# Dashboard
info "Installing dashboard dependencies..."
cd dashboard && npm install --silent && cd ..
ok "Dashboard ready"

# CLI
info "Installing truthlens CLI..."
pip install -e . --quiet
ok "CLI installed"

echo ""
echo "  ============================================"
echo "   TruthLens installed successfully!"
echo "  ============================================"
echo ""
echo "  Make sure Ollama is running:"
echo "    1. Install: curl -fsSL https://ollama.ai/install.sh | sh"
echo "    2. Run:     ollama serve"
echo "    3. Pull:    ollama pull llama3"
echo ""
echo "  Then start TruthLens:"
echo "    truthlens start"
echo ""
echo "  Or check setup:"
echo "    truthlens setup"
echo ""
