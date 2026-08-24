# Pre-trained Models Integration Guide

Complete reference for downloading and using state-of-the-art detection models.

## 📚 Quick Reference

| Category | Model | Task | Use |
|----------|-------|------|-----|
| **Face** | MediaPipe | Detection | `python -m mediapipe` |
| **Face** | RetinaFace | Better detection | Download |
| **Face** | FaceNet | Embeddings | Auto-load |
| **Deepfake** | Xception | Best detection | Download |
| **Deepfake** | MesoNet | Lightweight | Download |
| **Optical Flow** | RAFT | Temporal | Download |
| **Speech** | Wav2Vec2 | Speech-to-text | Auto-load |
| **Voice** | Resemblyzer | Voice embeddings | Auto-load |
| **Semantics** | CLIP | Image understanding | Auto-load |
| **Objects** | YOLOv8 | Detection | Auto-load |

---

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

```bash
# Download all recommended models
bash scripts/download-models.sh

# Or use Python manager
python3 scripts/model_manager.py download

# List available models
python3 scripts/model_manager.py list

# Check storage requirements
python3 scripts/model_manager.py estimate
```

### Option 2: Manual Download

```bash
# Create models directory
mkdir -p models

# Download Xception (deepfake detection)
wget https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth -O models/xception-epoch-92.pth

# Download RAFT (optical flow)
wget https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth -O models/raft-things.pth
```

### Option 3: Individual Installation

```bash
# Face detection (auto-loads)
python3 -c "import mediapipe as mp; print('Ready')"

# Deepfake detection
python3 -c "import torch; model = torch.load('models/xception-epoch-92.pth')"

# Speech processing (auto-loads)
python3 -c "from transformers import Wav2Vec2ForCTC; print('Ready')"
```

---

## 📊 Model Storage Requirements

```
RECOMMENDED (Total: ~700 MB)
├── Xception              107 MB  ✓ (Deepfake detection - production quality)
├── RAFT                  244 MB  ✓ (Optical flow - temporal analysis)
├── Auto-loaded models    350 MB  ✓ (CLIP, YOLOv8, Wav2Vec2 - cached)
└── System models          ~50 MB  ✓ (MediaPipe, FaceNet - auto-load)

LIGHTWEIGHT (Total: ~600 MB)
├── MesoNet                 8 MB  ✓ (Lightweight deepfake)
├── RAFT                  244 MB  ✓ (Optical flow)
└── Auto-loaded           350 MB  ✓ (Already included)

FULL ENTERPRISE (Total: ~1.5 GB)
├── All above models            
├── RetinaFace            100 MB  (Alternative face detection)
├── YOLOv8 Large          200 MB  (Large object detection)
└── Additional research   ~200 MB
```

---

## 🔧 Integration Examples

### Example 1: Use Xception for Deepfake Detection

```python
# src/visual/forensics.py

import torch
from pathlib import Path

class VisualForensics:
    def __init__(self, device="cpu"):
        self.device = device
        
        # Load Xception model
        model_path = Path("models/xception-epoch-92.pth")
        if model_path.exists():
            self.deepfake_model = torch.load(model_path, map_location=device)
            self.deepfake_model.eval()
        else:
            logger.warning("Xception model not found - using placeholder")
            self.deepfake_model = None
    
    async def detect_deepfake(self, image):
        """Detect deepfakes using Xception"""
        if self.deepfake_model is None:
            return {"score": 0.5, "confidence": 0.0}
        
        # Preprocess
        img_tensor = self._preprocess(image).to(self.device)
        
        # Predict
        with torch.no_grad():
            output = self.deepfake_model(img_tensor)
            probs = torch.softmax(output, dim=1)
            fake_score = probs[0, 1].item()
        
        return {
            "fake_probability": fake_score,
            "real_probability": 1 - fake_score,
            "confidence": max(fake_score, 1 - fake_score)
        }
    
    def _preprocess(self, image):
        """Preprocess image for Xception"""
        from torchvision import transforms
        
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((299, 299)),
            transforms.Normalize(
                mean=[0.5, 0.5, 0.5],
                std=[0.5, 0.5, 0.5]
            )
        ])
        
        return transform(image).unsqueeze(0)
```

### Example 2: Use CLIP for Semantic Analysis

```python
# src/visual/forensics.py - Add to VisualForensics

async def analyze_semantic_consistency(self, image, claim):
    """Check if image matches claim using CLIP"""
    import clip
    import torch
    
    # Load CLIP
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Prepare image
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    
    # Create text options
    texts = [
        "a real photo",
        "a fake/synthetic photo",
        "edited or manipulated",
        claim  # User's claim
    ]
    
    text_tokens = clip.tokenize(texts).to(device)
    
    # Get similarity
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        text_features = model.encode_text(text_tokens)
        
        similarities = (image_features @ text_features.T).softmax(dim=-1)
    
    return {
        "real_prob": similarities[0, 0].item(),
        "fake_prob": similarities[0, 1].item(),
        "claim_match": similarities[0, 3].item()
    }
```

### Example 3: Use Wav2Vec2 for Speech-to-Text

