CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY,
    media_path TEXT NOT NULL,
    media_type TEXT NOT NULL,
    claim TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds FLOAT
);

CREATE TABLE IF NOT EXISTS results (
    id UUID PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    media_assessment JSONB,
    claim_assessment JSONB,
    provenance JSONB,
    evidence JSONB,
    evidence_graph JSONB,
    evidence_quality FLOAT,
    overall_confidence FLOAT,
    classification TEXT,
    info_classification TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_type TEXT,
    statement TEXT,
    relationship TEXT,
    reliability FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_media_type ON tasks(media_type);
CREATE INDEX IF NOT EXISTS idx_results_task ON results(id);
CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence_items(task_id);
