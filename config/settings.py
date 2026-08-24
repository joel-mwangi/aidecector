import os
from typing import Optional

# Application Settings
APP_NAME = "Multimodal Misinformation Detection"
APP_VERSION = "0.1.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Database (Supabase PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your Supabase credentials."
    )

# Supabase
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# File Upload
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_VIDEO_DURATION = 600  # 10 minutes
ALLOWED_MEDIA_TYPES = {
    "image": {"image/jpeg", "image/png", "image/webp"},
    "video": {"video/mp4", "video/quicktime", "video/x-msvideo"},
    "audio": {"audio/mpeg", "audio/wav", "audio/ogg", "audio/aac"},
}

# Model Settings
MODEL_CACHE_PATH = os.getenv("MODEL_CACHE_PATH", "./models")
GPU_ENABLED = os.getenv("GPU_ENABLED", "false").lower() == "true"
DEVICE = "cuda" if GPU_ENABLED else "cpu"

# Processing
NUM_WORKERS = int(os.getenv("NUM_WORKERS", 4))
INFERENCE_TIMEOUT = 300  # 5 minutes
TASK_QUEUE_NAME = "detection_tasks"

# Fusion and Calibration
FUSION_METHOD = "logistic_regression"  # options: gradient_boosting, neural_fusion, bayesian_fusion
CALIBRATION_PERCENTILE = 0.95

# Detection Thresholds
MANIPULATION_THRESHOLD = 0.5
SYNTHETIC_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.7
UNCERTAINTY_THRESHOLD = 0.3

# Explainability
MAX_EXPLANATION_ITEMS = 5
INCLUDE_EVIDENCE_GRAPH = True

# Security
FILE_SIZE_LIMITS = {
    "image": 50 * 1024 * 1024,   # 50 MB
    "video": 500 * 1024 * 1024,  # 500 MB
    "audio": 100 * 1024 * 1024,  # 100 MB
}

# Privacy
DELETE_UPLOADS_AFTER_DAYS = 7
ENCRYPT_UPLOADS = True

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
