#!/bin/bash

# Ensemble System Quick Start
# Complete setup in 3 steps

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ENSEMBLE MULTIMODAL DETECTION - QUICK START            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "[1/3] Checking prerequisites..."
echo ""

if ! command -v python &> /dev/null; then
    echo "✗ Python 3.8+ not found"
    exit 1
fi
echo "✓ Python $(python --version 2>&1 | cut -d' ' -f2)"

if ! command -v docker &> /dev/null; then
    echo "⚠ Docker not found (optional for containerization)"
else
    echo "✓ Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
fi

if ! command -v git &> /dev/null; then
    echo "⚠ Git not found (optional)"
else
    echo "✓ Git $(git --version | cut -d' ' -f3)"
fi

echo ""
echo "[2/3] Downloading ensemble models..."
echo ""

if [ -f "scripts/download-ensemble-models.sh" ]; then
    chmod +x scripts/download-ensemble-models.sh
    bash scripts/download-ensemble-models.sh
else
    echo "✗ Model download script not found"
    exit 1
fi

echo ""
echo "[3/3] Installing dependencies..."
echo ""

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo "✓ Dependencies installed"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║               SETUP COMPLETE ✓                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "Option 1: Docker (Recommended)"
echo "  docker compose -f docker-compose.full.yml up -d"
echo "  Open: http://localhost:3000"
echo ""
echo "Option 2: Local Python"
echo "  python src/api/main.py"
echo "  curl http://localhost:8000/health"
echo ""
echo "Test the system:"
echo ""
echo "  # Get model status"
echo "  curl http://localhost:8000/health"
echo ""
echo "  # Analyze image"
echo "  curl -X POST http://localhost:8000/api/v1/analyze/quick \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"media_type\":\"image\",\"media_url\":\"https://example.com/img.jpg\"}'"
echo ""
echo "Documentation:"
echo "  - ENSEMBLE_IMPLEMENTATION_COMPLETE.md"
echo "  - ENSEMBLE_MODELS.md"
echo ""
echo "Troubleshooting:"
echo "  - Check: src/models/model_manager.py"
echo "  - Check: config/ensemble_config.py"
echo "  - Logs: docker compose logs api"
echo ""
