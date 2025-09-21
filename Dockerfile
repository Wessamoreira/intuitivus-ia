# Multi-stage Dockerfile para produção otimizada
# Suporta tanto frontend quanto backend em um único container

# ==========================================
# STAGE 1: Frontend Build
# ==========================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./

# Install dependencies
RUN npm ci --only=production --silent

# Copy source code
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./

# Build frontend
RUN npm run build

# ==========================================
# STAGE 2: Backend Dependencies
# ==========================================
FROM python:3.11-slim AS backend-deps

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 3: Production Runtime
# ==========================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production
ENV ENVIRONMENT=production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

# Copy Python dependencies from builder stage
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=backend-deps /usr/local/bin/ /usr/local/bin/

# Copy built frontend
COPY --from=frontend-builder /app/dist/ /app/static/

# Copy backend application
COPY backend/ ./backend/

# Copy configuration files
COPY docker/ ./docker/

# Setup nginx configuration
RUN cp docker/nginx.conf /etc/nginx/nginx.conf \
    && cp docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /var/log/app /var/run/app \
    && chown -R app:app /app /var/log/app /var/run/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER app

# Expose port
EXPOSE 8080

# Start supervisor (manages nginx + uvicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
