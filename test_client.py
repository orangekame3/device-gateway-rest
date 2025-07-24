#!/usr/bin/env python3
"""
Test client for Quantum Random Number Generator API
"""

import argparse

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def format_bytes_as_bits(data: bytes, n_bits: int) -> str:
    """
    Convert byte data to formatted bit string

    Args:
        data: Raw byte data
        n_bits: Number of bits that were requested

    Returns:
        Formatted bit string
    """
    bits = []
    for byte in data:
        # Convert each byte to 8-bit binary string
        bit_string = format(byte, "08b")
        bits.extend(bit_string)

    # Only show the requested number of bits
    bits = bits[:n_bits]
    return "".join(bits)


def format_bytes_hex(data: bytes) -> str:
    """
    Format bytes as hexadecimal string

    Args:
        data: Raw byte data

    Returns:
        Hex string with spaces
    """
    return " ".join(f"{byte:02x}" for byte in data)


def analyze_randomness(bits: str) -> dict:
    """
    Basic randomness analysis

    Args:
        bits: Binary string

    Returns:
        Analysis results
    """
    if not bits:
        return {}

    ones = bits.count("1")
    zeros = bits.count("0")
    total = len(bits)

    return {
        "total_bits": total,
        "ones": ones,
        "zeros": zeros,
        "ones_ratio": ones / total if total > 0 else 0,
        "zeros_ratio": zeros / total if total > 0 else 0,
    }


def test_quantum_random_api(
    base_url: str, n_bits: int, api_key: str, backend: str = None, verify_ssl: bool = False
) -> None:
    """
    Test the quantum random API

    Args:
        base_url: Base URL of the API
        n_bits: Number of bits to request
        api_key: API key for authentication
        backend: Backend type to use ('simulator' or 'hardware')
        verify_ssl: Whether to verify SSL certificates
    """
    url = f"{base_url}/quantum-random"
    payload = {"n_bits": n_bits}
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    print("Testing Quantum Random API")
    print(f"URL: {url}")
    print(f"Requesting {n_bits} bits...")
    print("-" * 50)

    try:
        response = requests.post(url, json=payload, headers=headers, verify=verify_ssl, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            # Binary response
            data = response.content
            print(f"Received {len(data)} bytes")

            # Convert to bits
            bits = format_bytes_as_bits(data, n_bits)
            print(f"Binary representation: {bits}")
            print()

            # Show hex representation
            hex_data = format_bytes_hex(data)
            print(f"Hex representation: {hex_data}")
            print()

            # Analyze randomness
            analysis = analyze_randomness(bits)
            if analysis:
                print("Randomness Analysis:")
                print(f"  Total bits: {analysis['total_bits']}")
                print(f"  Ones: {analysis['ones']} ({analysis['ones_ratio']:.2%})")
                print(f"  Zeros: {analysis['zeros']} ({analysis['zeros_ratio']:.2%})")
                print()

            # Show bit groups for easier reading
            if len(bits) > 8:
                print("Bit groups (8-bit chunks):")
                for i in range(0, len(bits), 8):
                    chunk = bits[i : i + 8]
                    byte_val = int(chunk.ljust(8, "0"), 2)  # Pad with zeros if needed
                    print(f"  {chunk:<8} = {byte_val:3d} (0x{byte_val:02x})")
        else:
            # Error response
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except Exception:
                print(f"Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def test_health_endpoints(base_url: str, verify_ssl: bool = False) -> None:
    """
    Test health check endpoints

    Args:
        base_url: Base URL of the API
        verify_ssl: Whether to verify SSL certificates
    """
    endpoints = ["/", "/health"]

    print("Testing Health Endpoints")
    print("-" * 30)

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, verify=verify_ssl, timeout=10)
            print(f"{endpoint}: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Test client for Quantum Random API")
    parser.add_argument(
        "--url",
        default="http://localhost:9001",
        help="Base URL of the API (default: http://localhost:9001)",
    )
    parser.add_argument(
        "--bits", type=int, default=16, help="Number of bits to request (default: 16)"
    )
    parser.add_argument(
        "--api-key", 
        default="hogehoge",
        help="API key for authentication (default: hogehoge)"
    )
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    parser.add_argument("--no-health", action="store_true", help="Skip health check tests")

    args = parser.parse_args()

    print("Quantum Random Number Generator - Test Client")
    print("=" * 50)
    print()

    # Test health endpoints
    if not args.no_health:
        test_health_endpoints(args.url, args.verify_ssl)

    # Test quantum random endpoint
    test_quantum_random_api(args.url, args.bits, args.api_key, None, args.verify_ssl)


if __name__ == "__main__":
    main()
