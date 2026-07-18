#!/bin/bash
# List tags for a specific image in the local registry
# Usage: ./registry-tags.sh greencloud/api
REGISTRY=${REGISTRY_HOST:-localhost:5000}
REPO=${1:?"Usage: $0 <repository-name>"}

echo "=== Tags for ${REPO} in ${REGISTRY} ==="
curl -s "http://${REGISTRY}/v2/${REPO}/tags/list" | python3 -m json.tool 2>/dev/null || \
  curl -s "http://${REGISTRY}/v2/${REPO}/tags/list"
