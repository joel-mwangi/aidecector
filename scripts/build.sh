#!/bin/bash

# Multimodal Misinformation Detection System - Build Script

set -e

echo "Building Multimodal Misinformation Detection System..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

# Build base image
echo "Building Docker image..."
docker build -t misinformation-detector:latest .

# Create directories
mkdir -p uploads models cache data/downloads

# Initialize database
echo "Initializing database..."
docker compose up -d postgres

# Wait for postgres to be ready
sleep 5

# Start all services
echo "Starting all services..."
docker compose up -d

# Wait for services to be healthy
sleep 10

# Run tests
echo "Running tests..."
docker compose exec -T api pytest tests/ -v --tb=short || true

# Print status
echo ""
echo "✓ Build complete!"
echo ""
echo "Services running:"
docker compose ps
echo ""
echo "API available at: http://localhost:8000"
echo "Health check: curl http://localhost:8000/health"
echo ""
echo "To submit analysis:"
echo "  curl -X POST http://localhost:8000/api/v1/analyze \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"media_url\": \"...\", \"media_type\": \"image\", \"claim\": \"...\"}'"
echo ""
