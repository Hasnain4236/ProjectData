# Multi-stage Dockerfile for ProjectData Backend
# Combines Node.js 18 + Python 3.10 for full-stack analytics

FROM node:18-slim AS base

# Install Python 3.10 and essential build tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy backend package files
COPY backend/package*.json ./backend/

# Install Node.js dependencies
WORKDIR /app/backend
RUN npm ci --only=production

# Setup Python virtual environment
WORKDIR /app/backend/scripts
COPY backend/scripts/requirements.txt ./

# Install CPU-only torch first (much smaller ~2GB vs 8GB for CUDA version)
RUN python3 -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir torch==2.1.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy backend source code
WORKDIR /app
COPY backend/ ./backend/

# Create required directories
RUN mkdir -p /app/backend/uploads /app/backend/visualizations

# Build frontend
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Final stage
FROM base AS production

# Copy built frontend to backend's public folder for serving
COPY --from=frontend-build /app/frontend/build /app/backend/public

# Set environment
ENV NODE_ENV=production
ENV PORT=8080
ENV PYTHON_PATH=/app/backend/scripts/venv/bin/python3

WORKDIR /app/backend

# Expose port (App Runner uses 8080 by default)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

# Start the server
CMD ["node", "server.js"]
