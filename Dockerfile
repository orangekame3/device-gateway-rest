# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Qiskit
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY main.py ./

# Create certs directory (SSL certificates can be mounted here)
RUN mkdir -p certs
# Set environment variables
ENV QUANTUM_BACKEND=simulator
ENV QUANTUM_N_QUBITS=4
