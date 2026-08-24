# Build a Multimodal Misinformation and Synthetic Media Detection System

You are a senior ML engineer, AI researcher, computer-vision engineer, cybersecurity engineer, and software architect.

Build a serious, research-grade **multimodal misinformation and synthetic-media detection platform**.

The objective is NOT merely to classify an image or video as “AI-generated.” The objective is to determine whether submitted media and its associated claim are authentic, manipulated, synthetic, misleading, or unsupported by available evidence.

The system must distinguish between:

- authentic media
- AI-generated media
- AI-manipulated media
- face swaps
- lip-sync manipulation
- voice cloning
- edited real media
- authentic media used with a false caption
- authentic old footage presented as a recent event
- misleading context
- fabricated events
- unverifiable claims
- insufficient evidence

Do not assume that AI-generated media is automatically misinformation.

---

## 1. Core Principle

Build the system as an **evidence-fusion architecture**, not a single binary classifier.

The system should independently estimate:

1. Probability that the media has been manipulated.
2. Probability that the media is AI-generated or AI-assisted.
3. Probability that the audio has been synthetically generated or manipulated.
4. Probability that the video contains temporal inconsistencies.
5. Probability that faces or identities have been manipulated.
6. Probability that the audio and video are inconsistent.
7. Probability that the physical scene contains synthetic/manipulation artifacts.
8. Provenance confidence.
9. Probability that the textual claim is false or misleading.
10. Availability and quality of independent corroborating evidence.

Then combine these signals using a calibrated evidence-fusion layer.

Never allow one weak detector to automatically determine the final result.

---

# 2. Example Scenario

The system may receive:

> “President X gave a speech yesterday and kissed Person Y during the event.”

The uploaded video may show exactly that event.

The system must not simply ask:

> “Does this video look AI-generated?”

Instead, it should determine:

### Media analysis

- Is the video synthetic?
- Has the face been manipulated?
- Is the audio genuine?
- Is the lip movement synchronized?
- Are there frame-to-frame inconsistencies?
- Are lighting, shadows, reflections and geometry consistent?
- Are hands, teeth, eyes and facial boundaries plausible?
- Has the video been edited?

### Claim analysis

Extract structured claims:

```text
Subject:
President X

Second person:
Person Y

Action:
kissing

Event:
official/public speech

Date:
claimed date

Location:
claimed location
```

Then investigate whether independent evidence supports the event.

The final answer should distinguish:

```text
MEDIA AUTHENTICITY
MEDIA MANIPULATION
CLAIM VERACITY
CONTEXTUAL ACCURACY
EVIDENCE QUALITY
```

---

# 3. Architecture

Use a modular architecture:

```text
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

Keep each subsystem independently testable.

---

# 4. Technology

Use a practical ML stack.

Preferred:

- Python
- PyTorch
- OpenCV
- FFmpeg
- NumPy
- pandas
- scikit-learn
- Hugging Face Transformers where appropriate
- FastAPI for inference APIs
- PostgreSQL for metadata/results
- Redis or an equivalent queue if asynchronous processing becomes necessary

Use Docker for reproducible environments.

Do not over-containerize the first version.

Initially use:

```text
docker
├── api
└── detector
```

Add separate workers only when processing requirements justify them.

If GPU acceleration is available, support NVIDIA GPU execution through Docker.

The application must still have a CPU fallback for development and testing.

---

# 5. Visual Forensics

Implement a visual-analysis pipeline capable of detecting:

- face swaps
- facial reenactment
- generated faces
- image synthesis
- frame manipulation
- inconsistent skin texture
- abnormal facial boundaries
- eye inconsistencies
- teeth/mouth artifacts
- hand anomalies
- lighting inconsistencies
- shadows
- reflections
- geometric inconsistencies
- resampling artifacts
- compression inconsistencies
- unnatural frequency-domain patterns

Do not rely on manually written heuristics alone.

Design the system so multiple forensic models can contribute signals.

---

# 6. Temporal Video Analysis

For videos, never analyze only one frame.

Sample frames intelligently across the video.

Analyze:

- frame-to-frame identity consistency
- facial landmark movement
- optical-flow consistency
- motion continuity
- lighting continuity
- background consistency
- object persistence
- temporal artifacts
- sudden visual transitions
- face-boundary changes
- lip movement consistency

Use temporal models where justified.

Avoid processing every frame unnecessarily.

Implement configurable sampling strategies.

---

# 7. Audio Forensics

Extract audio from video when necessary.

Analyze:

- synthetic speech probability
- voice-cloning indicators
- spectral anomalies
- unnatural prosody
- speaker consistency
- background-noise consistency
- acoustic discontinuities
- editing boundaries

Do not treat low-quality audio as automatically fake.

The system must explicitly account for uncertainty caused by compression and noise.

---

# 8. Audio-Visual Synchronization

Analyze whether:

```text
spoken phonemes
        ↕
