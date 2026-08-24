"""
Ensemble Model Manager
Manages multiple pre-trained models for comprehensive detection.
"""

import torch
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EnsembleModelManager:
    """Manages multiple models for ensemble inference."""
    
    def __init__(self, device: str = "cpu", model_dir: str = "models"):
        self.device = device
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.models = {}
        self.weights = {}
        self.model_status = {}
        
        logger.info(f"Initializing Ensemble Model Manager on {device}")
        self.initialize_ensemble()
    
    def initialize_ensemble(self):
        """Load all models in the ensemble."""
        
        logger.info("=" * 60)
        logger.info("LOADING ENSEMBLE MODELS")
        logger.info("=" * 60)
        
        # Visual models
        self._load_model('xception', self._load_xception)
        self._load_model('mesonet', self._load_mesonet)
        self._load_model('retinaface', self._load_retinaface)
        self._load_model('mediapipe', self._load_mediapipe)
        self._load_model('clip', self._load_clip)
        self._load_model('yolov8', self._load_yolov8)
        
        # Audio models
        self._load_model('wav2vec2', self._load_wav2vec2)
        self._load_model('resemblyzer', self._load_resemblyzer)
        self._load_model('asvspoof', self._load_asvspoof)
        
        # Temporal models
        self._load_model('raft', self._load_raft)
        
        # Set initial weights (calibrated)
        self.weights = {
            'xception': 0.25,      # Primary detector
            'mesonet': 0.15,       # Backup detector
            'retinaface': 0.05,    # Face quality
            'mediapipe': 0.05,     # Face consistency
            'clip': 0.10,          # Semantic analysis
            'yolov8': 0.05,        # Object consistency
            'wav2vec2': 0.10,      # Speech extraction
            'resemblyzer': 0.10,   # Voice consistency
            'asvspoof': 0.08,      # Synthetic speech
            'raft': 0.12           # Temporal analysis
        }
        
        available = self.get_available_models()
        logger.info(f"✓ Ensemble ready with {len(available)} models: {', '.join(available)}")
        logger.info("=" * 60)
    
    def _load_model(self, name: str, loader_fn):
        """Load a model with error handling."""
        try:
            model = loader_fn()
            if model is not None:
                self.models[name] = model
                self.model_status[name] = "loaded"
                logger.info(f"✓ {name.upper():15} - Loaded successfully")
                return True
        except Exception as e:
            self.model_status[name] = f"failed: {str(e)[:50]}"
            logger.warning(f"✗ {name.upper():15} - {str(e)[:50]}")
        
        self.models[name] = None
        return False
    
    def _load_xception(self):
        """Load Xception deepfake detector."""
        model_path = self.model_dir / "xception-epoch-92.pth"
        
        if not model_path.exists():
            return None
        
        try:
            model = torch.load(str(model_path), map_location=self.device)
            model.eval()
            return model
        except Exception:
            return None
    
    def _load_mesonet(self):
        """Load MesoNet lightweight detector."""
        try:
            # Try TensorFlow/Keras
            import tensorflow as tf
            model_path = self.model_dir / "MesoNet-4_DF.h5"
            
            if model_path.exists():
                model = tf.keras.models.load_model(str(model_path))
                return model
        except Exception:
            pass
        
        return None
    
    def _load_retinaface(self):
        """Load RetinaFace face detector."""
        try:
            from retinaface import RetinaFace
            model_path = self.model_dir / "retinaface.pth"
            
            if model_path.exists():
                detector = RetinaFace.RetinaFace.load_from_pretrained(
                    str(model_path),
                    device=self.device
                )
                return detector
        except Exception:
            pass
        
        return None
    
    def _load_mediapipe(self):
        """Load MediaPipe face detection."""
        try:
            import mediapipe as mp
            return mp.solutions.face_detection
        except Exception:
            return None
    
    def _load_clip(self):
        """Load CLIP model."""
        try:
            import clip
            model, preprocess = clip.load("ViT-B/32", device=self.device)
            return {"model": model, "preprocess": preprocess}
        except Exception:
            return None
    
    def _load_yolov8(self):
        """Load YOLOv8."""
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8x.pt')
            return model
        except Exception:
            return None
    
    def _load_wav2vec2(self):
        """Load Wav2Vec2 speech-to-text."""
        try:
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
            processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
            model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
            model.to(self.device)
            return {"model": model, "processor": processor}
        except Exception:
            return None
    
    def _load_resemblyzer(self):
        """Load Resemblyzer voice embeddings."""
        try:
            from resemblyzer import VoiceEncoder
            encoder = VoiceEncoder()
            return encoder
        except Exception:
            return None
    
    def _load_asvspoof(self):
        """Load ASVspoof synthetic speech detector."""
        try:
            model_path = self.model_dir / "asvspoof_model.pth"
            
            if model_path.exists():
                model = torch.load(str(model_path), map_location=self.device)
                model.eval()
                return model
        except Exception:
            pass
        
        return None
    
    def _load_raft(self):
        """Load RAFT optical flow."""
        try:
            model_path = self.model_dir / "raft-things.pth"
            
            if model_path.exists():
                model = torch.load(str(model_path), map_location=self.device)
                model.eval()
                return model
        except Exception:
            pass
        
        return None
    
    def get_model(self, name: str) -> Optional[Any]:
        """Get a specific model."""
        return self.models.get(name)
    
    def get_weight(self, name: str) -> float:
        """Get weight for a model."""
        return self.weights.get(name, 0.0)
    
    def set_weights(self, weights: Dict[str, float]):
        """Update model weights."""
        for name, weight in weights.items():
            if name in self.weights:
                self.weights[name] = weight
        
        logger.info(f"Weights updated: {self.weights}")
    
    def get_available_models(self) -> List[str]:
        """Get list of successfully loaded models."""
        return [name for name, model in self.models.items() if model is not None]
    
    def get_model_status(self) -> Dict[str, str]:
        """Get status of all models."""
        return self.model_status.copy()
    
    def get_total_weight(self) -> float:
        """Get total weight of all models."""
        available = self.get_available_models()
        return sum(self.weights.get(name, 0.0) for name in available)
    
    def normalize_weights(self):
        """Normalize weights so they sum to 1."""
        total = self.get_total_weight()
        if total > 0:
            available = self.get_available_models()
            for name in available:
                self.weights[name] = self.weights[name] / total
    
    def summary(self) -> str:
        """Get human-readable summary."""
        available = self.get_available_models()
        status = self.get_model_status()
        
        lines = [
            "\n" + "=" * 60,
            "ENSEMBLE MODEL SUMMARY",
            "=" * 60,
            f"Device: {self.device}",
            f"Models Loaded: {len(available)}/{len(self.models)}",
            f"Model Directory: {self.model_dir}",
            "",
            "LOADED MODELS:",
        ]
        
        for name in self.models.keys():
            weight = self.weights.get(name, 0.0)
            is_loaded = name in available
            status_icon = "✓" if is_loaded else "✗"
            lines.append(f"  {status_icon} {name:15} - Weight: {weight:.2f}")
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)


def get_model_manager(device: str = "cpu", model_dir: str = "models") -> EnsembleModelManager:
    """Factory function to create model manager."""
    return EnsembleModelManager(device=device, model_dir=model_dir)
