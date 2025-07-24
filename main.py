import logging
import math
import os

from fastapi import FastAPI, HTTPException, Response, Depends, Header
from pydantic import BaseModel
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Random Number Generator", version="2.0.0")


class RandomRequest(BaseModel):
    n_bits: int


def generate_with_simulator(n_bits: int) -> bytes:
    """Generate random bits using Qiskit simulator"""
    n_qubits = int(os.getenv("N_QUBITS", 4))
    shots = math.ceil(n_bits / n_qubits)

    # Create quantum circuit
    qc = QuantumCircuit(n_qubits)
    for i in range(n_qubits):
        qc.h(i)
    qc.measure_all()

    # Run simulation with memory=True to get individual shot results
    simulator = Aer.get_backend("aer_simulator")
    result = simulator.run(transpile(qc, simulator), shots=shots, memory=True).result()
    memory = result.get_memory()
    logger.info(f"Generated {len(memory)} shots of random bits")
    logger.info(f"Memory results: {memory}")

    # Convert to bits
    random_bits = []
    for outcome in memory:
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


def generate_with_qpu(n_bits: int) -> bytes:
    """Generate random bits using QPU (uses same algorithm as simulator)"""
    # QPU uses the same quantum circuit algorithm as simulator
    # In the future, this could connect to actual quantum hardware
    # For now, we use the same implementation
    return generate_with_simulator(n_bits)


def verify_api_key(x_api_key: str = Header(alias="X-API-Key")):
    """Verify API key from header"""
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.post("/quantum-random")
def generate_random_bits(request: RandomRequest, api_key: str = Depends(verify_api_key)):
    """Generate quantum random bits"""
    if request.n_bits <= 0:
        raise HTTPException(status_code=400, detail="n_bits must be positive")

    if request.n_bits > 10000:
        raise HTTPException(status_code=400, detail="n_bits must be <= 10000")

    try:
        # Choose backend based on environment variable only
        backend = os.getenv("BACKEND", "sim").lower()

        if backend == "qpu":
            random_bytes = generate_with_qpu(request.n_bits)
            backend_name = "qpu"
        else:  # default to simulator
            random_bytes = generate_with_simulator(request.n_bits)
            backend_name = "sim"

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
    current_backend = os.getenv("QUANTUM_BACKEND", "sim").lower()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "current_backend": current_backend,
        "backends": {
            "sim": "available",
            "qpu": "placeholder (Osaka server not ready)",
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
