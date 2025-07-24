# Quantum Random Number Generator API

A simple REST API for generating quantum random numbers using Qiskit simulator or real quantum hardware.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Setup and Install

```bash
# Install dependencies
uv sync
```

### 2. Start Development Server

```bash
# Start server (port 9001)
uv run uvicorn main:app --host 0.0.0.0 --port 9001

# Or with auto-reload for development
uv run uvicorn main:app --host 0.0.0.0 --port 9001 --reload
```

### 3. Test API

```bash
# Test with Python client
uv run python test_client.py --bits 10 --api-key hogehoge

# Or with curl
curl -X POST "http://localhost:9001/quantum-random" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hogehoge" \
  -d '{"n_bits": 16}'
```

### Quick Commands

```bash
# Show all available tasks
task

# Development workflow
task install    # Install dependencies
task dev        # Start server
task check      # Code quality checks
task test       # Test API

# Docker deployment
task deploy     # Deploy with Docker + Cloudflare tunnel
task status     # Check service status
```

## Configuration

Use environment variables to configure the server:

```bash
# Required: API key for authentication
export API_KEY=your-secret-api-key

# Optional: Backend selection (sim or qpu)
export QUANTUM_BACKEND=sim

# Optional: Number of qubits for simulator
export QUANTUM_N_QUBITS=4

# Start server
uv run uvicorn main:app --host 0.0.0.0 --port 9001
```

## API Endpoints

### Generate Random Bits

**POST** `/quantum-random`

**Headers:**
- `X-API-Key`: Required API key for authentication

**Request:**
```json
{
  "n_bits": 16
}
```

**Response:**
- Content-Type: `application/octet-stream`
- Binary data containing the requested random bits
- Headers:
  - `X-Bits-Generated`: Number of bits generated
  - `X-Backend`: Backend used (simulator/hardware)

### Health Check

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "current_backend": "sim",
  "backends": {
    "sim": "available",
    "qpu": "placeholder (Osaka server not ready)"
  }
}
```

## Testing

Test the API with curl:

```bash
# Basic test
curl "http://localhost:9001/health"

# Generate random bits (requires API key)
curl -X POST "http://localhost:9001/quantum-random" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hogehoge" \
  -d '{"n_bits": 16}'

# Save binary output to file and decode
curl -X POST "http://localhost:9001/quantum-random" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hogehoge" \
  -d '{"n_bits": 10}' \
  -o output.bin

# View binary data as hex
xxd output.bin

# Decode to binary string (Python one-liner - recommended)
python3 -c "
with open('output.bin', 'rb') as f: data = f.read()
bits = ''.join(format(b, '08b') for b in data)
n_bits = 10  # change this to your requested bits
print(f'Binary: {bits[:n_bits]}')
print(f'Hex: {data.hex()}')
"

# Quick binary-only output
python3 -c "
with open('output.bin', 'rb') as f: data = f.read()
print(''.join(format(b, '08b') for b in data)[:10])
"

# With variable
n_bits=10; python3 -c "
with open('output.bin', 'rb') as f: data = f.read()
print(''.join(format(b, '08b') for b in data)[:$n_bits])
"
```

## Hardware Backend

Currently uses a placeholder URL. When the Osaka University server is ready:

1. Update the `hardware_url` in `main.py`
2. Set environment variable: `export QUANTUM_BACKEND=hardware`
3. The API will automatically fallback to simulator if hardware fails

## SSL/HTTPS

The server automatically uses HTTPS if SSL certificates are found in `certs/`:
- `certs/cert.pem` - SSL certificate
- `certs/key.pem` - SSL private key

If certificates are not found, it falls back to HTTP on port 8000.

## Interface Specification

Based on the Slack discussion:

**Request Format:**
```json
{"n_bits": 24}
```

**Authentication:**
- Required `X-API-Key` header with valid API key

**Server Processing:**
1. Server determines available quantum bits (n_qubits)
2. Calculates shots = ceil(n_bits / n_qubits)
3. Creates Hadamard-only quantum circuit
4. Executes circuit for calculated shots
5. Returns exactly n_bits as binary data

## Dependencies

- FastAPI - REST API framework
- Qiskit + Qiskit-Aer - Quantum computing simulation
- Requests - HTTP client for hardware backend
- Uvicorn - ASGI server

## Docker Usage

### Build and Run

```bash
# Using Task (recommended)
task docker-up          # Start API only
task docker-up-tunnel   # Start API + Cloudflare tunnel
task docker-logs        # View logs
task docker-down        # Stop services

# Or using Docker Compose directly
docker compose up -d api
docker compose ps
docker compose logs api
docker compose down
```

### Cloudflare Tunnel Setup

This setup includes Cloudflare Tunnel for secure public access:

1. **Create Cloudflare Tunnel:**
   ```bash
   # Install cloudflared locally
   brew install cloudflared  # macOS
   # or download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

   # Login to Cloudflare
   cloudflared tunnel login

   # Create tunnel
   cloudflared tunnel create quantum-api

   # Get tunnel token from Cloudflare Zero Trust dashboard
   ```

2. **Configure Environment:**
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env file
   QUANTUM_BACKEND=simulator
   QUANTUM_N_QUBITS=4
   API_KEY=your-secret-api-key
   TUNNEL_TOKEN=your-cloudflare-tunnel-token
   PORT=9000
   ```

3. **Deploy:**
   ```bash
   # Using Task (recommended)
   task deploy

   # Or manually
   docker compose up -d

   # Your API will be accessible via Cloudflare tunnel URL
   # Check Cloudflare Zero Trust dashboard for the public URL
   ```

### Environment Variables

Required variables in `.env` file:

```bash
# Quantum Configuration
QUANTUM_BACKEND=sim         # sim or qpu
QUANTUM_N_QUBITS=4          # Number of qubits for simulator

# Security (required)
API_KEY=your-secret-key     # API key for authentication

# Cloudflare Tunnel
TUNNEL_TOKEN=your-token     # Get from Cloudflare Zero Trust

# Server
PORT=9000                   # Server port
```

## Code Formatting

This project uses Ruff for code formatting and linting:

```bash
# Using Task (recommended)
task check      # Run format + lint
task format     # Format only
task lint       # Lint only
task lint-fix   # Auto-fix issues

# Or directly with uv
uv run ruff format main.py
uv run ruff check main.py
uv run ruff check --fix main.py
```

## Task Commands

Use `task --list` to see all available commands:

```bash
task                    # Show available tasks  
task help              # Detailed help
task install           # Install dependencies
task dev               # Start development server
task dev-watch         # Start with auto-reload
task test              # Test API endpoints
task check             # Code quality checks
task deploy            # Deploy with Docker + tunnel
task status            # Show service status
task clean             # Clean temporary files
```

## Files

- `main.py` - Main API server
- `Taskfile.yml` - Task runner configuration
- `pyproject.toml` - Python dependencies and Ruff configuration
- `Dockerfile` - Docker image definition
- `compose.yaml` - Docker Compose configuration with Cloudflare tunnel
- `.dockerignore` - Docker ignore patterns
- `.env.example` - Environment variables template
- `test_client.py` - Optional test client (for local development)
- `certs/` - SSL certificates (auto-generated for local development)
- `README.md` - This file
