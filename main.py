import logging
import math
import os

import requests
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Random Number Generator", version="2.0.0")


class RandomRequest(BaseModel):
    n_bits: int
    backend: str | None = None


def generate_with_simulator(n_bits: int) -> bytes:
    """Generate random bits using Qiskit simulator"""
    n_qubits = 4
    shots = math.ceil(n_bits / n_qubits)

    # Create quantum circuit
    qc = QuantumCircuit(n_qubits, n_qubits)
    for i in range(n_qubits):
        qc.h(i)
    qc.measure_all()

    # Run simulation
    simulator = Aer.get_backend("aer_simulator")
    result = simulator.run(transpile(qc, simulator), shots=shots).result()
    counts = result.get_counts()

    # Convert to bits
    random_bits = []
    for outcome, count in counts.items():
        for _ in range(count):
            clean_outcome = outcome.replace(" ", "")
            random_bits.extend([int(bit) for bit in clean_outcome])

    # Adjust to required bits
    random_bits = random_bits[:n_bits]
    while len(random_bits) < n_bits:
        random_bits.append(0)

    # Convert to bytes
    byte_array = bytearray()
    for i in range(0, len(random_bits), 8):
        byte_bits = random_bits[i : i + 8]
        while len(byte_bits) < 8:
            byte_bits.append(0)

        byte_value = 0
        for j, bit in enumerate(byte_bits):
            byte_value |= bit << j
        byte_array.append(byte_value)

    return bytes(byte_array)


def generate_with_hardware(n_bits: int) -> bytes:
    """Generate random bits using real hardware"""
    hardware_url = "https://quantum-device.example.com/api/v1"

    payload = {"n_bits": n_bits}

    try:
        response = requests.post(f"{hardware_url}/quantum-random", json=payload, timeout=30)

        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Hardware error: {response.status_code}")

    except Exception as e:
        logger.error(f"Hardware failed: {e}, falling back to simulator")
        return generate_with_simulator(n_bits)


@app.post("/quantum-random")
def generate_random_bits(request: RandomRequest):
    """Generate quantum random bits"""
    if request.n_bits <= 0:
        raise HTTPException(status_code=400, detail="n_bits must be positive")

    if request.n_bits > 10000:
        raise HTTPException(status_code=400, detail="n_bits must be <= 10000")

    try:
        # Choose backend

        use_hardware = (
            request.backend == "hardware"
            or os.getenv("QUANTUM_BACKEND", "simulator").lower() == "hardware"
        )

        if use_hardware:
            random_bytes = generate_with_hardware(request.n_bits)
            backend_name = "hardware"
        else:
            random_bytes = generate_with_simulator(request.n_bits)
            backend_name = "simulator"

        return Response(
            content=random_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Length": str(len(random_bytes)),
                "X-Bits-Generated": str(request.n_bits),
                "X-Backend": backend_name,
            },
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
def root():
    """Health check"""
    return {"message": "Quantum Random Number Generator API", "status": "running"}


@app.get("/health")
def health():
    """Health check with backend info"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "backends": {
            "simulator": "available",
            "hardware": "placeholder (Osaka server not ready)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # SSL setup
    cert_file = "certs/cert.pem"
    key_file = "certs/key.pem"

    port = int(os.getenv("PORT", 9000))

    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info(f"Starting HTTPS server on port {port}")
        uvicorn.run(
            app, host="0.0.0.0", port=port, ssl_keyfile=key_file, ssl_certfile=cert_file, workers=1
        )
    else:
        logger.info(f"Starting HTTP server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
