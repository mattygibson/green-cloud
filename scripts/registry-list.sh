#!/bin/bash
# List all repositories in the local registry
REGISTRY=${REGISTRY_HOST:-localhost:5000}

echo "=== Repositories in ${REGISTRY} ==="
curl -s "http://${REGISTRY}/v2/_catalog" | python3 -m json.tool 2>/dev/null || \
  curl -s "http://${REGISTRY}/v2/_catalog"
