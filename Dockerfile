# Multi-stage Dockerfile for Smart Contract Security Auditor
# Stage 1: Builder - Install heavy dependencies
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Go for Medusa
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && \
    rm go1.21.5.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Install Medusa
RUN go install github.com/crytic/medusa@latest

# Install solc
RUN wget -q https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux && \
    chmod +x solc-static-linux && \
    mv solc-static-linux /usr/local/bin/solc

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binaries from builder
COPY --from=builder /go/bin/medusa /usr/local/bin/medusa
COPY --from=builder /usr/local/bin/solc /usr/local/bin/solc

# Create non-root user
RUN groupadd -r auditor && useradd -r -g auditor auditor

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=auditor:auditor . .

# Create data directory for artifacts
RUN mkdir -p /data/artifacts && chown -R auditor:auditor /data

# Switch to non-root user
USER auditor

# Environment variables with safe defaults
ENV MODE=simulation \
    PYTHONUNBUFFERED=1 \
    MEDUSA_TIMEOUT=60 \
    LOG_LEVEL=INFO

# Expose port for service mode
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command: CLI mode
ENTRYPOINT ["python3"]
CMD ["auditor_ai.py", "5"]
