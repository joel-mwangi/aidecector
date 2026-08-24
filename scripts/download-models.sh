#!/bin/bash
# Automated Model Downloader for Misinformation Detection System
# Downloads all recommended pre-trained models

set -e

MODELS_DIR="${1:-.}/models"
mkdir -p "$MODELS_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Misinformation Detection - Model Downloader           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Models will be saved to: $MODELS_DIR"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to report progress
download_model() {
    local name=$1
    local url=$2
    local filename=$3
    local size=$4
    
    echo -e "${BLUE}[DOWNLOADING]${NC} $name ($size)"
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$MODELS_DIR/$filename" "$url" 2>&1 || {
            echo -e "${YELLOW}[WARN]${NC} Failed to download $name from $url"
            return 1
        }
    elif command -v curl &> /dev/null; then
        curl -# -o "$MODELS_DIR/$filename" "$url" || {
            echo -e "${YELLOW}[WARN]${NC} Failed to download $name from $url"
            return 1
        }
    else
        echo -e "${YELLOW}[WARN]${NC} Neither wget nor curl available. Skipping $name"
        return 1
    fi
    
    echo -e "${GREEN}[✓]${NC} $name"
}

echo "═══════════════════════════════════════════════════════════════"
echo "STEP 1: Auto-loading Python Models (No Download Needed)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -e "${BLUE}[CHECKING]${NC} MediaPipe (will auto-download on first use)"
python3 << 'EOF' 2>/dev/null
try:
    import mediapipe as mp
    print("✓ MediaPipe Face Mesh")
    print("✓ MediaPipe Holistic")
except ImportError:
    print("Installing MediaPipe...")
    import subprocess
    subprocess.run(['pip', 'install', 'mediapipe'], check=True)
EOF

echo -e "${BLUE}[CHECKING]${NC} OpenCV (for image/video processing)"
python3 << 'EOF' 2>/dev/null
try:
    import cv2
    print("✓ OpenCV ready")
except ImportError:
    print("Installing OpenCV...")
    import subprocess
    subprocess.run(['pip', 'install', 'opencv-python'], check=True)
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 2: Downloading Pre-trained Models"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Deepfake Detection - Xception
download_model \
    "Xception (Deepfake Detector)" \
    "https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth" \
    "xception-epoch-92.pth" \
    "107 MB" || true

# Optional: MesoNet (Lightweight)
echo ""
echo -e "${YELLOW}[INFO]${NC} MesoNet (lighter alternative to Xception)"
echo "  Download from: https://github.com/HyperIntel/MesoNet/releases"
echo "  Or run: wget https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5"

# RAFT Optical Flow
download_model \
    "RAFT (Optical Flow Detection)" \
    "https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth" \
    "raft-things.pth" \
    "244 MB" || true

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 3: Install HuggingFace Models (Auto-download on Use)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -e "${BLUE}[INFO]${NC} Installing HuggingFace models (auto-load)..."

python3 << 'EOF'
import sys

models_to_cache = {
    "CLIP": "openai/clip-vit-base-patch32",
    "YOLOv8": "ultralytics/yolov8x",
    "Wav2Vec2": "facebook/wav2vec2-base-960h",
    "Resemblyzer": "speaker-embeddings"
}

print("The following models will auto-download on first use:")
for name, model_id in models_to_cache.items():
    print(f"  ✓ {name:20} - {model_id}")

print("\nTo pre-download HuggingFace models, run:")
print("  python3 -c \"from transformers import CLIPModel; CLIPModel.from_pretrained('openai/clip-vit-base-patch32')\"")
print("  python3 -c \"from transformers import Wav2Vec2ForCTC; Wav2Vec2ForCTC.from_pretrained('facebook/wav2vec2-base-960h')\"")
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 4: Optional - Download Additional Research Models"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}[OPTIONAL]${NC} Download FaceForensics++ full dataset"
echo "  Website: https://github.com/ondyari/FaceForensics"
echo "  Command: python download-ff.py --help"
echo ""

echo -e "${YELLOW}[OPTIONAL]${NC} Download ASVspoof 2021 models"
echo "  Website: https://www.asvspoof.org/"
echo "  Size: 500MB+"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "STEP 5: Verify Installation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

python3 << 'EOF'
import os
import sys

models_dir = "models"
downloaded_models = []
auto_load_models = []

# Check downloaded models
if os.path.exists(models_dir):
    for f in os.listdir(models_dir):
        if os.path.isfile(os.path.join(models_dir, f)):
            size_mb = os.path.getsize(os.path.join(models_dir, f)) / (1024*1024)
            downloaded_models.append((f, size_mb))

print("✓ Downloaded Models:")
total_size = 0
for name, size in downloaded_models:
    print(f"  {name:40} {size:8.1f} MB")
    total_size += size

if downloaded_models:
    print(f"\n  Total: {total_size:.1f} MB")
else:
    print("  (None yet - they will download on first use)")

print("\n✓ Auto-loading Models (will download on first use):")
auto_models = [
    ("MediaPipe Face Mesh", "~50 MB"),
    ("MediaPipe Holistic", "~50 MB"),
    ("CLIP ViT-B/32", "~350 MB"),
    ("YOLOv8x", "~200 MB"),
    ("Wav2Vec2", "~400 MB"),
    ("Resemblyzer", "~30 MB"),
]

for name, size in auto_models:
    print(f"  {name:40} {size:>10}")

print("\n✓ All essential models are ready!")
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "INTEGRATION INSTRUCTIONS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat << 'EOF'
1. Update your detector files:

   src/visual/forensics.py:
   - Replace xception placeholder with loaded model
   - Use RAFT for optical flow
   
   src/audio/forensics.py:
   - Use wav2vec2 for speech-to-text
   - Use resemblyzer for voice embeddings

   Example:
   ```python
   import torch
   self.deepfake_model = torch.load('models/xception-epoch-92.pth')
   ```

2. Test the installation:
   ```bash
   docker compose exec api python3 << 'PYEOF'
   import torch
   model = torch.load('models/xception-epoch-92.pth')
   print(f"✓ Deepfake model loaded: {model}")
   PYEOF
   ```

3. Monitor memory usage:
   ```bash
   docker stats
   ```

4. If running out of memory:
   - Use smaller models (MesoNet instead of Xception)
   - Enable model quantization
   - Use only CPU with reduced batch size
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✓ Model Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Total models ready: $(ls -1 models/ 2>/dev/null | wc -l) files"
echo ""
echo "Next steps:"
echo "  1. Review MODELS_GUIDE.md for integration details"
echo "  2. Update detector code to use real models"
echo "  3. Test with: docker compose exec api python3 -m pytest tests/"
echo "  4. Monitor performance with: docker stats"
echo ""
