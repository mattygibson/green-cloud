#!/bin/bash
# Run garbage collection on the local registry to reclaim disk space
echo "=== Running registry garbage collection ==="
docker exec greencloud-registry registry garbage-collect /etc/docker/registry/config.yml
echo "=== Done ==="
