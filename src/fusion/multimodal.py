"""
Enhanced Multimodal Fusion using Ensemble Results
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LogisticRegression
import pickle
import os
import asyncio

from src.models.model_manager import EnsembleModelManager
from src.ensemble.inference import EnsembleInferenceEngine

logger = logging.getLogger(__name__)


class MultimodalFusion:
    """Enhanced fusion layer combining ensemble and forensic signals."""
    
    def __init__(self, device: str = "cpu", model_dir: str = "models"):
        self.device = device
        self.model_manager = EnsembleModelManager(device=device, model_dir=model_dir)
        self.inference_engine = EnsembleInferenceEngine(self.model_manager)
        self.fusion_model = None
        self._load_or_init_fusion_model()
        
        logger.info("Multimodal Fusion initialized with ensemble support")
    
    def _load_or_init_fusion_model(self):
        """Load pre-trained fusion model or initialize new one."""
        model_path = "./models/fusion_model.pkl"
        
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    self.fusion_model = pickle.load(f)
                logger.info("Loaded pre-trained fusion model")
            except Exception as e:
                logger.warning(f"Failed to load fusion model: {e}")
                self._init_fusion_model()
        else:
            self._init_fusion_model()
    
    def _init_fusion_model(self):
        """Initialize fusion model."""
        self.fusion_model = LogisticRegression(
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
            class_weight="balanced"
        )
        logger.info("Initialized logistic regression fusion model")
    
    async def fuse(
        self,
        visual_scores: Dict[str, Any],
        temporal_scores: Dict[str, Any],
        audio_scores: Dict[str, Any],
        lip_sync_scores: Dict[str, float] = None,
        provenance_scores: Dict[str, float] = None,
        ensemble_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fuse multiple forensic signals and ensemble results into calibrated probabilities.
        """
        try:
            logger.info("Starting multimodal fusion...")
            
            # Use ensemble results if provided
            if ensemble_results is None:
                logger.info("Running full ensemble inference...")
                ensemble_results = await self.inference_engine.fuse_predictions(
                    visual_scores,
                    audio_scores,
                    temporal_scores
                )
            
            # Fuse all signals
            fused = await self._fuse_with_ensemble(
                visual_scores,
                temporal_scores,
                audio_scores,
                lip_sync_scores or {},
                provenance_scores or {},
                ensemble_results
            )
            
            logger.info(f"Fusion complete: confidence={fused.get('overall_confidence', 0):.3f}")
            return fused
        
        except Exception as e:
            logger.error(f"Fusion failed: {str(e)}", exc_info=True)
            return self._default_fusion()
    
    async def _fuse_with_ensemble(
        self,
        visual_scores: Dict[str, Any],
        temporal_scores: Dict[str, Any],
        audio_scores: Dict[str, Any],
        lip_sync_scores: Dict[str, float],
        provenance_scores: Dict[str, float],
        ensemble_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fuse signals with ensemble results."""
        
        # Weights (calibrated)
        weights = {
            "visual": 0.30,
            "ensemble": 0.25,
            "temporal": 0.15,
            "audio": 0.15,
            "lip_sync": 0.10,
            "provenance": 0.05
        }
        
        # Extract ensemble manipulation probability
        ensemble_manipulation = ensemble_results.get("manipulation_probability", 0.5)
        ensemble_confidence = ensemble_results.get("overall_confidence", 0.0)
        
        # Visual signal
        visual_manip = visual_scores.get("manipulation_probability", 0.5)
        
        # Temporal signal
        temporal_inconsistency = temporal_scores.get("temporal_inconsistency", 0.5)
        temporal_manip = 1 - temporal_inconsistency  # High inconsistency = high manipulation
        
        # Audio signal
        audio_manip = audio_scores.get("synthetic_speech_probability", 0.5)
        
        # Lip sync signal
        lip_sync_inconsistency = 1 - lip_sync_scores.get("lip_sync_consistency", 0.5)
        
        # Provenance signal
        provenance_confidence = provenance_scores.get("confidence", 0.5)
        
        # Combined manipulation probability
        manipulation_prob = (
            weights["visual"] * visual_manip +
            weights["ensemble"] * ensemble_manipulation +
            weights["temporal"] * temporal_manip +
            weights["audio"] * audio_manip +
            weights["lip_sync"] * lip_sync_inconsistency +
            weights["provenance"] * (1 - provenance_confidence)
        )
        
        # Synthetic media probability
        synthetic_prob = (
            weights["ensemble"] * ensemble_results.get("synthetic_media_probability", 0.5) +
            weights["temporal"] * temporal_manip +
            weights["audio"] * audio_scores.get("voice_cloning_probability", 0.5)
        ) / 3
        
        # Audio manipulation
        audio_manip_prob = (
            0.6 * audio_scores.get("synthetic_speech_probability", 0.5) +
            0.4 * audio_scores.get("voice_cloning_probability", 0.5)
        )
        
        # Overall confidence
        all_confidence_signals = [
            ensemble_confidence,
            abs(visual_manip - 0.5) * 2,
            abs(temporal_manip - 0.5) * 2,
            abs(audio_manip - 0.5) * 2,
            abs(provenance_confidence - 0.5) * 2
        ]
        
        overall_confidence = np.mean(all_confidence_signals)
        
        # Compile result
        fused = {
            "manipulation_probability": float(np.clip(manipulation_prob, 0, 1)),
            "synthetic_media_probability": float(np.clip(synthetic_prob, 0, 1)),
            "audio_manipulation_probability": float(np.clip(audio_manip_prob, 0, 1)),
            "lip_sync_inconsistency": float(np.clip(lip_sync_inconsistency, 0, 1)),
            "overall_confidence": float(np.clip(overall_confidence, 0, 1)),
            
            # Detailed breakdown
            "ensemble_results": ensemble_results,
            "signal_breakdown": {
                "visual": float(visual_manip),
                "ensemble": float(ensemble_manipulation),
                "temporal": float(temporal_manip),
                "audio": float(audio_manip),
                "lip_sync": float(lip_sync_inconsistency),
                "provenance": float(1 - provenance_confidence)
            },
            "signal_weights": weights,
            
            # Model votes
            "model_votes": ensemble_results.get("model_votes", {}),
            "models_used": self.model_manager.get_available_models(),
            "model_agreement": ensemble_results.get("model_agreement", 0.0),
            "confidence_interval": ensemble_results.get("confidence_interval", {}),
            "outliers": ensemble_results.get("outliers", []),
            
            # Interpretability
            "feature_importance": weights,
            "explanation_factors": self._generate_explanation(
                manipulation_prob,
                ensemble_results,
                ensemble_confidence
            )
        }
        
        return fused
    
    def _generate_explanation(
        self,
        manipulation_prob: float,
        ensemble_results: Dict[str, Any],
        ensemble_confidence: float
    ) -> List[str]:
        """Generate human-readable explanation factors."""
        factors = []
        
        model_votes = ensemble_results.get("model_votes", {})
        num_models = len(model_votes)
        
        # Check model agreement
        if num_models > 0:
            numeric_votes = [v for v in model_votes.values() if isinstance(v, (int, float))]
            if numeric_votes:
                agree_threshold = 0.7
                high_votes = sum(1 for v in numeric_votes if v > 0.5)
                
                if high_votes / len(numeric_votes) > agree_threshold:
                    factors.append(f"High model agreement: {high_votes}/{len(numeric_votes)} models vote for manipulation")
                else:
                    factors.append("Mixed model opinions on manipulation")
        
        # Check manipulation probability
        if manipulation_prob > 0.8:
            factors.append("High probability of manipulation detected")
        elif manipulation_prob > 0.6:
            factors.append("Moderate indicators of manipulation")
        elif manipulation_prob > 0.4:
            factors.append("Some suspicious features detected")
        else:
            factors.append("Media appears largely authentic")
        
        # Check ensemble confidence
        if ensemble_confidence > 0.8:
            factors.append("High confidence in ensemble prediction")
        elif ensemble_confidence < 0.3:
            factors.append("Low confidence - uncertain prediction")
        
        # Check outliers
        outliers = ensemble_results.get("outliers", [])
        if outliers:
            factors.append(f"{len(outliers)} model(s) strongly disagree with ensemble")
        
        return factors
    
    @staticmethod
    def _default_fusion() -> Dict[str, Any]:
        """Return default fusion result."""
        return {
            "manipulation_probability": 0.5,
            "synthetic_media_probability": 0.5,
            "audio_manipulation_probability": 0.5,
            "lip_sync_inconsistency": 0.5,
            "overall_confidence": 0.0,
            "model_votes": {},
            "models_used": [],
            "signal_breakdown": {},
            "signal_weights": {},
            "feature_importance": {},
            "explanation_factors": ["Error occurred during fusion"]
        }
    
    @staticmethod
    def _build_feature_vector(
        visual_scores: Dict[str, float],
        temporal_scores: Dict[str, float],
        audio_scores: Dict[str, float],
        lip_sync_scores: Dict[str, float],
        provenance_scores: Dict[str, float]
    ) -> np.ndarray:
        """Build feature vector from all scores."""
        features = []
        features.extend(visual_scores.values())
        features.extend(temporal_scores.values())
        features.extend(audio_scores.values())
        features.extend(lip_sync_scores.values())
        features.extend(provenance_scores.values())
        return np.array(features).reshape(1, -1)
    
    def get_model_manager(self) -> EnsembleModelManager:
        """Get the model manager."""
        return self.model_manager
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.model_manager.get_available_models()
    
    def get_model_summary(self) -> str:
        """Get model summary."""
        return self.model_manager.summary()
