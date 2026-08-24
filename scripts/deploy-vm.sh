#!/bin/bash
# Quick deploy to single VM with docker-compose

set -e

echo "🚀 Misinformation Detector - Quick Deploy"
echo "=========================================="
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not installed"; exit 1; }

# Set variables
DOMAIN="${1:-localhost}"
POSTGRES_PASS="${2:-$(openssl rand -base64 16)}"
REDIS_PASS="${3:-$(openssl rand -base64 16)}"

echo ""
echo "Configuration:"
echo "  Domain: $DOMAIN"
echo "  PostgreSQL Password: (hidden)"
echo "  Redis Password: (hidden)"
echo ""

# Create .env file
cat > .env <<EOF
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://detector:${POSTGRES_PASS}@postgres:5432/misinformation
REDIS_URL=redis://:${REDIS_PASS}@redis:6379
GPU_ENABLED=false
API_HOST=0.0.0.0
API_PORT=8000
EOF

echo "✓ Created .env file"

# Update docker-compose for production
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  api:
    build: .
    container_name: detector-api
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - DATABASE_URL=postgresql://detector:${DB_PASS}@postgres:5432/misinformation
      - REDIS_URL=redis://:${REDIS_PASS}@redis:6379
      - GPU_ENABLED=false
    volumes:
      - ./src:/app/src
      - ./uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - detector

  visual-worker:
    build: .
    command: python -m src.workers.detection_worker
    environment:
      - WORKER_TYPE=visual
      - REDIS_URL=redis://:${REDIS_PASS}@redis:6379
      - DATABASE_URL=postgresql://detector:${DB_PASS}@postgres:5432/misinformation
    volumes:
      - ./src:/app/src
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - detector

  audio-worker:
    build: .
    command: python -m src.workers.detection_worker
    environment:
      - WORKER_TYPE=audio
      - REDIS_URL=redis://:${REDIS_PASS}@redis:6379
      - DATABASE_URL=postgresql://detector:${DB_PASS}@postgres:5432/misinformation
    volumes:
      - ./src:/app/src
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - detector

  postgres:
    image: postgres:16-alpine
    container_name: detector-db
    environment:
      POSTGRES_USER: detector
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: misinformation
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U detector"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - detector

  redis:
    image: redis:7-alpine
    container_name: detector-cache
    command: redis-server --requirepass ${REDIS_PASS} --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - detector

volumes:
  postgres_data:
  redis_data:

networks:
  detector:
    driver: bridge
EOF

echo "✓ Updated docker-compose.yml"

# Build image
echo ""
echo "Building Docker image..."
docker build -t misinformation-detector:latest -f Dockerfile . 2>&1 | tail -10

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "Checking service health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ API is healthy"
else
    echo "❌ API health check failed"
    docker-compose logs api
    exit 1
fi

# Test analysis endpoint
echo ""
echo "Testing analysis endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "image",
    "claim": "Test claim"
  }')

if echo "$RESPONSE" | grep -q "task_id"; then
    TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)
    echo "✓ Analysis submitted successfully (Task ID: $TASK_ID)"
else
    echo "❌ Analysis submission failed"
    echo "$RESPONSE"
    exit 1
fi

# Print summary
echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Services running:"
docker-compose ps
echo ""
echo "API endpoint: http://$DOMAIN:8000"
echo "Health check: curl http://$DOMAIN:8000/health"
echo ""
echo "Submit analysis:"
echo "  curl -X POST http://$DOMAIN:8000/api/v1/analyze \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"media_type\": \"image\", \"claim\": \"...\"}'"
echo ""
echo "Check status:"
echo "  curl http://$DOMAIN:8000/api/v1/status/{task_id}"
echo ""
echo "Database credentials saved in .env (KEEP SECURE!)"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo ""
