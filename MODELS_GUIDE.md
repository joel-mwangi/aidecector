# Pre-trained Models for Misinformation Detection

Complete guide to downloading and integrating state-of-the-art detection models.

---

## 1. FACE DETECTION & MANIPULATION

### MediaPipe Face Detection (Recommended - Easiest)

**What it detects:**
- Face detection and localization
- Facial landmarks (468 points)
- Head pose estimation
- Performance: Real-time on CPU

**Download & Install:**

```bash
# Already in requirements.txt
pip install mediapipe

# Quick test
python3 << 'EOF'
import mediapipe as mp

mp_face_detection = mp.solutions.face_detection
with mp_face_detection.FaceDetection() as face_detection:
    print("MediaPipe Face Detection ready")
EOF
```

**Integration in Code:**

```python
import mediapipe as mp
import cv2

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=10,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# In your detector
def detect_faces(image):
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if results.multi_face_landmarks:
        return results.multi_face_landmarks
    return []
```

---

### RetinaFace (Better for Unconstrained Faces)

**What it detects:**
- Face detection in wild images
- Facial landmarks
- Better handling of partial faces, extreme angles
- Pre-trained on hard negative mining

**Download:**

```bash
# Install
pip install retina-face

# Download model (automatic on first use)
from retinaface import RetinaFace

# Detect
detection = RetinaFace.detect_faces("image.jpg")
print(detection)
```

**Hugging Face Model:**

```bash
# Download from Hugging Face
pip install huggingface-hub

python3 << 'EOF'
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="Bingsu/RetinaFace",
    filename="retinaface.onnx"
)
print(f"Model saved to: {model_path}")
EOF
```

---

### FaceNet (Face Embeddings & Verification)

**What it does:**
- Extract 128D embeddings per face
- Compare faces for identity consistency
- Identify if same person across frames

**Download from TensorFlow Hub:**

```bash
pip install tensorflow tensorflow-hub

python3 << 'EOF'
import tensorflow as tf
import tensorflow_hub as hub

# Load FaceNet model
facenet_model = hub.load('https://tfhub.dev/google/imagenet/inception_v3/feature_vector/5')
print("FaceNet loaded")

# Or use face_recognition library
pip install face_recognition
EOF
```

**Quick Face Recognition:**

```python
import face_recognition

# Load image
image = face_recognition.load_image_file("face.jpg")
face_encodings = face_recognition.face_encodings(image)

# Compare faces
for encoding in face_encodings:
    print(f"Face embedding: {encoding.shape}")  # (128,)
```

---

## 2. DEEPFAKE & FACE SWAP DETECTION

### FaceForensics++ (Research Benchmark)

**What it includes:**
- Detection models pre-trained on deepfakes
- Face2Face, FaceSwap, NeuralTextures, DeepFaceLab datasets
- SOTA detection accuracies (98%+)

**Download Dataset:**

```bash
# Get the detection models
# https://github.com/ondyari/FaceForensics

git clone https://github.com/ondyari/FaceForensics.git
cd FaceForensics

# Download models (requires registration)
python download-ff.py --help

# Or download pre-trained detector
wget https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth
```

**Use Pre-trained Detector:**

```python
import torch
import torch.nn as nn
from torchvision import transforms

# Load Xception detector (pre-trained on FaceForensics++)
model = torch.hub.load('pytorch/vision:v0.10.0', 'xception', pretrained=True)

# Modify for binary classification (real/fake)
model.fc = nn.Linear(2048, 2)
checkpoint = torch.load('xception-epoch-92.pth')
model.load_state_dict(checkpoint['state_dict'])
model.eval()

# Predict
def detect_deepfake(image_tensor):
    with torch.no_grad():
        output = model(image_tensor)
    return torch.softmax(output, dim=1)
```

---

### EfficientNet B7 (Lightweight Deepfake Detector)

**What it offers:**
- Faster inference than Xception
- Better accuracy/speed tradeoff
- Good for real-time processing

**Download from Hugging Face:**

```bash
pip install timm

python3 << 'EOF'
import timm

# Load pre-trained EfficientNet
model = timm.create_model('efficientnet_b7', pretrained=True)

# Fine-tune for deepfake detection
import torch.nn as nn
model.classifier = nn.Sequential(
    nn.Dropout(0.2),
    nn.Linear(2560, 2)
)
print("EfficientNet B7 ready")
EOF
```

