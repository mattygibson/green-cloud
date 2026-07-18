#!/bin/bash
# Build Docker images and push to local registry
# Usage: ./build-and-push.sh [tag] [platform]
# Examples:
#   ./build-and-push.sh prod                    # Build for ARM64 (Pi target)
#   ./build-and-push.sh dev linux/amd64         # Build for local dev

REGISTRY=${REGISTRY_HOST:-localhost:5000}
TAG=${1:-latest}
PLATFORM=${2:-linux/amd64}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Building images ==="
echo "  Registry: ${REGISTRY}"
echo "  Tag: ${TAG}"
echo "  Platform: ${PLATFORM}"
echo ""

echo "--- Building API ---"
docker buildx build \
  --platform "${PLATFORM}" \
  -t "${REGISTRY}/greencloud/api:${TAG}" \
  --push \
  "${PROJECT_ROOT}/services/app/api/"

if [ $? -ne 0 ]; then
  echo "ERROR: API build failed"
  exit 1
fi

echo ""
echo "--- Building UI ---"
docker buildx build \
  --platform "${PLATFORM}" \
  -t "${REGISTRY}/greencloud/ui:${TAG}" \
  --push \
  "${PROJECT_ROOT}/services/app/ui/"

if [ $? -ne 0 ]; then
  echo "ERROR: UI build failed"
  exit 1
fi

echo ""
echo "=== Done ==="
echo "  API: ${REGISTRY}/greencloud/api:${TAG}"
echo "  UI:  ${REGISTRY}/greencloud/ui:${TAG}"
