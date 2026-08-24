"""
Ensemble Configuration
Centralized configuration for all ensemble models and parameters.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class DeviceType(Enum):
    """Supported device types."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Metal


class ModelType(Enum):
    """Model categories."""
    VISUAL = "visual"
    AUDIO = "audio"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    type: ModelType
    model_category: str
    size_mb: int
    accuracy: float
    speed: str  # e.g., "fast", "medium", "slow"
    weight: float
    enabled: bool = True
    auto_load: bool = False
    url: Optional[str] = None
    local_path: Optional[str] = None
    description: str = ""


class EnsembleConfig:
    """Master ensemble configuration."""
    
    # Device settings
    device: str = "cpu"
    use_mixed_precision: bool = False
    num_workers: int = 4
    batch_size: int = 1
    
    # Model paths
    model_dir: str = "models"
    cache_dir: str = ".cache"
    
    # Ensemble settings
    fusion_method: str = "weighted_average"  # or "logistic_regression"
    calibrate_probabilities: bool = True
    confidence_threshold: float = 0.5
    
    # Performance settings
    enable_async: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3
    
    # Logging settings
    log_level: str = "INFO"
    log_predictions: bool = True
    save_evidence: bool = True
    
    # Model Definitions
    MODELS: Dict[str, ModelConfig] = {
        # Visual Deepfake Detection
        "xception": ModelConfig(
            name="Xception",
            type=ModelType.VISUAL,
            model_category="Deepfake Detection (Primary)",
            size_mb=107,
            accuracy=0.98,
            speed="medium",
            weight=0.25,
            url="https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth",
            local_path="models/xception-epoch-92.pth",
            description="Pre-trained Xception for deepfake and face manipulation detection"
        ),
        
        "mesonet": ModelConfig(
            name="MesoNet",
            type=ModelType.VISUAL,
            model_category="Deepfake Detection (Backup)",
            size_mb=8,
            accuracy=0.95,
            speed="fast",
            weight=0.15,
            url="https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5",
            local_path="models/MesoNet-4_DF.h5",
            description="Lightweight deepfake detector for edge deployment"
        ),
        
        "retinaface": ModelConfig(
            name="RetinaFace",
            type=ModelType.VISUAL,
            model_category="Face Detection",
            size_mb=100,
            accuracy=0.98,
            speed="medium",
            weight=0.05,
            url="https://github.com/serengoodbroad/RetinaFace_Pytorch/releases/download/latest/mobilenet0.25_Final.pth",
            local_path="models/retinaface.pth",
            description="Advanced face detection with extreme angle handling"
        ),
        
        "mediapipe": ModelConfig(
            name="MediaPipe",
            type=ModelType.VISUAL,
            model_category="Face Analysis",
            size_mb=50,
            accuracy=0.97,
            speed="fast",
            weight=0.05,
            auto_load=True,
            description="Face landmarks and head pose estimation"
        ),
        
        "clip": ModelConfig(
            name="CLIP",
            type=ModelType.SEMANTIC,
            model_category="Semantic Understanding",
            size_mb=350,
            accuracy=0.88,
            speed="medium",
            weight=0.10,
            auto_load=True,
            description="Vision-language model for semantic analysis"
        ),
        
        "yolov8": ModelConfig(
            name="YOLOv8",
            type=ModelType.SEMANTIC,
            model_category="Object Detection",
            size_mb=200,
            accuracy=0.96,
            speed="fast",
            weight=0.05,
            auto_load=True,
            description="Real-time object detection and tracking"
        ),
        
        # Audio Analysis
        "wav2vec2": ModelConfig(
            name="Wav2Vec2",
            type=ModelType.AUDIO,
            model_category="Speech-to-Text",
            size_mb=400,
            accuracy=0.95,
            speed="medium",
            weight=0.10,
            auto_load=True,
            description="Self-supervised speech recognition"
        ),
        
        "resemblyzer": ModelConfig(
            name="Resemblyzer",
            type=ModelType.AUDIO,
            model_category="Voice Verification",
            size_mb=30,
            accuracy=0.94,
            speed="fast",
            weight=0.10,
            auto_load=True,
            description="Speaker embedding and verification"
        ),
        
        "asvspoof": ModelConfig(
            name="ASVspoof",
            type=ModelType.AUDIO,
            model_category="Synthetic Speech Detection",
            size_mb=50,
            accuracy=0.96,
            speed="medium",
            weight=0.08,
            local_path="models/asvspoof_model.pth",
            description="Detects synthetic/cloned voices"
        ),
        
        # Temporal Analysis
        "raft": ModelConfig(
            name="RAFT",
            type=ModelType.TEMPORAL,
            model_category="Optical Flow",
            size_mb=244,
            accuracy=0.99,
            speed="slow",
            weight=0.12,
            url="https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth",
            local_path="models/raft-things.pth",
            description="State-of-the-art optical flow for temporal consistency"
        ),
    }
    
    # Model weights (calibrated)
    WEIGHTS: Dict[str, float] = {
        "xception": 0.25,      # Primary deepfake detector
        "mesonet": 0.15,       # Backup deepfake detector
        "retinaface": 0.05,    # Face quality/presence
        "mediapipe": 0.05,     # Face consistency
        "clip": 0.10,          # Semantic understanding
        "yolov8": 0.05,        # Object consistency
        "wav2vec2": 0.10,      # Speech extraction
        "resemblyzer": 0.10,   # Voice consistency
        "asvspoof": 0.08,      # Synthetic speech
        "raft": 0.12,          # Temporal consistency
    }
    
    # Signal weights for fusion
    SIGNAL_WEIGHTS: Dict[str, float] = {
        "visual": 0.30,        # Visual manipulation signals
        "ensemble": 0.25,      # Overall ensemble vote
        "temporal": 0.15,      # Frame-to-frame consistency
        "audio": 0.15,         # Audio authenticity
        "lip_sync": 0.10,      # Lip-audio sync
        "provenance": 0.05,    # Source credibility
    }
    
    # Thresholds for classification
    CLASSIFICATION_THRESHOLDS: Dict[str, float] = {
        "authentic": 0.30,        # < 0.30 = authentic
        "uncertain": 0.70,        # 0.30-0.70 = uncertain
        "manipulated": 1.00,      # > 0.70 = manipulated
    }
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLDS: Dict[str, float] = {
        "high": 0.85,
        "medium": 0.60,
        "low": 0.30,
    }
    
    # Model categories for analysis
    REQUIRED_MODELS_FOR_VIDEO: List[str] = [
        "xception",
        "raft",
        "wav2vec2",
    ]
    
    REQUIRED_MODELS_FOR_IMAGE: List[str] = [
        "xception",
        "mesonet",
    ]
    
    REQUIRED_MODELS_FOR_AUDIO: List[str] = [
        "wav2vec2",
        "asvspoof",
        "resemblyzer",
    ]
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return cls.MODELS.get(model_name)
    
    @classmethod
    def get_models_by_type(cls, model_type: ModelType) -> List[str]:
        """Get all models of a specific type."""
        return [
            name for name, config in cls.MODELS.items()
            if config.type == model_type
        ]
    
    @classmethod
    def get_model_weight(cls, model_name: str) -> float:
        """Get weight for a model."""
        return cls.WEIGHTS.get(model_name, 0.0)
    
    @classmethod
    def normalize_weights(cls) -> Dict[str, float]:
        """Get normalized weights (sum to 1)."""
        total = sum(cls.WEIGHTS.values())
        if total > 0:
            return {name: weight / total for name, weight in cls.WEIGHTS.items()}
        return cls.WEIGHTS
    
    @classmethod
    def get_total_storage_mb(cls) -> int:
        """Calculate total storage needed for all models."""
        auto_load_size = sum(
            config.size_mb for config in cls.MODELS.values()
            if config.auto_load
        )
        downloadable_size = sum(
            config.size_mb for config in cls.MODELS.values()
            if config.url and not config.auto_load
        )
        return auto_load_size + downloadable_size
    
    @classmethod
    def get_available_models_summary(cls) -> Dict[str, any]:
        """Get summary of all available models."""
        return {
            "total_models": len(cls.MODELS),
            "total_storage_mb": cls.get_total_storage_mb(),
            "by_type": {
                model_type.value: cls.get_models_by_type(model_type)
                for model_type in ModelType
            },
            "auto_load": [
                name for name, config in cls.MODELS.items()
                if config.auto_load
            ],
            "downloadable": [
                name for name, config in cls.MODELS.items()
                if config.url
            ],
        }


