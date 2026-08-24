"""
Enhanced FastAPI with Ensemble Models Integration
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
from datetime import datetime
import logging
import asyncio

from src.ingestion.handler import IngestHandler
from src.api.models import AnalysisRequest, AnalysisResponse, StatusResponse
from src.api.database import Database
from src.api.queue import TaskQueue
from src.models.model_manager import EnsembleModelManager
from src.ensemble.inference import EnsembleInferenceEngine
from src.fusion.multimodal import MultimodalFusion
from src.visual.forensics import VisualForensics, FaceAnalysis
from src.audio.forensics import AudioForensics
from src.temporal.analysis import TemporalAnalysis
from src.lipsync.analyzer import LipsyncAnalyzer

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multimodal Misinformation Detection API with Ensemble Models",
    version="0.2.0",
    description="Evidence-fusion architecture with 10+ ensemble models for authenticity analysis"
)

# Initialize services
ingest_handler = IngestHandler()
db = Database()
queue = TaskQueue()

# Initialize ensemble components
model_manager = None
multimodal_fusion = None
visual_forensics = None
face_analysis = None
audio_forensics = None
temporal_analysis = None
lipsync_analyzer = None

@app.on_event("startup")
async def startup():
    """Initialize database, queue, and ensemble models."""
    global model_manager, multimodal_fusion, visual_forensics, face_analysis
    global audio_forensics, temporal_analysis, lipsync_analyzer
    
    try:
        # Connect database and queue
        await db.connect()
        await queue.connect()
        logger.info("Database and queue connected")
        
        # Initialize ensemble models
        logger.info("Initializing ensemble models...")
        
        device = "cuda" if os.environ.get("USE_GPU") == "true" else "cpu"
        model_manager = EnsembleModelManager(device=device, model_dir="models")
        logger.info(model_manager.summary())
        
        # Initialize multimodal fusion
        multimodal_fusion = MultimodalFusion(device=device, model_dir="models")
        logger.info("✓ Multimodal fusion initialized")
        
        # Initialize forensics modules
        visual_forensics = VisualForensics(device=device, model_dir="models")
        logger.info("✓ Visual forensics initialized")
        
        face_analysis = FaceAnalysis(device=device, model_dir="models")
        logger.info("✓ Face analysis initialized")
        
        audio_forensics = AudioForensics(device=device, model_dir="models")
        logger.info("✓ Audio forensics initialized")
        
        temporal_analysis = TemporalAnalysis(device=device, model_dir="models")
        logger.info("✓ Temporal analysis initialized")
        
        lipsync_analyzer = LipsyncAnalyzer(device=device, model_dir="models")
        logger.info("✓ Lipsync analyzer initialized")
        
        logger.info("=" * 60)
        logger.info("API startup complete - all systems ready")
        logger.info(f"Ensemble models: {len(model_manager.get_available_models())} loaded")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown():
    """Close database and queue connections."""
    try:
        await db.disconnect()
        await queue.disconnect()
        logger.info("API shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint with model status."""
    try:
        models_available = model_manager.get_available_models() if model_manager else []
        model_status = model_manager.get_model_status() if model_manager else {}
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "ensemble_models": {
                "available": len(models_available),
                "total": 10,
                "models": models_available
            },
            "model_status": model_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/v1/models")
async def get_models_info():
    """Get information about loaded ensemble models."""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Models not initialized")
    
    available = model_manager.get_available_models()
    status = model_manager.get_model_status()
    
    return {
        "total_models": len(model_manager.models),
        "loaded_models": len(available),
        "available_models": available,
        "model_status": status,
        "weights": model_manager.weights,
        "summary": model_manager.summary()
    }

