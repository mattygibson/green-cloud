# ---------------------------------------------------------
# GreenCloud Template: React + Vite
# A production-ready Dockerfile for React apps built with Vite.
#
# Usage:
#   1. Copy this file, nginx.conf, docker-entrypoint.sh into your project root
#   2. Build: docker build -t my-ui .
#   3. Run:   docker run -p 3000:80 -e VITE_API_URL=http://localhost:8000 my-ui
# ---------------------------------------------------------

# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /build

# Copy dependency files first (maximises Docker layer caching)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .

# Build with a placeholder — real URL injected at runtime
ENV VITE_API_URL=__VITE_API_URL_PLACEHOLDER__
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine AS runtime

# Copy built assets
COPY --from=builder /build/dist /usr/share/nginx/html

# Custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Runtime config injection script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
