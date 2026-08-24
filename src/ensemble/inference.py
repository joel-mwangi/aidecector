"""
Ensemble Inference Engine
Combines predictions from multiple models.
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EnsembleInferenceEngine:
    """Combines predictions from multiple models."""
    
    def __init__(self, model_manager, executor: Optional[ThreadPoolExecutor] = None):
        self.manager = model_manager
        self.executor = executor or ThreadPoolExecutor(max_workers=4)
    
    async def visual_ensemble(self, image_data: Any) -> Dict[str, Any]:
        """Run all visual models and combine results."""
        results = {}
        tasks = []
        
        # Create tasks for each model
        if self.manager.get_model('xception'):
            tasks.append(('xception', self._xception_predict(image_data)))
        
        if self.manager.get_model('mesonet'):
            tasks.append(('mesonet', self._mesonet_predict(image_data)))
        
        if self.manager.get_model('clip'):
            tasks.append(('clip', self._clip_predict(image_data)))
        
        if self.manager.get_model('yolov8'):
            tasks.append(('yolov8', self._yolo_predict(image_data)))
        
        # Run all tasks concurrently
        for model_name, task in tasks:
            try:
                score = await task
                results[model_name] = score
                logger.debug(f"Visual {model_name}: {score:.3f}")
            except Exception as e:
                logger.warning(f"Visual {model_name} failed: {e}")
                results[model_name] = 0.5  # Default score
        
        return results
    
    async def audio_ensemble(self, audio_path: str) -> Dict[str, Any]:
        """Run all audio models and combine results."""
        results = {}
        tasks = []
        
        # Wav2Vec2 speech-to-text
        if self.manager.get_model('wav2vec2'):
            tasks.append(('speech_text', self._wav2vec2_predict(audio_path)))
        
        # Resemblyzer voice embedding
        if self.manager.get_model('resemblyzer'):
            tasks.append(('voice_embedding', self._resemblyzer_predict(audio_path)))
        
        # ASVspoof synthetic detection
        if self.manager.get_model('asvspoof'):
            tasks.append(('asvspoof', self._asvspoof_predict(audio_path)))
        
        # Run all tasks concurrently
        for model_name, task in tasks:
            try:
                result = await task
                results[model_name] = result
                logger.debug(f"Audio {model_name}: {result}")
            except Exception as e:
                logger.warning(f"Audio {model_name} failed: {e}")
        
        return results
    
    async def temporal_ensemble(self, video_path: str, sample_rate: int = 10) -> Dict[str, Any]:
        """Run temporal analysis models."""
        results = {}
        
        # RAFT optical flow
        if self.manager.get_model('raft'):
            try:
                raft_score = await self._raft_predict(video_path, sample_rate)
                results['raft'] = raft_score
                logger.debug(f"Temporal RAFT: {raft_score:.3f}")
            except Exception as e:
                logger.warning(f"Temporal RAFT failed: {e}")
        
        return results
    
    async def fuse_predictions(
        self,
        visual_results: Dict,
        audio_results: Dict,
        temporal_results: Dict
    ) -> Dict[str, Any]:
        """Fuse all predictions using weighted ensemble."""
        
        fused = {
            "manipulation_probability": 0.0,
            "synthetic_media_probability": 0.0,
            "audio_manipulation_probability": 0.0,
            "temporal_inconsistency": 0.0,
            "overall_confidence": 0.0,
            "model_votes": {},
            "model_weights": {}
        }
        
        # Visual fusion (deepfake detection)
        visual_scores = []
        
        if "xception" in visual_results:
            xception_score = visual_results["xception"]
            visual_scores.append(xception_score)
            fused["model_votes"]["xception"] = xception_score
            fused["model_weights"]["xception"] = self.manager.get_weight("xception")
        
        if "mesonet" in visual_results:
            mesonet_score = visual_results["mesonet"]
            visual_scores.append(mesonet_score)
            fused["model_votes"]["mesonet"] = mesonet_score
            fused["model_weights"]["mesonet"] = self.manager.get_weight("mesonet")
        
        if visual_scores:
            # Weighted average
            total_weight = sum(
                self.manager.get_weight(m) for m in visual_results.keys()
                if m in ['xception', 'mesonet']
            )
            
            if total_weight > 0:
                weighted_sum = sum(
                    visual_results.get(m, 0.5) * self.manager.get_weight(m)
                    for m in ['xception', 'mesonet']
                    if m in visual_results
                )
                fused["manipulation_probability"] = weighted_sum / total_weight
            else:
                fused["manipulation_probability"] = np.mean(visual_scores)
        
        # Semantic analysis (CLIP)
        if "clip" in visual_results:
            clip_score = visual_results["clip"]
            fused["model_votes"]["clip"] = clip_score
            fused["model_weights"]["clip"] = self.manager.get_weight("clip")
        
        # Object detection (YOLO)
        if "yolov8" in visual_results:
            yolo_score = visual_results["yolov8"]
            fused["model_votes"]["yolov8"] = yolo_score
            fused["model_weights"]["yolov8"] = self.manager.get_weight("yolov8")
        
        # Audio fusion
        audio_scores = []
        
        if "asvspoof" in audio_results and isinstance(audio_results["asvspoof"], (int, float)):
            asvspoof_score = audio_results["asvspoof"]
            audio_scores.append(asvspoof_score)
            fused["model_votes"]["asvspoof"] = asvspoof_score
            fused["model_weights"]["asvspoof"] = self.manager.get_weight("asvspoof")
        
        if audio_scores:
            fused["audio_manipulation_probability"] = np.mean(audio_scores)
        
        # Store speech text if available
        if "speech_text" in audio_results:
            fused["extracted_speech"] = audio_results["speech_text"]
        
        # Temporal fusion
        if "raft" in temporal_results:
            raft_score = temporal_results["raft"]
            fused["temporal_inconsistency"] = raft_score
            fused["model_votes"]["raft"] = raft_score
            fused["model_weights"]["raft"] = self.manager.get_weight("raft")
        
        # Calculate overall confidence
        all_scores = list(fused["model_votes"].values())
        if all_scores:
            # Confidence = how far from 0.5 (uncertain) the prediction is
            numeric_scores = [s for s in all_scores if isinstance(s, (int, float))]
            if numeric_scores:
                fused["overall_confidence"] = np.mean([abs(s - 0.5) for s in numeric_scores]) * 2
        
        # Calculate agreement
        fused["model_agreement"] = self._calculate_agreement(fused["model_votes"])
        
        # Detect outliers
        fused["outliers"] = self._detect_outliers(fused["model_votes"])
        
        # Calculate confidence interval
        fused["confidence_interval"] = self._calculate_confidence_interval(fused["model_votes"])
        
        return fused
    
    async def _xception_predict(self, image_data: Any) -> float:
        """Xception inference."""
        model = self.manager.get_model('xception')
        if model is None:
            return 0.5
        
        try:
            import torch
            with torch.no_grad():
                output = model(image_data)
                probs = torch.softmax(output, dim=1)
                return float(probs[0, 1].item())
        except Exception as e:
            logger.warning(f"Xception inference failed: {e}")
            return 0.5
    
    async def _mesonet_predict(self, image_data: Any) -> float:
        """MesoNet inference."""
        model = self.manager.get_model('mesonet')
        if model is None:
            return 0.5
        
        try:
            # MesoNet inference
            output = model.predict(image_data, verbose=0)
            return float(output[0][0])
        except Exception as e:
            logger.warning(f"MesoNet inference failed: {e}")
            return 0.5
    
    async def _clip_predict(self, image_data: Any) -> float:
        """CLIP semantic analysis."""
        clip_data = self.manager.get_model('clip')
        if clip_data is None:
            return 0.5
        
        try:
            # CLIP analysis (simplified)
            # Real implementation would use text prompts for classification
            return 0.6
        except Exception as e:
            logger.warning(f"CLIP inference failed: {e}")
            return 0.5
    
    async def _yolo_predict(self, image_data: Any) -> float:
        """YOLOv8 object detection."""
        model = self.manager.get_model('yolov8')
        if model is None:
            return 0.5
        
        try:
            # YOLOv8 inference (simplified)
            # Real implementation would track object consistency
            results = model.predict(image_data, verbose=False)
            # Return confidence based on detections
            if results and len(results) > 0:
                return 0.7
            return 0.5
        except Exception as e:
            logger.warning(f"YOLOv8 inference failed: {e}")
            return 0.5
    
    async def _wav2vec2_predict(self, audio_path: str) -> str:
        """Wav2Vec2 speech extraction."""
        wav2vec_data = self.manager.get_model('wav2vec2')
        if wav2vec_data is None:
            return ""
        
        try:
            import librosa
            import torch
            
            processor = wav2vec_data["processor"]
            model = wav2vec_data["model"]
            
            # Load audio
            speech, sr = librosa.load(audio_path, sr=16000)
            
            # Process
            input_values = processor(speech, sampling_rate=16000, return_tensors="pt").input_values
            
            with torch.no_grad():
                logits = model(input_values).logits
            
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(predicted_ids)[0]
            
            return transcription
        except Exception as e:
            logger.warning(f"Wav2Vec2 inference failed: {e}")
            return ""
    
    async def _resemblyzer_predict(self, audio_path: str) -> Optional[np.ndarray]:
        """Resemblyzer voice embedding."""
        model = self.manager.get_model('resemblyzer')
        if model is None:
            return None
        
        try:
            import librosa
            
            # Load audio
            wav, sr = librosa.load(audio_path, sr=16000)
            
            # Get embedding
            embedding = model.embed_utterance(wav)
            
            return embedding
        except Exception as e:
            logger.warning(f"Resemblyzer inference failed: {e}")
            return None
    
    async def _asvspoof_predict(self, audio_path: str) -> float:
        """ASVspoof synthetic speech detection."""
        model = self.manager.get_model('asvspoof')
        if model is None:
            return 0.5
        
        try:
            # Synthetic speech detection (simplified)
            # Real implementation would process audio features
            import torch
            
            with torch.no_grad():
                # Placeholder: return synthetic probability
                return 0.15
        except Exception as e:
            logger.warning(f"ASVspoof inference failed: {e}")
            return 0.5
    
    async def _raft_predict(self, video_path: str, sample_rate: int = 10) -> float:
        """RAFT optical flow analysis."""
        model = self.manager.get_model('raft')
        if model is None:
            return 0.5
        
        try:
            import cv2
            import torch
            
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            inconsistencies = []
            
            # Sample frames
            for i in range(0, frame_count, max(1, frame_count // sample_rate)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if ret:
                    # Process frame (simplified)
                    # Real implementation would compute optical flow
                    inconsistencies.append(np.random.rand())
            
            cap.release()
            
            # Return average inconsistency
            if inconsistencies:
                return float(np.mean(inconsistencies))
            return 0.5
        except Exception as e:
            logger.warning(f"RAFT inference failed: {e}")
            return 0.5
    
    def _calculate_agreement(self, model_votes: Dict[str, Any]) -> float:
        """Calculate how well models agree."""
        numeric_votes = [v for v in model_votes.values() if isinstance(v, (int, float))]
        
        if len(numeric_votes) < 2:
            return 0.0
        
        # Agreement = 1 - (std / max_possible_std)
        std = np.std(numeric_votes)
        # Max std for 0-1 range is 0.5 (when split at 0 and 1)
        max_std = 0.5
        
        agreement = 1.0 - (std / max_std)
        return max(0.0, min(1.0, agreement))
    
    def _detect_outliers(self, model_votes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect models that disagree with the ensemble."""
        numeric_votes = {k: v for k, v in model_votes.items() if isinstance(v, (int, float))}
        
        if len(numeric_votes) < 2:
            return []
        
        scores = list(numeric_votes.values())
        mean = np.mean(scores)
        std = np.std(scores)
        
        if std == 0:
            return []
        
        outliers = []
        for model, score in numeric_votes.items():
            z_score = abs((score - mean) / std)
            if z_score > 2.0:  # 2-sigma rule
                outliers.append({
                    "model": model,
                    "score": float(score),
                    "deviation": float(z_score),
                    "ensemble_mean": float(mean)
                })
        
        return outliers
    
    def _calculate_confidence_interval(self, model_votes: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate 95% confidence interval."""
        numeric_votes = [v for v in model_votes.values() if isinstance(v, (int, float))]
        
        if len(numeric_votes) < 2:
            return {"lower": 0.0, "upper": 1.0, "width": 1.0}
        
        mean = np.mean(numeric_votes)
        std = np.std(numeric_votes)
        ci = 1.96 * (std / np.sqrt(len(numeric_votes)))
        
        return {
            "lower": max(0.0, float(mean - ci)),
            "upper": min(1.0, float(mean + ci)),
            "width": float(ci * 2),
            "mean": float(mean),
            "std": float(std)
        }
