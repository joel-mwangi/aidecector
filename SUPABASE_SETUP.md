# Supabase PostgreSQL Integration Guide

## 🔒 Security Setup

### Step 1: Secure Your Credentials

**Create `.env` file (NEVER commit to git):**

```bash
# .env (add to .gitignore)
DATABASE_URL=postgresql://postgres:YOUR_NEW_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres
SUPABASE_URL=https://db.hiejdzjkulnticknenay.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**Add to `.gitignore`:**

```
.env
.env.local
.env*.local
*.pth
*.pt
models/
```

### Step 2: Rotate Password NOW

1. Go to: https://supabase.com/dashboard
2. Project → Settings → Database
3. Click "Reset password"
4. Update `.env` file
5. Update docker-compose.yml

---

## 🚀 Quick Integration

### Option 1: Docker Compose (Recommended)

**Update `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres
      - SUPABASE_URL=https://db.hiejdzjkulnticknenay.supabase.co
      - ENVIRONMENT=production
    depends_on:
      - redis
    networks:
      - detector

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - detector

  # Remove postgres service - use Supabase instead

networks:
  detector:
    driver: bridge
```

### Option 2: Environment Variables

**Create `.env.production`:**

```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres
SUPABASE_URL=https://db.hiejdzjkulnticknenay.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

**Load in code:**

```python
from dotenv import load_dotenv
import os

load_dotenv(".env.production")

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
```

---

## 📊 Database Setup

### Step 1: Initialize Supabase Database

**Create schema (run in Supabase SQL editor):**

```sql
-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_path TEXT NOT NULL,
    media_type TEXT NOT NULL,
    claim TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds FLOAT
);

-- Results table
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

-- Evidence items table
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

-- Create indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX idx_tasks_media_type ON tasks(media_type);
CREATE INDEX idx_results_task ON results(id);
CREATE INDEX idx_evidence_task ON evidence_items(task_id);

-- Enable Row Level Security (RLS)
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY;

-- Allow all operations (for service role)
CREATE POLICY "Allow all for service role" ON tasks
    USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for service role" ON results
    USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for service role" ON evidence_items
    USING (true) WITH CHECK (true);
```

### Step 2: Verify Connection

```bash
# Test connection
psql postgresql://postgres:YOUR_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres -c "\dt"
```

---

## 🔗 Code Integration

### Update `src/api/database.py`

```python
import asyncpg
from typing import Optional
import os

class Database:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.pool = None
    
    async def connect(self):
        """Connect to Supabase PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=10,
                max_size=20,
                command_timeout=60,
                ssl=True  # Supabase requires SSL
            )
            print("✓ Connected to Supabase PostgreSQL")
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("✓ Disconnected from Supabase")
    
    # Rest of methods remain the same
```

### Update `src/api/main.py`

```python
from fastapi import FastAPI
from src.api.database import Database
import os

app = FastAPI()

@app.on_event("startup")
async def startup():
    database = Database(os.getenv("DATABASE_URL"))
    await database.connect()
    app.state.db = database

@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, 'db'):
        await app.state.db.disconnect()
```

---

## 🧪 Testing

### Test Connection

```bash
# In Docker
docker compose exec api python3 << 'EOF'
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

async def test():
    pool = await asyncpg.create_pool(DATABASE_URL, ssl=True)
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT NOW()")
        print(f"✓ Connected: {result[0]['now']}")
    await pool.close()

import asyncio
asyncio.run(test())
EOF
```

### Verify Schema

```bash
docker compose exec api python3 << 'EOF'
import asyncpg
import os

async def verify():
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"), ssl=True)
    async with pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        for table in tables:
            print(f"✓ {table['table_name']}")
    await pool.close()

import asyncio
asyncio.run(verify())
EOF
```

---

## 🚀 Deploy with Supabase

### Step 1: Update docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: detector-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    depends_on:
      - redis
    networks:
      - detector
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: detector-cache
    ports:
      - "6379:6379"
    networks:
      - detector
    restart: unless-stopped

networks:
  detector:
    driver: bridge
```

### Step 2: Create `.env.local`

```bash
DATABASE_URL=postgresql://postgres:YOUR_NEW_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres
REDIS_URL=redis://redis:6379
ENVIRONMENT=production
```

### Step 3: Start Services

```bash
# Build and start
docker compose up -d

# Verify connection
docker compose logs api | grep -i "database\|connected"