mouth movements
```

are synchronized.

Detect:

- lip-sync manipulation
- dubbed speech
- generated speech over real video
- delayed audio
- inconsistent speaker identity

Return a confidence score rather than a binary result.

---

# 9. Identity Analysis

Where technically and legally appropriate, analyze whether the person appearing in the media is consistent with the claimed identity.

Do NOT make unsupported identity claims.

Distinguish:

```text
Face detected
        ↓
Face consistent across frames
        ↓
Possible identity match
        ↓
Confidence
```

Never state:

> “This is definitely Person X”

when the evidence does not justify that conclusion.

---

# 10. Metadata and Provenance

Inspect:

- EXIF
- container metadata
- timestamps
- encoding information
- editing software signatures
- file history where available
- Content Credentials / C2PA where available
- cryptographic provenance information where available

Important:

Metadata absence is NOT proof of manipulation.

Treat provenance as one evidence source among many.

---

# 11. OCR and Speech-to-Text

For video/image text:

Use OCR to extract:

- captions
- headlines
- signs
- watermarks
- timestamps
- usernames
- logos
- claims embedded inside the media

For audio:

Convert speech to text.

Then identify factual claims.

Example:

```text
“The president announced a national emergency yesterday.”
```

becomes a structured claim requiring verification.

---

# 12. Claim Extraction

Create a claim extraction subsystem.

Input:

```text
“The president gave a speech in Nairobi yesterday and announced that the government had banned X.”
```

Output:

```json
{
  "claims": [
    {
      "subject": "President",
      "action": "gave a speech",
      "location": "Nairobi",
      "time": "yesterday"
    },
    {
      "subject": "Government",
      "action": "banned X",
      "time": "yesterday"
    }
  ]
}
```

Claims must be independently evaluated.

---

# 13. Evidence Retrieval

Build an evidence-retrieval layer capable of finding relevant independent sources.

Prefer authoritative sources where possible.

Examples:

- government websites
- official statements
- official event records
- reputable news organizations
- authenticated original media
- public records
- trusted archives

Do not treat search-engine results themselves as proof.

The system should record:

```text
source
source type
publication date
relevance
agreement/disagreement
source reliability
retrieval timestamp
```

Never manufacture evidence.

---

# 14. Evidence Graph

Represent evidence relationships.

Example:

```text
CLAIM
 │
 ├── supports → Source A
 │
 ├── contradicts → Source B
 │
 ├── supports → Original Video
 │
 └── uncertain → Source C
```

This should allow the final system to explain *why* it reached a conclusion.

---

# 15. Evidence Fusion

Build a fusion layer that combines:

```text
visual_score
temporal_score
audio_score
lip_sync_score
identity_score
metadata_score
provenance_score
claim_score
corroboration_score
source_quality_score
```

Do not simply average these values.

Investigate appropriate approaches such as:

- logistic regression
- gradient boosting
- calibrated neural fusion
- Bayesian evidence fusion
- learned ensemble methods

Compare approaches experimentally.

The fusion model must be calibrated.

---

# 16. Output

Do not return only:

```text
FAKE
```

Return a structured result such as:

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
    "misleading_probability": 0.88
  },
  "provenance": {
    "confidence": 0.12
  },
  "evidence_quality": 0.76,
  "overall_confidence": 0.89,
  "classification": "LIKELY_MANIPULATED_AND_MISLEADING"
}
```

Also generate human-readable evidence.

---

# 17. Classification System

Use multiple dimensions.

Possible media classifications:

```text
AUTHENTIC
LIKELY_AUTHENTIC
UNCERTAIN
LIKELY_MANIPULATED
MANIPULATED
AI_GENERATED
```

Possible information classifications:

```text
SUPPORTED
MOSTLY_SUPPORTED
UNVERIFIED
MISLEADING
LIKELY_FALSE
FALSE
```

Do not collapse these into a single label.

---

# 18. Uncertainty

This is mandatory.

The system must be capable of saying:

> “Insufficient evidence.”

A detector that is forced to classify every input as true or false will produce dangerous false positives.

Define explicit thresholds and confidence intervals where possible.

---

# 19. Dataset Strategy

Do not train only on one benchmark dataset.

Build a dataset strategy containing:

### Real media

- authentic videos
- authentic speeches
- interviews
- public events
- different cameras
- different lighting
- different resolutions

### Synthetic media

Include multiple generation techniques and generators.

### Manipulated media

Include:

- face swaps
- lip-sync manipulation
- voice cloning
- reenactment
- editing
- splicing
- recompression
- cropping
- resizing
- screen recording

### Real-world misinformation

Include examples where:

