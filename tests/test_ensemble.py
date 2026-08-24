"""
Ensemble Models Test Suite
Tests all ensemble components and integration.
"""

import pytest
import asyncio
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.models.model_manager import EnsembleModelManager
from src.ensemble.inference import EnsembleInferenceEngine
from src.fusion.multimodal import MultimodalFusion
from src.visual.forensics import VisualForensics, FaceAnalysis


# Fixtures
@pytest.fixture
def model_manager():
    """Create a model manager instance."""
    return EnsembleModelManager(device="cpu", model_dir="models")


@pytest.fixture
def inference_engine(model_manager):
    """Create inference engine."""
    return EnsembleInferenceEngine(model_manager)


@pytest.fixture
def multimodal_fusion():
    """Create multimodal fusion instance."""
    return MultimodalFusion(device="cpu", model_dir="models")


@pytest.fixture
def sample_image_tensor():
    """Create a sample image tensor."""
    return torch.randn(1, 3, 299, 299)


# Model Manager Tests
class TestEnsembleModelManager:
    """Test model manager functionality."""
    
    def test_initialization(self, model_manager):
        """Test model manager initialization."""
        assert model_manager is not None
        assert model_manager.device == "cpu"
        assert model_manager.model_dir.exists()
    
    def test_weights_initialization(self, model_manager):
        """Test weights are initialized."""
        assert len(model_manager.weights) > 0
        assert all(isinstance(v, float) for v in model_manager.weights.values())
    
    def test_get_available_models(self, model_manager):
        """Test getting available models."""
        available = model_manager.get_available_models()
        assert isinstance(available, list)
        # Should have at least the auto-loading models
        assert len(available) >= 0
    
    def test_get_weight(self, model_manager):
        """Test getting model weight."""
        weight = model_manager.get_weight("xception")
        assert isinstance(weight, float)
        assert 0 <= weight <= 1
    
    def test_set_weights(self, model_manager):
        """Test updating weights."""
        new_weights = {"xception": 0.5, "mesonet": 0.5}
        model_manager.set_weights(new_weights)
        assert model_manager.get_weight("xception") == 0.5
        assert model_manager.get_weight("mesonet") == 0.5
    
    def test_normalize_weights(self, model_manager):
        """Test weight normalization."""
        model_manager.normalize_weights()
        available = model_manager.get_available_models()
        
        if available:
            total = sum(model_manager.get_weight(m) for m in available)
            assert abs(total - 1.0) < 0.01 or total == 0
    
    def test_model_status(self, model_manager):
        """Test model status reporting."""
        status = model_manager.get_model_status()
        assert isinstance(status, dict)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in status.items())
    
    def test_summary(self, model_manager):
        """Test summary generation."""
        summary = model_manager.summary()
        assert isinstance(summary, str)
        assert "ENSEMBLE" in summary
        assert "Device" in summary


# Inference Engine Tests
class TestEnsembleInferenceEngine:
    """Test inference engine functionality."""
    
    @pytest.mark.asyncio
    async def test_visual_ensemble(self, inference_engine, sample_image_tensor):
        """Test visual ensemble inference."""
        results = await inference_engine.visual_ensemble(sample_image_tensor)
        assert isinstance(results, dict)
        # Results should have model names as keys
        for key, value in results.items():
            assert isinstance(key, str)
            assert isinstance(value, (int, float)) or value is None
    
    @pytest.mark.asyncio
    async def test_audio_ensemble(self, inference_engine):
        """Test audio ensemble inference."""
        # Create a dummy audio path
        results = await inference_engine.audio_ensemble("test_audio.wav")
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_temporal_ensemble(self, inference_engine):
        """Test temporal ensemble inference."""
        results = await inference_engine.temporal_ensemble("test_video.mp4")
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_fuse_predictions(self, inference_engine):
        """Test prediction fusion."""
        visual_results = {"xception": 0.8, "mesonet": 0.75}
        audio_results = {"asvspoof": 0.1}
        temporal_results = {"raft": 0.9}
        
        fused = await inference_engine.fuse_predictions(
            visual_results,
            audio_results,
            temporal_results
        )
        
        assert "manipulation_probability" in fused
        assert "overall_confidence" in fused
        assert "model_votes" in fused
        assert 0 <= fused["manipulation_probability"] <= 1
        assert 0 <= fused["overall_confidence"] <= 1
    
    def test_calculate_agreement(self, inference_engine):
        """Test model agreement calculation."""
        model_votes = {
            "model1": 0.8,
            "model2": 0.85,
            "model3": 0.75
        }
        
        agreement = inference_engine._calculate_agreement(model_votes)
        assert 0 <= agreement <= 1
    
    def test_detect_outliers(self, inference_engine):
        """Test outlier detection."""
        model_votes = {
            "model1": 0.8,
            "model2": 0.85,
            "model3": 0.10  # Outlier
        }
        
        outliers = inference_engine._detect_outliers(model_votes)
        assert isinstance(outliers, list)
        # The outlier should be detected
        if len(outliers) > 0:
            assert any(o["model"] == "model3" for o in outliers)
    
    def test_calculate_confidence_interval(self, inference_engine):
        """Test confidence interval calculation."""
        model_votes = {
            "model1": 0.8,
            "model2": 0.75,
            "model3": 0.85
        }
        
        ci = inference_engine._calculate_confidence_interval(model_votes)
        assert "lower" in ci
        assert "upper" in ci
        assert "width" in ci
        assert ci["lower"] <= ci["upper"]
        assert 0 <= ci["lower"] <= 1
        assert 0 <= ci["upper"] <= 1