# Preset configurations for different scenarios
class PresetConfigs:
    """Preset configurations for common use cases."""
    
    @staticmethod
    def lightweight() -> EnsembleConfig:
        """Lightweight configuration (edge/mobile)."""
        config = EnsembleConfig()
        config.device = "cpu"
        config.batch_size = 1
        config.num_workers = 1
        config.use_mixed_precision = True
        
        # Use only fast models
        for model_name, model_config in config.MODELS.items():
            if model_config.speed != "fast":
                model_config.enabled = False
        
        return config
    
    @staticmethod
    def balanced() -> EnsembleConfig:
        """Balanced configuration (default)."""
        config = EnsembleConfig()
        config.device = "cpu"
        config.batch_size = 4
        config.num_workers = 4
        return config
    
    @staticmethod
    def high_accuracy() -> EnsembleConfig:
        """High accuracy configuration (server/GPU)."""
        config = EnsembleConfig()
        config.device = "cuda"
        config.batch_size = 16
        config.num_workers = 8
        config.use_mixed_precision = True
        
        # Enable all models
        for model_config in config.MODELS.values():
            model_config.enabled = True
        
        return config
    
    @staticmethod
    def fast_detection() -> EnsembleConfig:
        """Fast detection configuration."""
        config = EnsembleConfig()
        config.device = "cpu"
        config.timeout_seconds = 30
        config.batch_size = 1
        
        # Use only primary and fast models
        for model_name, model_config in config.MODELS.items():
            if model_name not in ["xception", "mesonet", "wav2vec2"]:
                model_config.enabled = False
        
        return config


def get_config(preset: str = "balanced", device: str = "cpu") -> EnsembleConfig:
    """Get configuration by preset name."""
    presets = {
        "lightweight": PresetConfigs.lightweight,
        "balanced": PresetConfigs.balanced,
        "high_accuracy": PresetConfigs.high_accuracy,
        "fast_detection": PresetConfigs.fast_detection,
    }
    
    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}")
    
    config = presets[preset]()
    if device:
        config.device = device
    
    return config


# Default configuration
DEFAULT_CONFIG = EnsembleConfig()