# Test API
curl http://localhost:8000/health
```

---

## ⚙️ Supabase Configuration

### Enable Extensions

In Supabase Dashboard → SQL Editor, run:

```sql
-- Enable UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Check enabled extensions
SELECT * FROM pg_extension;
```

### Set Up Backups

In Supabase Dashboard:
1. Project Settings → Backups
2. Enable daily backups
3. Set retention to 30 days

### Monitor Usage

In Supabase Dashboard:
- Project Settings → Usage
- Monitor connections, storage, bandwidth

---

## 🔐 Security Best Practices

### 1. Environment Variables

```bash
# .env (NEVER commit)
DATABASE_URL=postgresql://postgres:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres

# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

### 2. Supabase RLS (Row Level Security)

```sql
-- Create public role for API
CREATE ROLE api_user WITH LOGIN;
GRANT USAGE ON SCHEMA public TO api_user;
GRANT ALL ON public.tasks TO api_user;
GRANT ALL ON public.results TO api_user;
GRANT ALL ON public.evidence_items TO api_user;

-- Restrict by policies
CREATE POLICY "Enable read for authenticated users" ON tasks
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON tasks
    FOR INSERT
    WITH CHECK (true);
```

### 3. Connection Pooling

```python
# Use pgbouncer for connection pooling
# Supabase provides pgbouncer connection string

# In Supabase, grab the "Connection pooling" string instead
DATABASE_URL=postgresql://pgbouncer:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:6543/postgres
```

### 4. SSL/TLS

```python
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# asyncpg uses ssl=True by default
pool = await asyncpg.create_pool(
    DATABASE_URL,
    ssl=ssl_context
)
```

---

## 📈 Performance Tips

### 1. Connection Pooling

```python
pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=10,      # Keep connections open
    max_size=20,      # Max connections
    max_cached_statement_lifetime=300,
    max_cacheable_statement_size=15000,
    command_timeout=60
)
```

### 2. Indexes for Common Queries

```sql
-- Already created above, but verify:
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence_items(task_id);
```

### 3. Partition Large Tables (Optional)

```sql
-- For very high volume
CREATE TABLE tasks_2024_q1 PARTITION OF tasks
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

---

## 🔄 Backups & Disaster Recovery

### Manual Backup

```bash
# Backup entire database
pg_dump postgresql://postgres:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres > backup.sql

# Backup specific table
pg_dump -t tasks postgresql://postgres:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres > tasks_backup.sql

# Restore
psql postgresql://postgres:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres < backup.sql
```

### Automated Backups

In Supabase Dashboard:
- Project Settings → Backups
- Enable daily automatic backups

---

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test connection
psql postgresql://postgres:PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres -c "\dt"

# Check if firewall allows connection
telnet db.hiejdzjkulnticknenay.supabase.co 5432

# View connection logs in Docker
docker compose logs api | grep -i "database\|connection\|error"
```

### SSL Errors

```python
# If SSL errors, try:
pool = await asyncpg.create_pool(
    DATABASE_URL,
    ssl='require'  # or True
)

# Or disable (NOT recommended for production)
pool = await asyncpg.create_pool(
    DATABASE_URL,
    ssl=False
)
```

### Performance Issues

```sql
-- Monitor queries
SELECT pid, query, state FROM pg_stat_activity;

-- Check table size
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public';

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'queued';
```

---

## ✅ Deployment Checklist

- [ ] Changed Supabase password
- [ ] Created `.env` file with credentials
- [ ] Added `.env` to `.gitignore`
- [ ] Ran schema setup SQL in Supabase
- [ ] Updated `docker-compose.yml`
- [ ] Updated `src/api/database.py`
- [ ] Tested connection: `docker compose exec api python3 -c "..."`
- [ ] Verified schema: `docker compose exec api python3 -c "..."`
- [ ] Started API: `docker compose up -d`
- [ ] Tested endpoint: `curl http://localhost:8000/health`
- [ ] Enabled backups in Supabase
- [ ] Set up monitoring

---

## 📚 Next Steps

1. **Right now:**
   - Rotate your Supabase password
   - Create `.env` file with new credentials
   - Run schema setup

2. **Today:**
   - Update docker-compose.yml
   - Test connection
   - Verify tables created

3. **This week:**
   - Deploy to production
   - Monitor connections
   - Set up backups

4. **Ongoing:**
   - Monitor performance
   - Review logs
   - Optimize queries as needed

---

## 🚀 Go Live

```bash
# 1. Create .env
echo "DATABASE_URL=postgresql://postgres:NEW_PASSWORD@db.hiejdzjkulnticknenay.supabase.co:5432/postgres" > .env

# 2. Start services
docker compose up -d

# 3. Verify
docker compose exec api curl http://localhost:8000/health

# 4. Test analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"media_type":"image","claim":"test"}'
```

You're connected! 🎉
