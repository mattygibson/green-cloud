#!/bin/sh
# Runtime environment variable injection for Vite-built apps.
# Replaces the build-time placeholder with the actual API URL from environment.
#
# This allows you to build once and deploy to different environments
# (dev, staging, prod) without rebuilding the Docker image.

set -e

# Default to /api if VITE_API_URL is not set (assumes reverse proxy handles routing)
API_URL="${VITE_API_URL:-/api}"

# Replace placeholder in all JS files
find /usr/share/nginx/html -name '*.js' -exec \
    sed -i "s|__VITE_API_URL_PLACEHOLDER__|${API_URL}|g" {} +

echo "Injected VITE_API_URL=${API_URL}"

# Execute the CMD (nginx)
exec "$@"
