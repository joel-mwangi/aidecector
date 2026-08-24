import asyncio
import logging
from src.api.queue import TaskQueue
from src.api.database import Database
from src.audio.forensics import AudioForensics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioWorker:
    """Worker for audio forensics tasks."""

    def __init__(self):
        self.queue = TaskQueue()
        self.db = Database()
        self.forensics = AudioForensics()

    async def start(self):
        await self.queue.connect()
        await self.db.connect()
        logger.info("Audio worker started")

        try:
            while True:
                task = await self.queue.dequeue("audio", timeout=10)
                if not task:
                    continue

                task_id = task.get("task_id")
                payload = task.get("payload", {})

                try:
                    await self.db.update_task_status(task_id, "processing")
                    logger.info(f"Audio worker processing task {task_id}")

                    result = await self.forensics.analyze(
                        media_path=payload.get("media_path"),
                    )

                    await self.db.create_result(task_id, result)
                    await self.db.update_task_status(
                        task_id,
                        "completed",
                        processing_time=result.get("processing_time_seconds"),
                    )
                    logger.info(f"Audio task {task_id} completed")

                except Exception as e:
                    logger.error(f"Audio task {task_id} failed: {e}", exc_info=True)
                    await self.db.update_task_status(task_id, "failed", error=str(e))

        except KeyboardInterrupt:
            logger.info("Audio worker interrupted")
        finally:
            await self.queue.disconnect()
            await self.db.disconnect()


async def main():
    worker = AudioWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