- authentic media is given false captions
- old media is presented as current
- events are incorrectly attributed
- real people are falsely identified
- media is taken out of context

Prevent train/test leakage.

Evaluate on unseen generators and unseen manipulation techniques.

---

# 20. Adversarial Robustness

Test the detector against transformations such as:

```text
resize
crop
compression
re-encoding
screen recording
watermark
blur
noise
brightness changes
contrast changes
frame-rate changes
audio compression
background noise
```

The detector should not collapse when content is uploaded to a social-media platform.

---

# 21. Evaluation

Create a reproducible benchmark.

Measure at minimum:

- accuracy
- precision
- recall
- F1
- AUROC
- AUPRC
- false-positive rate
- false-negative rate
- calibration error
- inference latency
- memory usage
- CPU performance
- GPU performance

Evaluate separately for:

```text
images
videos
audio
multimodal inputs
known generators
unknown generators
compressed media
real-world media
```

Generate confusion matrices and error analysis.

---

# 22. Explainability

Every result must be traceable to evidence.

For example:

```text
Overall assessment:
LIKELY MANIPULATED

Reasons:

1. Strong temporal inconsistency detected.
2. Facial boundary artifacts detected across 17 frames.
3. Audio/video synchronization anomaly detected.
4. Provenance information unavailable.
5. Independent sources contradict the claimed event.

Confidence:
89%
```

Never expose hidden chain-of-thought.

Expose only concise, evidence-based explanations.

---

# 23. Security

Treat uploaded media as untrusted input.

Protect against:

- malicious files
- decompression bombs
- oversized uploads
- malformed video containers
- command injection through filenames
- malicious metadata
- denial-of-service through expensive inference
- arbitrary code execution through media-processing dependencies

Sandbox FFmpeg and other media-processing operations where appropriate.

Apply:

- file-size limits
- duration limits
- MIME validation
- resource limits
- timeouts
- isolated processing
- safe temporary storage
- automatic cleanup

---

# 24. Privacy

Uploaded media may contain sensitive information.

Design for:

- encryption in transit
- secure storage
- automatic deletion policies
- minimal retention
- access controls
- audit logging
- privacy-preserving processing where possible

Do not retain uploaded media indefinitely by default.

---

# 25. Docker

Create a reproducible Docker development environment.

Requirements:

- Python dependency locking
- deterministic versions
- FFmpeg
- OpenCV
- PyTorch
- CPU mode
- optional GPU mode
- health checks
- resource limits
- environment configuration
- separate development and production configurations

Do not put model weights directly into Git if they are large.

Use a model/artifact storage strategy.

---

# 26. Repository Structure

Create a clean structure similar to:

```text
src/
├── ingestion/
├── preprocessing/
├── visual/
├── audio/
├── temporal/
├── provenance/
├── claim/
├── retrieval/
├── evidence/
├── fusion/
├── calibration/
├── inference/
└── api/

models/
datasets/
experiments/
evaluation/
tests/
docs/
docker/
scripts/
```

Keep research code separated from production code.

---

# 27. Research Discipline

Before implementing custom models:

1. Research current state-of-the-art approaches.
2. Identify established datasets.
3. Identify known limitations of current detectors.
4. Establish baseline models.
5. Establish evaluation metrics.
6. Establish reproducibility requirements.
7. Identify licensing constraints.
8. Document assumptions.

Do not reinvent an existing technique unnecessarily.

Use current primary research papers and official documentation when selecting models and libraries.

---

# 28. Baselines

Implement baseline detectors first.

Then compare the proposed fusion architecture against them.

The research question should ultimately be:

> Does multimodal evidence fusion generalize better to unseen synthetic-media generation and real-world misinformation than individual forensic detectors?

Do not claim superiority without benchmarking it.

---

# 29. Development Method

Follow this order:

```text
1. Inspect repository
2. Understand environment
3. Research current approaches
4. Define requirements
5. Design architecture
6. Define datasets
7. Implement preprocessing
8. Implement baseline detectors
9. Build evaluation framework
10. Build fusion model
11. Calibrate probabilities
12. Build evidence system
13. Build API
14. Dockerize
15. Run tests
16. Benchmark
17. Perform adversarial evaluation
18. Document limitations
19. Verify end-to-end operation
```

Do not skip directly to model training.

---

# 30. Important Constraint

Never claim that the system can determine truth with certainty.

The correct objective is:

> **Estimate authenticity and claim credibility from multiple independent evidence sources, while explicitly representing uncertainty.**

False positives and false negatives must be measured and reported.

The system must be designed so that a user can understand:

**what was detected, what evidence supports the result, how confident the system is, and what remains uncertain.**

Start by analyzing the existing repository and environment. Do not modify code until you have produced the architecture, identified the current state, and explained the implementation plan.