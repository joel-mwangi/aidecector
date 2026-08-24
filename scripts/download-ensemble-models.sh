#!/bin/bash

# Ensemble Models Downloader
# Downloads all pre-trained models for multimodal ensemble detection

set -e

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

echo "=========================================="
echo "Ensemble Models Downloader"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

total_size=0

# Xception Deepfake Detector
echo -e "${YELLOW}[1/4] Xception Deepfake Detector${NC}"
if [ -f "$MODELS_DIR/xception-epoch-92.pth" ]; then
    echo -e "${GREEN}✓ Already exists${NC}"
else
    echo "Downloading (107 MB)..."
    wget -q --show-progress "https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth" \
        -O "$MODELS_DIR/xception-epoch-92.pth"
    echo -e "${GREEN}✓ Downloaded${NC}"
fi
((total_size += 107))

# RAFT Optical Flow
echo -e "${YELLOW}[2/4] RAFT Optical Flow${NC}"
if [ -f "$MODELS_DIR/raft-things.pth" ]; then
    echo -e "${GREEN}✓ Already exists${NC}"
else
    echo "Downloading (244 MB)..."
    wget -q --show-progress "https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth" \
        -O "$MODELS_DIR/raft-things.pth"
    echo -e "${GREEN}✓ Downloaded${NC}"
fi
((total_size += 244))

# MesoNet Lightweight Detector (optional)
echo -e "${YELLOW}[3/4] MesoNet Lightweight Detector (optional)${NC}"
if [ -f "$MODELS_DIR/MesoNet-4_DF.h5" ]; then
    echo -e "${GREEN}✓ Already exists${NC}"
else
    echo "Downloading (8 MB)..."
    wget -q --show-progress "https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5" \
        -O "$MODELS_DIR/MesoNet-4_DF.h5" || echo -e "${YELLOW}⚠ Optional model failed to download${NC}"
fi
((total_size += 8))

# Create model checksums file
echo -e "${YELLOW}[4/4] Creating verification checksums${NC}"
cd "$MODELS_DIR"

if command -v sha256sum &> /dev/null; then
    sha256sum *.pth *.h5 2>/dev/null > checksums.sha256 || true
    echo -e "${GREEN}✓ Checksums created${NC}"
fi

cd ..

echo ""
echo "=========================================="
echo "Download Summary"
echo "=========================================="
echo "Models Directory: $(pwd)/$MODELS_DIR"
echo "Estimated Total Size: ~${total_size} MB"
echo ""
echo "Models Downloaded:"
ls -lh "$MODELS_DIR"/ | grep -E '\.(pth|h5)$' || echo "No models found"
echo ""

# Verify models
echo "Verifying model files..."
if [ -f "$MODELS_DIR/xception-epoch-92.pth" ]; then
    echo -e "${GREEN}✓ Xception${NC}"
else
    echo -e "${YELLOW}✗ Xception (missing)${NC}"
fi

if [ -f "$MODELS_DIR/raft-things.pth" ]; then
    echo -e "${GREEN}✓ RAFT${NC}"
else
    echo -e "${YELLOW}✗ RAFT (missing)${NC}"
fi

if [ -f "$MODELS_DIR/MesoNet-4_DF.h5" ]; then
    echo -e "${GREEN}✓ MesoNet${NC}"
else
    echo -e "${YELLOW}⚠ MesoNet (optional, not found)${NC}"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Start the system:"
echo "   docker compose -f docker-compose.full.yml up -d"
echo ""
echo "2. Test ensemble:"
echo "   curl -X POST http://localhost:8000/api/v1/analyze ..."
echo ""
echo "3. View results:"
echo "   http://localhost:3000"
echo ""
echo "=========================================="

# Auto-loaded models (no download needed)
echo ""
echo "Auto-loading Models (on first use):"
echo "  • Wav2Vec2 (~400 MB) - Speech-to-text"
echo "  • MediaPipe (~50 MB) - Face detection"
echo "  • CLIP (~350 MB) - Image understanding"
echo "  • YOLOv8 (~200 MB) - Object detection"
echo "  • Resemblyzer (~30 MB) - Voice embeddings"
echo ""
echo "Total disk space needed: ~1.3 GB"
echo ""
echo -e "${GREEN}✓ Download complete!${NC}"
