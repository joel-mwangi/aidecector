import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ClassificationEngine:
    """Classify overall media and information authenticity."""
    
    MEDIA_CLASSIFICATIONS = [
        "AUTHENTIC",
        "LIKELY_AUTHENTIC",
        "UNCERTAIN",
        "LIKELY_MANIPULATED",
        "MANIPULATED",
        "AI_GENERATED"
    ]
    
    INFO_CLASSIFICATIONS = [
        "SUPPORTED",
        "MOSTLY_SUPPORTED",
        "UNVERIFIED",
        "MISLEADING",
        "LIKELY_FALSE",
        "FALSE"
    ]
    
    @staticmethod
    def classify_media(
        manipulation_prob: float,
        synthetic_prob: float,
        confidence: float,
        threshold_manipulated: float = 0.7,
        threshold_synthetic: float = 0.7
    ) -> str:
        """Classify media authenticity."""
        
        if synthetic_prob > threshold_synthetic:
            return "AI_GENERATED"
        
        if manipulation_prob > threshold_manipulated:
            return "MANIPULATED"
        
        if manipulation_prob > 0.5 or synthetic_prob > 0.5:
            return "LIKELY_MANIPULATED"
        
        if confidence < 0.3:
            return "UNCERTAIN"
        
        if manipulation_prob < 0.3 and synthetic_prob < 0.3:
            return "LIKELY_AUTHENTIC" if confidence > 0.6 else "UNCERTAIN"
        
        return "UNCERTAIN"
    
    @staticmethod
    def classify_information(
        claim_false_prob: float,
        claim_misleading_prob: float,
        supported_prob: float,
        confidence: float
    ) -> str:
        """Classify claim/information credibility."""
        
        if supported_prob > 0.8:
            return "SUPPORTED"
        
        if supported_prob > 0.6:
            return "MOSTLY_SUPPORTED"
        
        if claim_false_prob > 0.7:
            return "FALSE"
        
        if claim_false_prob > 0.5:
            return "LIKELY_FALSE"
        
        if claim_misleading_prob > 0.6:
            return "MISLEADING"
        
        if confidence < 0.3:
            return "UNVERIFIED"
        
        return "UNVERIFIED"
    
    @staticmethod
    def generate_explanation(
        media_classification: str,
        info_classification: str,
        forensic_scores: Dict[str, float],
        evidence_summary: str,
        top_findings: list
    ) -> str:
        """Generate human-readable explanation."""
        
        explanation = f"""
ASSESSMENT SUMMARY

Media Classification: {media_classification}
Information Classification: {info_classification}

KEY FINDINGS:
"""
        
        for i, finding in enumerate(top_findings[:5], 1):
            explanation += f"{i}. {finding}\n"
        
        explanation += f"""
EVIDENCE SUMMARY:
{evidence_summary}

CONFIDENCE:
The system is {forensic_scores.get('overall_confidence', 0.5):.0%} confident in this assessment.

LIMITATIONS:
- Results are probabilistic, not definitive
- False positives and false negatives are possible
- Evidence may be incomplete or unavailable
- Sophisticated manipulations may evade detection
"""
        
        return explanation.strip()
