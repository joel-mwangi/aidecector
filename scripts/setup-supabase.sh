#!/bin/bash
# Supabase Integration Setup Script

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Supabase PostgreSQL Integration Setup            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get connection details
echo -e "${BLUE}[INFO]${NC} Supabase Connection Setup"
echo ""
echo "Your Supabase details:"
echo "  Host: db.hiejdzjkulnticknenay.supabase.co"
echo "  Port: 5432"
echo "  Database: postgres"
echo "  User: postgres"
echo ""

read -sp "Enter Supabase password: " DB_PASS
echo ""

# Create .env file
echo -e "${BLUE}[STEP 1]${NC} Creating .env file..."

cat > .env <<EOF
# Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres:${DB_PASS}@db.hiejdzjkulnticknenay.supabase.co:5432/postgres

# Redis (local)
REDIS_URL=redis://redis:6379

# Environment
ENVIRONMENT=production
LOG_LEVEL=info

# Optional: Supabase Auth
# SUPABASE_URL=https://db.hiejdzjkulnticknenay.supabase.co
# SUPABASE_ANON_KEY=your_anon_key
# SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
EOF

echo -e "${GREEN}[✓]${NC} Created .env file"

# Add to .gitignore
echo -e "${BLUE}[STEP 2]${NC} Adding to .gitignore..."

if ! grep -q ".env" .gitignore 2>/dev/null; then
    cat >> .gitignore <<EOF

# Environment files
.env
.env.local
.env.*.local

# Credentials
*.pem
*.key
*.crt
EOF
    echo -e "${GREEN}[✓]${NC} Updated .gitignore"
else
    echo -e "${GREEN}[✓]${NC} Already in .gitignore"
fi

# Test connection
echo ""
echo -e "${BLUE}[STEP 3]${NC} Testing Supabase connection..."

python3 << PYEOF
import asyncpg
import asyncio
import sys

async def test_connection():
    try:
        url = "postgresql://postgres:${DB_PASS}@db.hiejdzjkulnticknenay.supabase.co:5432/postgres"
        pool = await asyncpg.create_pool(url, ssl=True, min_size=1, max_size=1)
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT NOW()")
            print(f"✓ Connected to Supabase: {result}")
        await pool.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        return False

if asyncio.run(test_connection()):
    print("Connection successful!")
else:
    print("Connection failed. Check your password and IP allowlist.")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}[✗]${NC} Connection test failed"
    exit 1
fi

echo -e "${GREEN}[✓]${NC} Connection test passed"

# Update docker-compose.yml
echo ""
echo -e "${BLUE}[STEP 4]${NC} Updating docker-compose.yml..."

cat > docker-compose.yml <<'COMPOSE_EOF'
version: '3.8'

services:
  api:
    build: .
    container_name: detector-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - GPU_ENABLED=false
    volumes:
      - ./src:/app/src
      - ./uploads:/app/uploads
    depends_on:
      - redis
    networks:
      - detector
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: detector-cache
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - detector
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:

networks:
  detector:
    driver: bridge
COMPOSE_EOF

echo -e "${GREEN}[✓]${NC} Updated docker-compose.yml"

# Create database schema
echo ""
echo -e "${BLUE}[STEP 5]${NC} Database schema setup"
echo ""
echo "Run this SQL in your Supabase SQL Editor:"
echo ""
echo "---"

cat << 'SQL_EOF'
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_media_type ON tasks(media_type);
CREATE INDEX IF NOT EXISTS idx_results_task ON results(id);
CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence_items(task_id);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for now - restrict as needed)
CREATE POLICY "Enable all operations" ON tasks
    USING (true) WITH CHECK (true);

CREATE POLICY "Enable all operations" ON results
    USING (true) WITH CHECK (true);

CREATE POLICY "Enable all operations" ON evidence_items
    USING (true) WITH CHECK (true);
SQL_EOF

echo "---"
echo ""
echo "After running the SQL, press Enter to continue..."
read

# Start services
echo ""
echo -e "${BLUE}[STEP 6]${NC} Starting Docker services..."

docker compose up -d

# Wait for services
echo -e "${BLUE}[STEP 7]${NC} Waiting for services to be healthy..."
sleep 5

# Verify tables
echo ""
echo -e "${BLUE}[STEP 8]${NC} Verifying database schema..."

docker compose exec -T api python3 << VERIFY_EOF
import asyncpg
import os
import asyncio

async def verify():
    url = os.getenv("DATABASE_URL")
    try:
        pool = await asyncpg.create_pool(url, ssl=True)
        async with pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            
            if not tables:
                print("✗ No tables found. Run the SQL setup in Supabase.")
                return False
            
            print("✓ Database tables:")
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
                print(f"  - {table['table_name']} ({count} rows)")
            
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if pool:
            await pool.close()

if asyncio.run(verify()):
    print("\n✓ Database setup complete!")
else:
    print("\n✗ Database verification failed")

VERIFY_EOF

# Test API
echo ""
echo -e "${BLUE}[STEP 9]${NC} Testing API..."

sleep 2

HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "{}")

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}[✓]${NC} API is healthy"
else
    echo -e "${RED}[✗]${NC} API health check failed"
    docker compose logs api | tail -20
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  Setup Complete!                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Environment variables configured"
echo "✓ Docker Compose updated"
echo "✓ Supabase connection tested"
echo "✓ Services started"
echo ""
echo "Next steps:"
echo "  1. Run the SQL schema in Supabase SQL Editor"
echo "  2. Test API: curl http://localhost:8000/health"
echo "  3. Submit analysis: curl -X POST http://localhost:8000/api/v1/analyze"
echo ""
echo "Security reminders:"
echo "  - .env file is in .gitignore (never commit!)"
echo "  - Change your Supabase password if this was a demo"
echo "  - Enable backups in Supabase Dashboard"
echo ""
echo "📚 See SUPABASE_SETUP.md for detailed documentation"
echo ""
