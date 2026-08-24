#!/usr/bin/env python3
"""
Model Manager for Misinformation Detection System
Downloads, caches, and manages pre-trained models
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """Central model management system"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.config_file = self.model_dir / "models.json"
        self.models_config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load model configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default model configuration"""
        return {
            "models": {
                "deepfake_detector_xception": {
                    "type": "pytorch",
                    "name": "Xception (FaceForensics++)",
                    "url": "https://github.com/ondyari/FaceForensics/releases/download/detection_models/xception-epoch-92.pth",
                    "filename": "xception-epoch-92.pth",
                    "size_mb": 107,
                    "sha256": None,
                    "optional": False,
                    "description": "Deepfake detection - high accuracy, good for production"
                },
                "deepfake_detector_mesonet": {
                    "type": "keras",
                    "name": "MesoNet-4",
                    "url": "https://github.com/HyperIntel/MesoNet/releases/download/v1.0/MesoNet-4_DF.h5",
                    "filename": "MesoNet-4_DF.h5",
                    "size_mb": 8,
                    "optional": True,
                    "description": "Lightweight deepfake detector - good for edge devices"
                },
                "optical_flow_raft": {
                    "type": "pytorch",
                    "name": "RAFT",
                    "url": "https://github.com/princeton-vl/RAFT/releases/download/v1.0/raft-things.pth",
                    "filename": "raft-things.pth",
                    "size_mb": 244,
                    "optional": False,
                    "description": "Optical flow for temporal consistency"
                },
                "face_detection_retinaface": {
                    "type": "pytorch_onnx",
                    "name": "RetinaFace",
                    "url": "https://github.com/serengoodbroad/RetinaFace_Pytorch/releases/download/latest/mobilenet0.25_Final.pth",
                    "filename": "retinaface.pth",
                    "size_mb": 100,
                    "optional": True,
                    "description": "Alternative face detection - handles extreme angles"
                }
            },
            "auto_load": {
                "clip": {
                    "type": "transformers",
                    "model_id": "openai/clip-vit-base-patch32",
                    "description": "Zero-shot image understanding",
                    "size_mb": 350
                },
                "yolov8": {
                    "type": "ultralytics",
                    "model": "yolov8x.pt",
                    "description": "Object detection",
                    "size_mb": 200
                },
                "wav2vec2": {
                    "type": "transformers",
                    "model_id": "facebook/wav2vec2-base-960h",
                    "description": "Speech-to-text",
                    "size_mb": 400
                },
                "resemblyzer": {
                    "type": "pip",
                    "package": "resemblyzer",
                    "description": "Voice embeddings and verification",
                    "size_mb": 30
                }
            }
        }
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.models_config, f, indent=2)
    
    def download_all(self, skip_optional: bool = False):
        """Download all models"""
        logger.info("Starting model downloads...")
        
        models = self.models_config.get("models", {})
        
        for model_key, model_info in models.items():
            if skip_optional and model_info.get("optional"):
                logger.info(f"Skipping optional model: {model_key}")
                continue
            
            self._download_model(model_key, model_info)
    
    def _download_model(self, key: str, model_info: Dict):
        """Download a single model"""
        filename = model_info.get("filename")
        url = model_info.get("url")
        filepath = self.model_dir / filename
        
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024*1024)
            logger.info(f"✓ Already exists: {key} ({size_mb:.1f} MB)")
            return
        
        logger.info(f"Downloading: {key} ({model_info.get('size_mb')} MB)")
        
        try:
            import urllib.request
            urllib.request.urlretrieve(url, filepath)
            size_mb = filepath.stat().st_size / (1024*1024)
            logger.info(f"✓ Downloaded: {key} ({size_mb:.1f} MB)")
        except Exception as e:
            logger.error(f"✗ Failed to download {key}: {e}")
    
    def get_model_path(self, model_key: str) -> Optional[Path]:
        """Get path to a model"""
        model_info = self.models_config.get("models", {}).get(model_key)
        if not model_info:
            return None
        
        filepath = self.model_dir / model_info["filename"]
        if filepath.exists():
            return filepath
        return None
    
    def list_models(self):
        """List all available models"""
        print("\n" + "="*70)
        print("MISINFORMATION DETECTION - AVAILABLE MODELS")
        print("="*70)
        
        print("\n📥 DOWNLOADABLE MODELS:")
        print("-" * 70)
        
        models = self.models_config.get("models", {})
        for key, info in models.items():
            status = "✓" if self.get_model_path(key) else "○"
            optional = " (optional)" if info.get("optional") else ""
            print(f"{status} {key}{optional}")
            print(f"   {info.get('description', 'N/A')}")
            print(f"   Size: {info.get('size_mb')} MB")
            print()
        
        print("🔄 AUTO-LOADING MODELS (download on first use):")
        print("-" * 70)
        
        auto_load = self.models_config.get("auto_load", {})
        for key, info in auto_load.items():
            print(f"✓ {key}")
            print(f"   {info.get('description', 'N/A')}")
            print(f"   Size: ~{info.get('size_mb')} MB (auto-cached)")
            print()
    
    def estimate_storage(self) -> Dict:
        """Estimate storage requirements"""
        models = self.models_config.get("models", {})
        auto_load = self.models_config.get("auto_load", {})
        
        required_mb = sum(
            m.get("size_mb", 0) for m in models.values()
            if not m.get("optional")
        )
        
        optional_mb = sum(
            m.get("size_mb", 0) for m in models.values()
            if m.get("optional")
        )
        
        auto_mb = sum(
            m.get("size_mb", 0) for m in auto_load.values()
        )
        
        return {
            "required_mb": required_mb,
            "optional_mb": optional_mb,
            "auto_load_mb": auto_mb,
            "total_mb": required_mb + optional_mb + auto_mb,
            "total_gb": (required_mb + optional_mb + auto_mb) / 1024
        }
    
    def generate_docker_volumes(self) -> str:
        """Generate docker-compose volumes configuration"""
        return f"""
volumes:
  models:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: {self.model_dir.absolute()}
"""


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Model Manager for Misinformation Detection System"
    )
    
    parser.add_argument(
        "command",
        choices=["download", "list", "estimate", "check"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--model-dir",
        default="models",
        help="Model directory (default: models/)"
    )
    
    parser.add_argument(
        "--skip-optional",
        action="store_true",
        help="Skip optional models"
    )
    
    args = parser.parse_args()
    
    manager = ModelManager(args.model_dir)
    
    if args.command == "download":
        manager.download_all(skip_optional=args.skip_optional)
    
    elif args.command == "list":
        manager.list_models()
    
    elif args.command == "estimate":
        est = manager.estimate_storage()
        print("\n" + "="*70)
        print("STORAGE REQUIREMENTS")
        print("="*70)
        print(f"Required models:   {est['required_mb']:>8.0f} MB")
        print(f"Optional models:   {est['optional_mb']:>8.0f} MB")
        print(f"Auto-loading:      {est['auto_load_mb']:>8.0f} MB")
        print(f"{'─'*40}")
        print(f"Total:             {est['total_mb']:>8.0f} MB ({est['total_gb']:>5.1f} GB)")
        print()
    
    elif args.command == "check":
        manager.list_models()
        est = manager.estimate_storage()
        print("\n" + "="*70)
        print("ESTIMATED STORAGE: {:.1f} GB".format(est['total_gb']))
        print("="*70)


if __name__ == "__main__":
    main()
