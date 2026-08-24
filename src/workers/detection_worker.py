import asyncio
import logging
from src.api.queue import TaskQueue
from src.api.database import Database
from src.inference.pipeline import AnalysisPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionWorker:
    """Main detection worker processing queued analysis tasks."""
    
    def __init__(self):
        self.queue = TaskQueue()
        self.db = Database()
        self.pipeline = AnalysisPipeline()
    
    async def start(self):
        """Start worker loop."""
        await self.queue.connect()
        await self.db.connect()
        
        logger.info("Detection worker started")
        
        try:
            while True:
                task = await self.queue.dequeue("analysis", timeout=10)
                
                if not task:
                    continue
                
                task_id = task.get("task_id")
                payload = task.get("payload")
                
                try:
                    await self.db.update_task_status(task_id, "processing")
                    
                    logger.info(f"Processing task {task_id}")
                    
                    result = await self.pipeline.analyze(
                        task_id=task_id,
                        media_path=payload["media_path"],
                        media_type=payload["media_type"],
                        claim=payload.get("claim"),
                        include_evidence_graph=payload.get("include_evidence_graph", True)
                    )
                    
                    await self.db.create_result(task_id, result)
                    await self.db.update_task_status(
                        task_id,
                        "completed",
                        processing_time=result.get("processing_time_seconds")
                    )
                    
                    logger.info(f"Task {task_id} completed successfully")
                
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
                    await self.db.update_task_status(task_id, "failed", error=str(e))
        
        except KeyboardInterrupt:
            logger.info("Worker interrupted")
        finally:
            await self.queue.disconnect()
            await self.db.disconnect()

async def main():
    worker = DetectionWorker()
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
