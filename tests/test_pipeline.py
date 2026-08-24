import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

class TestVisualForensics:
    """Test visual forensics pipeline."""
    
    @pytest.mark.asyncio
    async def test_image_analysis_basic(self):
        """Test basic image analysis."""
        from src.visual.forensics import VisualForensics
        
        forensics = VisualForensics(device="cpu")
        
        # Create dummy image
        import cv2
        import numpy as np
        test_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        test_path = "/tmp/test_image.jpg"
        cv2.imwrite(test_path, test_image)
        
        result = await forensics.analyze_image(test_path)
        
        assert "scores" in result
        assert "manipulation_probability" in result["scores"]
        assert 0 <= result["scores"]["manipulation_probability"] <= 1

class TestAudioForensics:
    """Test audio forensics pipeline."""
    
    @pytest.mark.asyncio
    async def test_audio_analysis_basic(self):
        """Test basic audio analysis."""
        from src.audio.forensics import AudioForensics
        import numpy as np
        import soundfile as sf
        
        forensics = AudioForensics(device="cpu")
        
        # Create dummy audio
        sr = 16000
        duration = 2
        audio = np.random.randn(sr * duration).astype(np.float32) * 0.1
        test_path = "/tmp/test_audio.wav"
        sf.write(test_path, audio, sr)
        
        result = await forensics.analyze(test_path)
        
        assert "scores" in result
        assert "synthetic_speech_probability" in result["scores"]
        assert result["duration_seconds"] > 0

class TestClaimExtractor:
    """Test claim extraction."""
    
    @pytest.mark.asyncio
    async def test_claim_extraction_basic(self):
        """Test basic claim extraction."""
        from src.claim.extractor import ClaimExtractor
        
        text = "The president announced a policy change yesterday."
        
        claims = await ClaimExtractor.extract(text)
        
        assert len(claims) > 0
        assert "statement" in claims[0]

class TestFusion:
    """Test multimodal fusion."""
    
    @pytest.mark.asyncio
    async def test_fusion_basic(self):
        """Test basic fusion operation."""
        from src.fusion.multimodal import MultimodalFusion
        
        fusion = MultimodalFusion()
        
        visual_scores = {
            "manipulation_probability": 0.3,
            "synthetic_media_probability": 0.2,
            "face_boundary_artifacts": 0.1
        }
        
        temporal_scores = {
            "optical_flow_consistency": 0.9,
            "motion_continuity": 0.85
        }
        
        audio_scores = {
            "synthetic_speech_probability": 0.1,
            "voice_cloning_probability": 0.05,
            "speaker_consistency": 0.95
        }
        
        lip_sync_scores = {
            "lip_sync_consistency": 0.8
        }
        
        provenance_scores = {
            "confidence": 0.5
        }
        
        result = await fusion.fuse(
            visual_scores=visual_scores,
            temporal_scores=temporal_scores,
            audio_scores=audio_scores,
            lip_sync_scores=lip_sync_scores,
            provenance_scores=provenance_scores
        )
        
        assert "manipulation_probability" in result
        assert 0 <= result["manipulation_probability"] <= 1
        assert 0 <= result["overall_confidence"] <= 1

class TestClassification:
    """Test classification engine."""
    
    def test_media_classification(self):
        """Test media authenticity classification."""
        from src.fusion.classification import ClassificationEngine
        
        # Likely authentic
        cls = ClassificationEngine.classify_media(
            manipulation_prob=0.1,
            synthetic_prob=0.2,
            confidence=0.8
        )
        assert cls == "LIKELY_AUTHENTIC"
        
        # Manipulated
        cls = ClassificationEngine.classify_media(
            manipulation_prob=0.8,
            synthetic_prob=0.2,
            confidence=0.8
        )
        assert cls == "MANIPULATED"
        
        # AI Generated
        cls = ClassificationEngine.classify_media(
            manipulation_prob=0.2,
            synthetic_prob=0.85,
            confidence=0.8
        )
        assert cls == "AI_GENERATED"

class TestEvidenceRetrieval:
    """Test evidence retrieval."""
    
    @pytest.mark.asyncio
    async def test_evidence_retrieval_basic(self):
        """Test basic evidence retrieval."""
        from src.retrieval.evidence import EvidenceRetrieval
        
        retrieval = EvidenceRetrieval()
        
        evidence = await retrieval.retrieve(
            query="test event",
            claim={"statement": "Test claim"}
        )
        
        assert isinstance(evidence, list)
        if len(evidence) > 0:
            assert "source" in evidence[0]
            assert "relationship" in evidence[0]

class TestAnalysisPipeline:
    """Test full analysis pipeline."""
    
    @pytest.mark.asyncio
    async def test_pipeline_basic(self):
        """Test basic pipeline execution."""
        from src.inference.pipeline import AnalysisPipeline
        import cv2
        import numpy as np
        
        pipeline = AnalysisPipeline(device="cpu")
        
        # Create dummy image
        test_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        test_path = "/tmp/test_pipeline.jpg"
        cv2.imwrite(test_path, test_image)
        
        result = await pipeline.analyze(
            task_id="test-task-001",
            media_path=test_path,
            media_type="image",
            claim="This is a test image",
            include_evidence_graph=False
        )
        
        assert "classification" in result
        assert "overall_confidence" in result
        assert 0 <= result["overall_confidence"] <= 1
        assert "processing_time_seconds" in result
        assert result["processing_time_seconds"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
