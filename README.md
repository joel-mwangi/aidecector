# Multimodal Misinformation and Synthetic Media Detection System

A research-grade evidence-fusion architecture for analyzing media authenticity and claim credibility across visual, audio, and temporal dimensions.

## Architecture

```
                         USER INPUT
                    image / video / audio
                              │
                              ▼
                    ┌──────────────────┐
                    │ Media Ingestion  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        Visual Pipeline Audio Pipeline Provenance
              │              │              │
              ▼              ▼              ▼
        Image Forensics  Audio Forensics  Metadata
        Face Analysis   Voice Analysis    Signatures
        Temporal        Lip Sync          Origin
        Analysis        Analysis
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    Multimodal Fusion
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       Synthetic Media   Semantic        Physical
         Detection      Consistency    Consistency
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                       Claim Engine
                             │
                             ▼
                  Evidence / Corroboration
                             │
                             ▼
                    Calibration Layer
                             │
                             ▼
                     FINAL ASSESSMENT
```

## Quick Start

### Build and Start

```bash
docker compose up --build -d
```

### Submit Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/video.mp4",
    "media_type": "video",
    "claim": "President announced policy change yesterday"
  }'
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Analysis queued. Check status using task_id."
}
```

### Check Status

```bash
curl http://localhost:8000/api/v1/status/550e8400-e29b-41d4-a716-446655440000
```

### Get Results

```bash
curl http://localhost:8000/api/v1/results/550e8400-e29b-41d4-a716-446655440000
```

## Services

- **API** (port 8000): FastAPI inference and task management
- **Detection Queue**: Redis-based task queue
- **Visual Worker**: Face analysis, deepfake detection, forensics
- **Audio Worker**: Synthetic speech detection, voice analysis
- **Claim Worker**: Claim extraction and verification
- **PostgreSQL**: Task and result storage
- **Redis**: Queue and caching

## Features

### Visual Analysis
- Face detection and consistency tracking
- Face-swap and reenactment detection
- Synthetic image/video detection
- Artifact detection (lighting, geometry, frequency domain)
- Resampling and compression analysis

### Audio Analysis
- Synthetic speech detection
- Voice-cloning indicators
- Speaker consistency analysis
- Audio-visual synchronization
- Lip-sync manipulation detection

### Temporal Analysis
- Frame-to-frame consistency
- Optical flow analysis
- Motion continuity
- Background consistency
- Lighting continuity

### Claim Analysis
- Claim extraction from unstructured text
- Structured claim representation
- Evidence retrieval from multiple sources
- Claim verification against evidence
- Evidence graph construction

### Multimodal Fusion
- Weighted averaging of forensic signals
- Calibrated probability outputs
- Confidence estimation
- Feature importance tracking

### Classifications

**Media Authenticity:**
- AUTHENTIC
- LIKELY_AUTHENTIC
- UNCERTAIN
- LIKELY_MANIPULATED
- MANIPULATED
- AI_GENERATED

**Information Credibility:**
- SUPPORTED
- MOSTLY_SUPPORTED
- UNVERIFIED
- MISLEADING
- LIKELY_FALSE
- FALSE

## API Endpoints

### POST /api/v1/analyze
Submit media for analysis.

**Request:**
```json
{
  "media_url": "string (optional)",
  "media_data": "bytes (optional)",
  "media_type": "image|video|audio",
  "claim": "string (optional)",
  "include_evidence_graph": true
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "queued|processing|completed|failed",
  "message": "string"
}
```

### GET /api/v1/status/{task_id}
Get task status and progress.

### GET /api/v1/results/{task_id}
Get full analysis results with evidence.

### GET /api/v1/tasks
List recent analysis tasks.

### DELETE /api/v1/tasks/{task_id}
Delete task and results.

### GET /health
Health check endpoint.

## Output Format

```json
{
  "media_assessment": {
    "manipulation_probability": 0.91,
    "synthetic_media_probability": 0.87,
    "audio_manipulation_probability": 0.18,
    "lip_sync_inconsistency": 0.82
  },
  "claim_assessment": {
    "false_probability": 0.79,
    "misleading_probability": 0.88,
    "supported_probability": 0.21,
    "verifiable": true,
    "extracted_claims": [...]
  },
  "provenance": {
    "confidence": 0.12,
    "metadata_available": false,
    "exif_data_present": false,
    "c2pa_present": false,
    "editing_signatures": []
  },
  "evidence": [...],
  "evidence_quality": 0.76,
  "overall_confidence": 0.89,
  "classification": "LIKELY_MANIPULATED",
  "info_classification": "LIKELY_FALSE",
  "explanation": "...",
  "processing_time_seconds": 45.2
}
```

## Configuration

See `config/settings.py` for all configuration options:

- `GPU_ENABLED`: Enable NVIDIA GPU acceleration
- `ENVIRONMENT`: development | production
- `MAX_UPLOAD_SIZE`: Maximum media file size
- `MAX_VIDEO_DURATION`: Maximum video length
- `FUSION_METHOD`: logistic_regression | gradient_boosting | neural_fusion | bayesian_fusion
- `MANIPULATION_THRESHOLD`: Classification threshold
- `DELETE_UPLOADS_AFTER_DAYS`: Auto-cleanup retention

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Access Logs

```bash
docker compose logs -f api
docker compose logs -f detection-queue
```

### Database Access

```bash
docker exec -it misinformation-db psql -U detector -d misinformation
```

### Clear Data

```bash
docker compose down -v
```

## Limitations & Disclaimers

1. **Probabilistic Assessment**: Results are probability estimates, not definitive classifications.
2. **False Positives/Negatives**: The system may fail to detect sophisticated manipulations or flag authentic media as suspicious.
3. **Incomplete Evidence**: Analysis quality depends on available corroborating evidence.
4. **Adversarial Robustness**: Deliberately adversarial transformations may evade detection.
5. **Context Dependency**: Assessment may be incomplete without full context or metadata.
6. **Model Limitations**: Pre-trained models have inherent biases and limitations.

## Research

This system is designed as a research platform for:

- Multi-signal forensic analysis
- Evidence fusion methodologies
- Calibration and uncertainty quantification
- Adversarial robustness evaluation
- Generalization to unseen detectors and manipulations
- Real-world misinformation patterns

## References

Key papers and datasets for extending this system:

- FaceForensics++ (Deepfake detection)
- SenseTime Anti-Spoofing (Face swap detection)
- WITNESS (Synthetic speech detection)
- Middlebury (Optical flow benchmarks)
- C2PA (Content credentials)

## Security & Privacy

- Uploaded media treated as untrusted input
- Resource limits on processing
- Automatic cleanup of uploads
- Encryption support in transit
- Audit logging for access
- Access controls for results

## License

Research use only. See LICENSE file for details.
