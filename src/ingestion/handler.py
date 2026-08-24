import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class IngestHandler:
    """Media ingestion and validation handler."""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def ingest(
        self,
        task_id: str,
        media_url: Optional[str] = None,
        media_data: Optional[bytes] = None,
        media_type: str = "image",
        claim: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest media from URL or raw bytes.
        
        Returns dict with:
        - path: local file path
        - hash: SHA256 hash of content
        - size: file size in bytes
        - duration: duration in seconds (for video/audio)
        """
        
        try:
            if media_url:
                logger.info(f"Ingesting from URL: {media_url}")
                media_data = await self._download_media(media_url)
            
            if not media_data:
                raise ValueError("No media data provided")
            
            # Validate size
            if len(media_data) > self._get_size_limit(media_type):
                raise ValueError(f"File too large. Max: {self._get_size_limit(media_type)} bytes")
            
            # Compute hash
            file_hash = hashlib.sha256(media_data).hexdigest()
            
            # Save file
            filename = f"{task_id}_{media_type}.bin"
            file_path = self.upload_dir / filename
            
            with open(file_path, "wb") as f:
                f.write(media_data)
            
            logger.info(f"Media ingested: {file_path} ({len(media_data)} bytes)")
            
            return {
                "path": str(file_path),
                "hash": file_hash,
                "size": len(media_data),
                "media_type": media_type,
                "claim": claim
            }
        
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            raise
    
    async def _download_media(self, url: str) -> bytes:
        """Download media from URL."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to download: {response.status}")
                    return await response.read()
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise
    
    def _get_size_limit(self, media_type: str) -> int:
        """Get size limit for media type."""
        limits = {
            "image": 50 * 1024 * 1024,   # 50 MB
            "video": 500 * 1024 * 1024,  # 500 MB
            "audio": 100 * 1024 * 1024   # 100 MB
        }
        return limits.get(media_type, 100 * 1024 * 1024)