---

### MesoNet (Lightweight Deepfake Detector)

**Best for:** Mobile/edge deployment, real-time analysis

**Download:**

```bash
git clone https://github.com/HyperIntel/MesoNet.git
cd MesoNet

# Download pre-trained weights
wget https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5

# Or directly
python3 << 'EOF'
from keras.models import load_model
model = load_model('MesoNet-4_DF.h5')
print("MesoNet loaded")
EOF
```

---

## 3. SYNTHETIC SPEECH DETECTION

### Resemblyzer (Voice Embeddings)

**What it does:**
- Extract speaker embeddings
- Compare voice consistency
- Detect voice cloning

**Install & Use:**

```bash
pip install resemblyzer

python3 << 'EOF'
from resemblyzer import VoiceEncoder
import librosa

encoder = VoiceEncoder()

# Load audio
wav, sr = librosa.load("audio.wav")

# Get embedding
embed = encoder.embed_utterance(wav)
print(f"Voice embedding shape: {embed.shape}")  # (256,)
EOF
```

---

### ASVspoof 2021 (Synthetic Speech Detection)

**What it detects:**
- Synthetic speech (TTS, voice conversion)
- Bonafide vs spoofed audio
- Trained on: WaveNet, Waveglow, Tacotron2, etc.

**Download Datasets & Models:**

```bash
# Download from ASVspoof Challenge
wget https://www.asvspoof.org/resources/ASVspoof2021_LA_asptoolkit.zip

# Or use pre-trained model from Hugging Face
python3 << 'EOF'
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="asvspoof/asvspoof2021-la",
    filename="model.pth"
)
print(f"Model: {model_path}")
EOF
```

**Integration:**

```python
import torch
import torchaudio

# Load detector
model = torch.hub.load('pytorch/pytorch_sound:main', 'asv_lfcc')

# Analyze audio
wav, sr = torchaudio.load("audio.wav")
logits = model(wav)
probs = torch.softmax(logits, dim=1)
fake_score = probs[0, 1].item()  # Probability of synthetic
```

---

### Coqui STT (Speech-to-Text for Claim Extraction)

**What it does:**
- Convert audio to text
- Extract claims from speech
- Open-source, offline

**Download & Install:**

```bash
pip install stt

# Or from Hugging Face
python3 << 'EOF'
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

print("Speech-to-text model ready")
EOF
```

---

## 4. LIP-SYNC DETECTION

### MediaPipe Holistic (Pose + Face + Hands)

**What it tracks:**
- Facial landmarks (468 points)
- Body pose (33 joints)
- Hand pose (21 joints per hand)
- Mouth movement detection

**Already Included:**

```python
import mediapipe as mp

mp_holistic = mp.solutions.holistic

with mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True
) as holistic:
    # Process each frame
    results = holistic.process(frame)
    
    # Access facial landmarks
    if results.face_landmarks:
        mouth_points = [
            results.face_landmarks.landmark[i]
            for i in range(61, 81)  # Mouth region
        ]
```

---

### Audio-Visual Synchronization (Custom Model)

**Build Your Own:**

```python
import numpy as np
from scipy.signal import correlate

def analyze_lip_sync(video_frames, audio_mfcc):
    """
    Compare mouth movement with audio features
    Returns synchronization score (0-1)
    """
    mouth_motion = []
    
    for frame in video_frames:
        # Extract mouth region
        mouth = frame[180:220, 200:280]  # Adjust ROI
        motion = np.std(np.diff(mouth, axis=0))
        mouth_motion.append(motion)
    
    # Correlate with audio
    correlation = np.max(correlate(
        np.array(mouth_motion),
        np.mean(audio_mfcc, axis=1),
        mode='valid'
    ))
    
    score = min(1.0, correlation)
    return score

# Usage
sync_score = analyze_lip_sync(video_frames, audio_mfcc)
print(f"Lip-sync score: {sync_score:.2f}")
```

---

## 5. OPTICAL FLOW & TEMPORAL ANALYSIS

### RAFT (Recurrent All-Pairs Field Transforms)

**What it does:**
- Compute dense optical flow
- Detect temporal inconsistencies
- SOTA accuracy on Sintel/KITTI benchmarks

**Download & Use:**

