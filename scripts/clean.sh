#!/bin/bash

# Clean up system
docker compose down -v
rm -rf uploads/* models/*.pt models/*.pth cache/* data/downloads/*
echo "System cleaned"