```python
# src/audio/forensics.py

from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import librosa

class AudioForensics:
    def __init__(self, device="cpu"):
        self.device = device
        self.processor = Wav2Vec2Processor.from_pretrained(
            "facebook/wav2vec2-base-960h"
        )
        self.model = Wav2Vec2ForCTC.from_pretrained(
            "facebook/wav2vec2-base-960h"
        ).to(device)
    
    async def extract_speech(self, audio_path):
        """Convert audio to text"""
        # Load audio
        waveform, sr = librosa.load(audio_path, sr=16000)
        
        # Process
        inputs = self.processor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
            padding="longest"
        )
        
        # Predict
        with torch.no_grad():
            logits = self.model(
                inputs.input_values.to(self.device)
            ).logits
        
        # Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        
        return {
            "text": transcription,
            "confidence": 0.9  # Could calculate from logits
        }
```

### Example 4: Use Resemblyzer for Voice Verification

```python
# src/audio/forensics.py

from resemblyzer import VoiceEncoder, preprocess_wav

class AudioForensics:
    def __init__(self):
        self.encoder = VoiceEncoder()
    
    async def check_speaker_consistency(self, audio_segments):
        """Check if all segments are from same speaker"""
        embeddings = []
        
        for audio_path in audio_segments:
            wav = preprocess_wav(audio_path)
            embed = self.encoder.embed_utterance(wav)
            embeddings.append(embed)
        
        # Compare embeddings (cosine similarity)
        import numpy as np
        
        consistencies = []
        for i in range(len(embeddings)-1):
            sim = np.dot(embeddings[i], embeddings[i+1])
            consistencies.append(sim)
        
        avg_consistency = np.mean(consistencies)
        
        return {
            "speaker_consistency": avg_consistency,
            "likely_same_speaker": avg_consistency > 0.7,
            "confidence": avg_consistency
        }
```

---

## 📥 Model Downloads

### Automatic (Recommended)

```bash
# Single command
python3 scripts/model_manager.py download

# Or with bash script
bash scripts/download-models.sh
```

### Manual Downloads

```bash
# Deepfake detection (Xception)
wget https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth

# Optical flow (RAFT)
wget https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth

# Face detection (RetinaFace)
wget https://github.com/serengoodbroad/RetinaFace_Pytorch/releases/download/latest/mobilenet0.25_Final.pth

# Lightweight deepfake (MesoNet)
wget https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5
```

---

## ✅ Verification & Testing

```bash
# Verify models loaded in Docker
docker compose exec api python3 << 'EOF'
import torch
import sys

# Check Xception
try:
    model = torch.load('models/xception-epoch-92.pth')
    print("✓ Xception loaded")
except Exception as e:
    print(f"✗ Xception: {e}")

# Check RAFT
try:
    model = torch.load('models/raft-things.pth')
    print("✓ RAFT loaded")
except Exception as e:
    print(f"✗ RAFT: {e}")

# Check auto-load models
try:
    import mediapipe as mp
    print("✓ MediaPipe loaded")
except:
    print("✗ MediaPipe not available")

try:
    from transformers import Wav2Vec2ForCTC
    print("✓ Wav2Vec2 available")
except:
    print("✗ Wav2Vec2 not available")

print("\nAll models status checked")
EOF
```

---

## 🔄 Update Detectors

Replace placeholders in your detector files:

```python
# BEFORE (placeholder)
return {
    "manipulation_probability": 0.5,
    "synthetic_media_probability": 0.3
}

# AFTER (using real models)
if self.deepfake_model:
    result = self.deepfake_model(image_tensor)
    return {
        "manipulation_probability": float(result["fake_prob"]),
        "synthetic_media_probability": float(result["synthetic_prob"])
    }
```

---

## 📊 Performance Benchmarks

| Model | Speed (CPU) | Speed (GPU) | Accuracy | Memory |
|-------|-------------|------------|----------|--------|
| MediaPipe | 30 FPS | - | 97% | 50 MB |
| Xception | 1-5 FPS | 20-30 FPS | 98% | 400 MB |
| MesoNet | 30-60 FPS | 100+ FPS | 95% | 80 MB |
| RAFT | 0.5-2 FPS | 5-10 FPS | 99% | 1200 MB |
| CLIP | 2-5 FPS | 20-50 FPS | 88% | 1500 MB |
| YOLOv8 | 5-10 FPS | 30-60 FPS | 96% | 1000 MB |

---

## 🎯 Recommended Configurations

### Development (CPU)
```
MediaPipe + MesoNet + RAFT
Total: ~300 MB
Speed: Real-time on CPU
```

### Production (GPU)
```
MediaPipe + Xception + RAFT + CLIP + YOLOv8
Total: ~1 GB
Speed: Real-time with GPU
```

### Research
```
All available models
Total: ~2 GB
Speed: Complete analysis
```

---

## 📖 Next Steps

1. **Download models:** `python3 scripts/model_manager.py download`
2. **Update detectors:** Replace placeholders with real models
3. **Test integration:** `docker compose exec api pytest tests/`
4. **Monitor performance:** `docker stats`
5. **Optimize:** Use quantization or model pruning if needed

---

See `MODELS_GUIDE.md` for detailed information on each model.