@app.post("/api/v1/analyze")
async def analyze_media(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit media for ensemble analysis.
    
    Uses 10+ models for:
    - Visual deepfake detection (Xception, MesoNet)
    - Face analysis (RetinaFace, MediaPipe)
    - Audio authenticity (Wav2Vec2, ASVspoof, Resemblyzer)
    - Temporal consistency (RAFT)
    - Semantic understanding (CLIP, YOLOv8)
    
    Returns a task ID immediately. Use /api/v1/status/{task_id} to poll results.
    """
    try:
        # Validate request
        if not request.media_url and not request.media_data:
            raise HTTPException(
                status_code=400,
                detail="Either media_url or media_data required"
            )
        
        if not model_manager or len(model_manager.get_available_models()) == 0:
            raise HTTPException(
                status_code=503,
                detail="Ensemble models not initialized. Download models first."
            )
        
        # Create task
        task_id = str(uuid.uuid4())
        
        # Ingest media
        media_info = await ingest_handler.ingest(
            task_id=task_id,
            media_url=request.media_url,
            media_data=request.media_data,
            media_type=request.media_type,
            claim=request.claim
        )
        
        # Store metadata in database
        await db.create_task(
            task_id=task_id,
            media_path=media_info["path"],
            media_type=request.media_type,
            claim=request.claim,
            status="queued"
        )
        
        # Queue analysis with ensemble flag
        await queue.enqueue(
            task_id=task_id,
            task_type="ensemble_analysis",
            payload={
                "media_path": media_info["path"],
                "media_type": request.media_type,
                "claim": request.claim,
                "include_evidence_graph": request.include_evidence_graph,
                "use_ensemble": True
            }
        )
        
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Ensemble analysis queued",
            "models_being_used": model_manager.get_available_models(),
            "estimated_time_seconds": 30 if request.media_type == "image" else 120
        }
        
    except Exception as e:
        logger.error(f"Analysis request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze/quick")
async def analyze_quick(request: AnalysisRequest):
    """Quick synchronous analysis (for images only)."""
    try:
        if request.media_type != "image":
            raise HTTPException(
                status_code=400,
                detail="Quick analysis only supports images"
            )
        
        # Ingest media
        task_id = str(uuid.uuid4())
        media_info = await ingest_handler.ingest(
            task_id=task_id,
            media_url=request.media_url,
            media_data=request.media_data,
            media_type=request.media_type,
            claim=request.claim
        )
        
        # Run ensemble analysis immediately
        logger.info(f"Running quick ensemble analysis: {task_id}")
        
        # Visual analysis
        visual_result = await visual_forensics.analyze_image(media_info["path"])
        
        # Face analysis
        face_result = await face_analysis.analyze(media_info["path"])
        
        # Multimodal fusion
        fused_result = await multimodal_fusion.fuse(
            visual_scores=visual_result.get("ensemble_results", {}),
            temporal_scores={},
            audio_scores={},
            ensemble_results=visual_result
        )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "quick_result": True,
            "analysis": {
                "visual": visual_result,
                "faces": face_result,
                "fused": fused_result
            }
        }
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/status/{task_id}")
async def get_status(task_id: str):
    """Get analysis status and results."""
    try:
        task = await db.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task["status"] == "completed":
            result = await db.get_result(task_id)
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "completed_at": task["completed_at"].isoformat() if task["completed_at"] else None
            }
        elif task["status"] == "failed":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": task["error"]
            }
        else:
            return {
                "task_id": task_id,
                "status": task["status"]
            }
    
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/results/{task_id}")
async def get_results(task_id: str):
    """Get full analysis results with ensemble details."""
    try:
        result = await db.get_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        return result
        
    except Exception as e:
        logger.error(f"Result retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks")
async def list_tasks(skip: int = 0, limit: int = 10):
    """List recent analysis tasks."""
    try:
        tasks = await db.list_tasks(skip=skip, limit=limit)
        return {
            "tasks": tasks,
            "total": len(tasks),
            "models_used": model_manager.get_available_models() if model_manager else []
        }
    except Exception as e:
        logger.error(f"Task listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its results."""
    try:
        success = await db.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task deleted"}
        
    except Exception as e:
        logger.error(f"Task deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
