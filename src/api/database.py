import asyncpg
import asyncpg
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database handler — compatible with Supabase and local Postgres."""

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is not set")
        self.pool = None

    async def connect(self):
        """Create connection pool. Uses SSL when connecting to Supabase."""
        use_ssl = _requires_ssl(self.connection_string)
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=2,
            max_size=10,
            command_timeout=60,
            ssl="require" if use_ssl else None,
            statement_cache_size=0,
        )
        await self._init_schema()
        logger.info("Database connected")

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database disconnected")

    async def _init_schema(self):
        """Initialize database schema if tables do not already exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY,
                    media_path TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    claim TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    error TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    processing_time_seconds FLOAT
                );

                CREATE TABLE IF NOT EXISTS results (
                    id UUID PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                    media_assessment JSONB,
                    claim_assessment JSONB,
                    provenance JSONB,
                    evidence JSONB,
                    evidence_quality FLOAT,
                    overall_confidence FLOAT,
                    classification TEXT,
                    info_classification TEXT,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS evidence_items (
                    id SERIAL PRIMARY KEY,
                    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    source_type TEXT,
                    statement TEXT,
                    relationship TEXT,
                    reliability FLOAT,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_tasks_media_type ON tasks(media_type);
                CREATE INDEX IF NOT EXISTS idx_results_task ON results(id);
                CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence_items(task_id);
            """)

    # ------------------------------------------------------------------
    # Task operations
    # ------------------------------------------------------------------

    async def create_task(
        self,
        task_id: str,
        media_path: str,
        media_type: str,
        claim: Optional[str],
        status: str,
    ):
        """Create a new analysis task."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tasks (id, media_path, media_type, claim, status)
                VALUES ($1, $2, $3, $4, $5)
                """,
                task_id, media_path, media_type, claim, status,
            )

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task metadata."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
            return dict(row) if row else None

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None,
        processing_time: Optional[float] = None,
    ):
        """Update task status."""
        async with self.pool.acquire() as conn:
            if status == "completed":
                await conn.execute(
                    """
                    UPDATE tasks
                    SET status = $1, completed_at = NOW(), processing_time_seconds = $2
                    WHERE id = $3
                    """,
                    status, processing_time, task_id,
                )
            else:
                await conn.execute(
                    "UPDATE tasks SET status = $1, error = $2 WHERE id = $3",
                    status, error, task_id,
                )

    async def list_tasks(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent tasks ordered by creation time."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, media_type, claim, status, created_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, skip,
            )
            return [dict(row) for row in rows]

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task and all associated data (cascade handles children)."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM tasks WHERE id = $1", task_id)
        return result == "DELETE 1"

    async def cleanup_old_tasks(self, days: int = 7):
        """Delete tasks older than N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM tasks WHERE created_at < $1", cutoff
            )
        count = int(result.split()[-1])
        logger.info(f"Cleaned up {count} old tasks")

    # ------------------------------------------------------------------
    # Result operations
    # ------------------------------------------------------------------

    async def create_result(self, task_id: str, result: Dict[str, Any]):
        """Store analysis result."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO results (
                    id, media_assessment, claim_assessment, provenance,
                    evidence, evidence_quality, overall_confidence,
                    classification, info_classification, explanation
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO UPDATE SET
                    media_assessment    = EXCLUDED.media_assessment,
                    claim_assessment    = EXCLUDED.claim_assessment,
                    provenance          = EXCLUDED.provenance,
                    evidence            = EXCLUDED.evidence,
                    evidence_quality    = EXCLUDED.evidence_quality,
                    overall_confidence  = EXCLUDED.overall_confidence,
                    classification      = EXCLUDED.classification,
                    info_classification = EXCLUDED.info_classification,
                    explanation         = EXCLUDED.explanation
                """,
                task_id,
                json.dumps(result.get("media_assessment", {})),
                json.dumps(result.get("claim_assessment", {})),
                json.dumps(result.get("provenance", {})),
                json.dumps(result.get("evidence", [])),
                result.get("evidence_quality", 0.0),
                result.get("overall_confidence", 0.0),
                result.get("classification", "UNKNOWN"),
                result.get("info_classification", "UNKNOWN"),
                result.get("explanation", ""),
            )

    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM results WHERE id = $1", task_id)
            return dict(row) if row else None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _requires_ssl(connection_string: str) -> bool:
    """Return True when the connection string points to a remote Supabase host."""
    return "supabase.co" in connection_string or "supabase.com" in connection_string