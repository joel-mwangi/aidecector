import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from src.ingestion.handler import IngestHandler
from src.visual.forensics import VisualForensics, FaceAnalysis
from src.audio.forensics import AudioForensics, LipSyncAnalysis
from src.temporal.analysis import TemporalAnalysis
from src.claim.extractor import ClaimExtractor, ClaimVerifier
from src.retrieval.evidence import EvidenceRetrieval, EvidenceGraph
from src.fusion.multimodal import MultimodalFusion
from src.fusion.classification import ClassificationEngine
from src.api.database import Database

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Main analysis pipeline orchestrating all detectors."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.ingest_handler = IngestHandler()
        self.visual_forensics = VisualForensics(device=device)
        self.face_analysis = FaceAnalysis(device=device)
        self.audio_forensics = AudioForensics(device=device)
        self.lip_sync_analysis = LipSyncAnalysis(device=device)
        self.temporal_analysis = TemporalAnalysis(device=device)
        self.evidence_retrieval = EvidenceRetrieval()
        self.multimodal_fusion = MultimodalFusion()
        self.db = Database()
    
    async def analyze(
        self,
        task_id: str,
        media_path: str,
        media_type: str,
        claim: str = None,
        include_evidence_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Execute full analysis pipeline.
        
        Returns comprehensive assessment with all forensic scores, evidence, and classifications.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting analysis for task {task_id}: {media_type}")
            
            # Initialize results
            results = {
                "task_id": task_id,
                "media_assessment": {},
                "claim_assessment": {},
                "provenance": {},
                "evidence": [],
                "evidence_quality": 0.0,
                "overall_confidence": 0.0,
                "classification": "UNCERTAIN",
                "info_classification": "UNVERIFIED",
                "explanation": "",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_seconds": 0.0
            }
            
            # Visual forensics
            if media_type in ["image", "video"]:
                logger.info(f"Running visual forensics on {media_type}")
                if media_type == "image":
                    visual_result = await self.visual_forensics.analyze_image(media_path)
                else:
                    visual_result = await self.visual_forensics.analyze_video(media_path)
                
                visual_scores = visual_result.get("scores", {})
                
                # Face analysis
                face_result = await self.face_analysis.analyze(media_path)
                face_scores = face_result.get("scores", {})
            else:
                visual_scores = {}
                face_scores = {}
            
            # Temporal analysis (video only)
            if media_type == "video":
                logger.info("Running temporal analysis")
                temporal_result = await self.temporal_analysis.analyze(media_path)
                temporal_scores = temporal_result.get("scores", {})
            else:
                temporal_scores = {}
            
            # Audio forensics
            if media_type in ["audio", "video"]:
                logger.info("Running audio forensics")
                if media_type == "video":
                    audio_path = media_path.replace(".mp4", ".wav")
                    await self.audio_forensics.extract_from_video(media_path, audio_path)
                else:
                    audio_path = media_path
                
                audio_result = await self.audio_forensics.analyze(audio_path)
                audio_scores = audio_result.get("scores", {})
                
                # Lip-sync analysis (video only)
                if media_type == "video":
                    logger.info("Running lip-sync analysis")
                    lip_sync_result = await self.lip_sync_analysis.analyze(media_path, audio_path)
                    lip_sync_scores = lip_sync_result.get("scores", {})
                else:
                    lip_sync_scores = {}
            else:
                audio_scores = {}
                lip_sync_scores = {}
            
            # Provenance analysis
            provenance_scores = {
                "confidence": 0.3,
                "metadata_available": False,
                "exif_present": False,
                "c2pa_present": False
            }
            
            # Fuse forensic scores
            logger.info("Fusing forensic signals")
            fusion_result = await self.multimodal_fusion.fuse(
                visual_scores=visual_scores,
                temporal_scores=temporal_scores,
                audio_scores=audio_scores,
                lip_sync_scores=lip_sync_scores,
                provenance_scores=provenance_scores
            )
            
            results["media_assessment"] = fusion_result
            
            # Claim analysis
            if claim:
                logger.info("Extracting and verifying claims")
                extracted_claims = await ClaimExtractor.extract(claim)
                
                # Retrieve evidence
                evidence_items = await self.evidence_retrieval.retrieve(claim, extracted_claims[0] if extracted_claims else {})
                
                # Verify claims
                claim_verifier = ClaimVerifier()
                verified_claims = []
                for c in extracted_claims:
                    verification = await claim_verifier.verify(c, evidence_items)
                    verified_claims.append(verification)
                
                # Aggregate claim assessment
                claim_assessment = {
                    "false_probability": sum(v.get("false_probability", 0.5) for v in verified_claims) / max(1, len(verified_claims)),
                    "misleading_probability": sum(v.get("misleading_probability", 0.5) for v in verified_claims) / max(1, len(verified_claims)),
                    "supported_probability": 1.0 - sum(v.get("false_probability", 0.5) for v in verified_claims) / max(1, len(verified_claims)),
                    "verifiable": len(evidence_items) > 0,
                    "extracted_claims": extracted_claims
                }
                
                results["claim_assessment"] = claim_assessment
                results["evidence"] = evidence_items
                
                # Build evidence graph
                if include_evidence_graph:
                    evidence_graph = EvidenceGraph.build(extracted_claims, evidence_items)
                    results["evidence_graph"] = evidence_graph
            
            # Classification
            media_class = ClassificationEngine.classify_media(
                manipulation_prob=fusion_result.get("manipulation_probability", 0.5),
                synthetic_prob=fusion_result.get("synthetic_media_probability", 0.5),
                confidence=fusion_result.get("overall_confidence", 0.5)
            )
            
            info_class = ClassificationEngine.classify_information(
                claim_false_prob=results["claim_assessment"].get("false_probability", 0.5),
                claim_misleading_prob=results["claim_assessment"].get("misleading_probability", 0.5),
                supported_prob=results["claim_assessment"].get("supported_probability", 0.5),
                confidence=fusion_result.get("overall_confidence", 0.5)
            )
            
            results["classification"] = media_class
            results["info_classification"] = info_class
            results["overall_confidence"] = fusion_result.get("overall_confidence", 0.5)
            results["evidence_quality"] = sum(e.get("reliability", 0) for e in evidence_items) / max(1, len(evidence_items))
            
            # Generate explanation
            explanation = ClassificationEngine.generate_explanation(
                media_class,
                info_class,
                fusion_result,
                f"Retrieved {len(evidence_items)} evidence items",
                [
                    f"Manipulation probability: {fusion_result.get('manipulation_probability', 0.5):.0%}",
                    f"Synthetic media probability: {fusion_result.get('synthetic_media_probability', 0.5):.0%}",
                    f"Audio manipulation probability: {fusion_result.get('audio_manipulation_probability', 0.5):.0%}",
                    f"Lip-sync inconsistency: {fusion_result.get('lip_sync_inconsistency', 0.5):.0%}",
                ]
            )
            
            results["explanation"] = explanation
            
            processing_time = time.time() - start_time
            results["processing_time_seconds"] = processing_time
            
            logger.info(f"Analysis complete for task {task_id}: {media_class} / {info_class} (took {processing_time:.2f}s)")
            
            return results
        
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {str(e)}", exc_info=True)
            raise
