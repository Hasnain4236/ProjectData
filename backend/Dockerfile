# Multi-stage build for production-ready backend
FROM node:18-alpine AS base
WORKDIR /app

# Install Python and required system dependencies for AutoViz/SweetViz
RUN apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    python3-dev \
    libffi-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev

# Create Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY scripts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Development stage
FROM base AS development
COPY package*.json ./
RUN npm ci --only=development
COPY . .
EXPOSE 5000
CMD ["npm", "run", "dev"]

# Production dependencies stage
FROM base AS deps
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Production stage
FROM base AS production
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Create uploads and visualizations directories
RUN mkdir -p uploads visualizations/autoviz visualizations/sweetviz

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S backend -u 1001 -G nodejs && \
    chown -R backend:nodejs /app

USER backend

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node healthcheck.js

CMD ["npm", "start"]