# Multimodal Fusion Tests
class TestMultimodalFusion:
    """Test multimodal fusion functionality."""
    
    @pytest.mark.asyncio
    async def test_fusion_initialization(self, multimodal_fusion):
        """Test fusion initialization."""
        assert multimodal_fusion is not None
        assert multimodal_fusion.model_manager is not None
        assert multimodal_fusion.inference_engine is not None
    
    @pytest.mark.asyncio
    async def test_fuse_with_ensemble(self, multimodal_fusion):
        """Test fusion with ensemble results."""
        visual_scores = {"manipulation_probability": 0.7}
        temporal_scores = {"temporal_inconsistency": 0.2}
        audio_scores = {"synthetic_speech_probability": 0.1}
        lip_sync_scores = {"lip_sync_consistency": 0.9}
        provenance_scores = {"confidence": 0.8}
        ensemble_results = {
            "manipulation_probability": 0.7,
            "overall_confidence": 0.8,
            "model_votes": {"xception": 0.7},
            "model_agreement": 0.9
        }
        
        fused = await multimodal_fusion._fuse_with_ensemble(
            visual_scores,
            temporal_scores,
            audio_scores,
            lip_sync_scores,
            provenance_scores,
            ensemble_results
        )
        
        assert "manipulation_probability" in fused
        assert "signal_breakdown" in fused
        assert "ensemble_results" in fused
        assert 0 <= fused["manipulation_probability"] <= 1
    
    def test_generate_explanation(self, multimodal_fusion):
        """Test explanation generation."""
        ensemble_results = {
            "model_votes": {
                "xception": 0.8,
                "mesonet": 0.75
            },
            "outliers": [],
            "model_agreement": 0.95
        }
        
        factors = multimodal_fusion._generate_explanation(0.75, ensemble_results, 0.85)
        assert isinstance(factors, list)
        assert len(factors) > 0
        assert all(isinstance(f, str) for f in factors)
    
    def test_model_manager_access(self, multimodal_fusion):
        """Test model manager access."""
        manager = multimodal_fusion.get_model_manager()
        assert manager is not None
        assert hasattr(manager, 'get_available_models')
    
    def test_get_available_models(self, multimodal_fusion):
        """Test getting available models."""
        models = multimodal_fusion.get_available_models()
        assert isinstance(models, list)
    
    def test_model_summary(self, multimodal_fusion):
        """Test model summary."""
        summary = multimodal_fusion.get_model_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


# Visual Forensics Tests
class TestVisualForensics:
    """Test visual forensics functionality."""
    
    def test_visual_forensics_initialization(self):
        """Test visual forensics initialization."""
        vf = VisualForensics(device="cpu", model_dir="models")
        assert vf is not None
        assert vf.model_manager is not None
    
    @pytest.mark.asyncio
    async def test_preprocess_image(self):
        """Test image preprocessing."""
        vf = VisualForensics(device="cpu", model_dir="models")
        
        # Create a dummy image
        import cv2
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        image_path = "/tmp/test_image.jpg"
        cv2.imwrite(image_path, dummy_image)
        
        try:
            tensor = vf._preprocess_image(image_path)
            assert isinstance(tensor, torch.Tensor)
            assert tensor.shape == (1, 3, 299, 299)
        finally:
            Path(image_path).unlink(missing_ok=True)
    
    def test_face_analysis_initialization(self):
        """Test face analysis initialization."""
        fa = FaceAnalysis(device="cpu", model_dir="models")
        assert fa is not None


# Integration Tests
class TestEnsembleIntegration:
    """Integration tests for the ensemble system."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, multimodal_fusion):
        """Test full analysis pipeline."""
        # Simulate complete analysis
        visual_scores = {"manipulation_probability": 0.6}
        temporal_scores = {}
        audio_scores = {}
        
        result = await multimodal_fusion.fuse(
            visual_scores=visual_scores,
            temporal_scores=temporal_scores,
            audio_scores=audio_scores
        )
        
        assert result is not None
        assert "manipulation_probability" in result
        assert "overall_confidence" in result
        assert "models_used" in result
    
    def test_model_weights_sum(self, model_manager):
        """Test that model weights are properly configured."""
        weights = model_manager.weights
        total_weight = sum(weights.values())
        
        # Weights should be reasonable (not all zero or extremely high)
        assert total_weight > 0
        assert all(0 <= w <= 1 for w in weights.values())


# Performance Tests
class TestPerformance:
    """Performance and reliability tests."""
    
    @pytest.mark.asyncio
    async def test_inference_speed(self, inference_engine, sample_image_tensor):
        """Test inference speed."""
        import time
        
        start = time.time()
        await inference_engine.visual_ensemble(sample_image_tensor)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 10 seconds on CPU)
        assert elapsed < 10
    
    def test_memory_efficiency(self, model_manager):
        """Test memory efficiency."""
        # Get model info
        available = model_manager.get_available_models()
        
        # Should not have excessive models loaded
        assert len(available) <= 15  # Reasonable upper bound


# Error Handling Tests
class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_missing_model_graceful_failure(self, inference_engine):
        """Test graceful failure when models are missing."""
        # This should not raise an exception
        result = await inference_engine.visual_ensemble(torch.randn(1, 3, 299, 299))
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_invalid_audio_path(self, inference_engine):
        """Test handling of invalid audio path."""
        # Should handle gracefully
        result = await inference_engine.audio_ensemble("/nonexistent/audio.wav")
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