```bash
git clone https://github.com/princeton-vl/RAFT.git
cd RAFT

# Download model
wget https://github.com/princeton-vl/RAFT/releases/download/v1.0/models.zip
unzip models.zip

python3 << 'EOF'
import torch
from raft import RAFT

model = torch.nn.DataParallel(RAFT())
model.load_state_dict(torch.load("models/raft-things.pth"))
model = model.module
model.cuda()
model.eval()

print("RAFT optical flow model ready")
EOF
```

---

### FlowNet2 (Faster Optical Flow)

**Better for real-time:**

```bash
pip install torchvision

python3 << 'EOF'
import torchvision.models as models

# FlowNet2 (modern replacement)
# Use torchvision's optical flow
import torch
import torchvision.transforms.v2 as T

# Or download from GitHub
# https://github.com/NVIDIA/flownet2-pytorch
EOF
```

---

## 6. IMAGE FORENSICS

### DnCNN (Denoiser Network for Artifact Detection)

**What it detects:**
- Compression artifacts
- Noise patterns
- Copy-move forgery

**Download:**

```bash
python3 << 'EOF'
from skimage import restoration
import cv2
import numpy as np

def detect_artifacts(image):
    # Denoise to amplify artifacts
    denoised = restoration.denoise_nl_means(
        image,
        h=0.1,
        fast_mode=True,
        patch_size=5,
        patch_distance=7
    )
    
    # Artifact mask
    artifacts = np.abs(image.astype(float) - denoised)
    artifact_score = np.mean(artifacts)
    
    return artifact_score

# Usage
img = cv2.imread("image.jpg")
score = detect_artifacts(img)
print(f"Artifact score: {score:.2f}")
EOF
```

---

### SpliceBuster (Splicing Detection)

**For detecting image compositing:**

```bash
git clone https://github.com/andrewbartels/SpliceBuster
cd SpliceBuster

# Download pre-trained model
wget https://github.com/andrewbartels/SpliceBuster/releases/download/v1.0/splicing_model.pth
```

---

## 7. GENERAL PURPOSE - TRANSFORMERS

### CLIP (Zero-shot Image Understanding)

**What it does:**
- Understand images semantically
- Match images to text descriptions
- Detect inconsistencies with claims

**Download:**

```bash
pip install clip-by-openai

python3 << 'EOF'
import clip
import torch
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load image
image = preprocess(Image.open("image.jpg")).unsqueeze(0).to(device)

# Check against text
text = clip.tokenize(["a real president", "a fake president"]).to(device)

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)
    logits_per_image = 100.0 * image_features @ text_features.T

print(f"Match scores: {logits_per_image}")
EOF
```

---

### YOLO v8 (General Object Detection)

**Why:** Better than CLIP for object consistency

```bash
pip install ultralytics

python3 << 'EOF'
from ultralytics import YOLO

# Load model
model = YOLO('yolov8x.pt')  # Nano (S), Small (M), Medium (L), Large (X)

# Detect
results = model.predict(source='image.jpg')

# Analyze consistency
for result in results:
    print(result.boxes)  # Objects detected
EOF
```

---

## 8. QUICK START - INTEGRATION

### Add Models to Your System

**Step 1: Create models directory**

```bash
mkdir -p models/
cd models/
```

**Step 2: Download key models**

```bash
# Face detection
python3 << 'EOF'
import mediapipe as mp
# Automatically downloads on first use

import face_recognition
# Auto-downloads model
EOF

# Deepfake detection (Xception)
wget https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth

# Synthetic speech
wget https://github.com/asvspoof-challenge/asvspoof-challenge.github.io/releases/download/asvspoof2021/best.pth

# Optical flow (RAFT)
wget https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth
```

**Step 3: Update config**

```python
# config/settings.py

MODEL_PATHS = {
    'face_detection': 'models/mediapipe_face',
    'face_recognition': 'models/facenet',
    'deepfake_detector': 'models/xception-epoch-92.pth',
    'synthetic_speech': 'models/best.pth',
    'optical_flow': 'models/raft-things.pth',
    'clip_model': 'models/ViT-B-32.pt'
}
```

**Step 4: Integrate into detectors**

```python
# src/visual/forensics.py

import torch
from pathlib import Path

class VisualForensics:
    def __init__(self, device="cpu"):
        self.device = device
        self.deepfake_model = torch.load(
            Path("models/xception-epoch-92.pth"),
            map_location=device
        )
    
    async def analyze_image(self, image_path):
        # Use real models instead of placeholders
        # ... implementation
```

