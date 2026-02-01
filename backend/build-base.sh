#!/bin/bash
# Build the base image with CPU-only PyTorch and ML dependencies
# Run this script once, or when requirements-base.txt changes

set -e

echo "Building teduco-backend-base:v1..."
docker build -f dockerfile.base -t teduco-backend-base:v1 -t teduco-backend-base:latest .

echo ""
echo "✅ Base image built successfully!"
echo ""
echo "Tagged as:"
echo "  - teduco-backend-base:v1"
echo "  - teduco-backend-base:latest"
echo ""
echo "Next steps:"
echo "  cd .. && docker-compose up --build"
