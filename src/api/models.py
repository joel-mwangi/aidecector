from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalysisRequest(BaseModel):
    """Request model for media analysis."""
    media_url: Optional[str] = None
    media_data: Optional[bytes] = None
    media_type: str  # "image", "video", "audio"
    claim: Optional[str] = None
    include_evidence_graph: bool = True

class MediaAssessment(BaseModel):
    """Media-level forensic scores."""
    manipulation_probability: float
    synthetic_media_probability: float
    audio_manipulation_probability: float
    lip_sync_inconsistency: float
    temporal_inconsistency: float
    identity_consistency: float
    face_boundary_artifacts: float
    lighting_consistency: float

class ClaimAssessment(BaseModel):
    """Claim-level evaluation."""
    false_probability: float
    misleading_probability: float
    supported_probability: float
    verifiable: bool
    extracted_claims: List[Dict[str, Any]]

class ProvenanceAssessment(BaseModel):
    """Metadata and origin analysis."""
    confidence: float
    metadata_available: bool
    exif_data_present: bool
    c2pa_present: bool
    editing_signatures: List[str]

class EvidenceItem(BaseModel):
    """Individual evidence piece."""
    source: str
    source_type: str
    statement: str
    relationship: str  # "supports", "contradicts", "uncertain"
    reliability: float
    retrieval_date: datetime

class AnalysisResponse(BaseModel):
    """Complete analysis result."""
    task_id: str
    media_assessment: MediaAssessment
    claim_assessment: ClaimAssessment
    provenance: ProvenanceAssessment
    evidence: List[EvidenceItem]
    evidence_quality: float
    overall_confidence: float
    classification: str  # "AUTHENTIC", "LIKELY_AUTHENTIC", "UNCERTAIN", "LIKELY_MANIPULATED", "MANIPULATED", "AI_GENERATED"
    info_classification: str  # "SUPPORTED", "MOSTLY_SUPPORTED", "UNVERIFIED", "MISLEADING", "LIKELY_FALSE", "FALSE"
    explanation: str
    timestamp: datetime
    processing_time_seconds: float

class StatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    status: str  # "queued", "processing", "completed", "failed"
    error: Optional[str] = None
    progress_percent: Optional[int] = None