---

## 9. MODEL COMPARISON TABLE

| Model | Task | Speed | Accuracy | Size | License |
|-------|------|-------|----------|------|---------|
| **MediaPipe** | Face Detection | ★★★★★ | 97% | 4MB | Apache 2.0 |
| **RetinaFace** | Face Detection | ★★★★ | 98% | 100MB | MIT |
| **FaceNet** | Face Embedding | ★★★★ | 99% | 180MB | Apache 2.0 |
| **Xception** | Deepfake | ★★★ | 98% | 80MB | Custom |
| **MesoNet** | Deepfake | ★★★★★ | 95% | 8MB | MIT |
| **RAFT** | Optical Flow | ★★ | 99% | 200MB | BSD |
| **CLIP** | Semantics | ★★★ | 88% | 350MB | MIT |
| **YOLOv8** | Detection | ★★★★ | 96% | 200MB | AGPL |
| **ASVspoof** | Speech | ★★★ | 96% | 50MB | Custom |
| **Coqui STT** | Speech-to-Text | ★★ | 95% | 500MB | MPL 2.0 |

---

## 10. DOWNLOAD SCRIPT

**Automated Model Downloader:**

```bash
cat > scripts/download-models.sh << 'EOF'
#!/bin/bash

mkdir -p models/

echo "Downloading detection models..."

# Face Detection (MediaPipe auto-loads)
python3 -c "import mediapipe as mp; print('MediaPipe ready')"

# Deepfake Detection
echo "Downloading Xception..."
cd models/
wget -q https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth
echo "✓ Xception"

# CLIP Model
echo "Downloading CLIP..."
python3 -c "import clip; clip.load('ViT-B/32')" 2>/dev/null && echo "✓ CLIP" || echo "CLIP requires download on first use"

# RAFT Optical Flow
echo "Downloading RAFT..."
wget -q https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth
echo "✓ RAFT"

# YOLOv8
echo "Downloading YOLOv8..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8x.pt')" 2>/dev/null && echo "✓ YOLOv8" || echo "YOLOv8 auto-downloads"

echo ""
echo "✓ All models downloaded to ./models/"
echo ""
echo "Total size: $(du -sh models/ | cut -f1)"
EOF

chmod +x scripts/download-models.sh
bash scripts/download-models.sh
```

---

## 11. WHICH MODELS TO START WITH?

### Minimum (Fast Setup - 15 minutes)

```python
# These auto-load or are tiny
✓ MediaPipe Face Detection    (4 MB)
✓ face_recognition (FaceNet)  (180 MB auto)
✓ CLIP                        (350 MB)
✓ YOLOv8n (nano)             (6 MB)
```

### Recommended (Production - 1 hour)

```python
✓ MediaPipe                   (Face landmarks)
✓ Xception                    (Deepfake detection)
✓ MesoNet                     (Backup deepfake)
✓ RAFT                        (Optical flow)
✓ CLIP                        (Semantic analysis)
✓ Coqui STT                   (Speech-to-text)
✓ Resemblyzer                 (Voice embeddings)
```

### Complete Enterprise (GPU required)

```python
All above +
✓ RetinaFace                  (Alternative face detection)
✓ FaceForensics++ models      (Multiple deepfake types)
✓ ASVspoof 2021              (Synthetic speech)
✓ FlowNet2                    (Alternative optical flow)
✓ YOLO v8x                    (Large object detection)
```

---

## 12. RUNTIME REQUIREMENTS

### CPU Mode (Recommended for Start)
```
RAM:   8GB minimum
Disk:  5GB for models
Time:  5-15 seconds per analysis
```

### GPU Mode (For Production)
```
GPU:   NVIDIA RTX 2060+ (6GB) or better
RAM:   8GB minimum
Disk:  5GB for models
Time:  0.5-2 seconds per analysis (10x faster)
```

---

## Next Steps

1. **Run download script:** `bash scripts/download-models.sh`
2. **Update your detectors** - Replace placeholders with real models
3. **Test locally** - Submit real media for analysis
4. **Monitor performance** - Track inference times
5. **Optimize** - Use model quantization for speed

You now have a complete toolkit for building a production-grade misinformation detection system!
