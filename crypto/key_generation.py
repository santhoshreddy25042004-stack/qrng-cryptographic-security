# crypto/key_generation.py

import os
import hashlib
import math
from dotenv import load_dotenv

# QRNG bit generator
from qrng import get_bit_string

# IBM init functions
from qrng.quantum_rng import set_provider_as_IBMQ, set_backend_interactive, get_backend_name


# ======================================================
# GLOBAL FLAG (init IBM only once)
# ======================================================
IBM_INITIALIZED = False


def shannon_entropy(bits: str) -> float:
    p0 = bits.count("0") / len(bits)
    p1 = bits.count("1") / len(bits)
    H = 0.0
    if p0 > 0:
        H -= p0 * math.log2(p0)
    if p1 > 0:
        H -= p1 * math.log2(p1)
    return H


def init_ibm_for_crypto():
    """
    Load IBM token and allow user to select REAL backend.
    Only runs once per program execution.
    If IBM fails, QRNG will automatically fall back to AerSimulator.
    """
    global IBM_INITIALIZED

    if IBM_INITIALIZED:
        return

    load_dotenv()
    token = os.getenv("IBM_API_KEY")

    if not token:
        print("⚠️ IBM_API_KEY not found in .env → will use AerSimulator")
        IBM_INITIALIZED = True
        return

    try:
        print("✅ Loading IBM token from .env ...")
        set_provider_as_IBMQ(token)

        print("✅ Select IBM backend now:")
        set_backend_interactive()

        backend = get_backend_name()
        print(f"✅ IBM backend set for Module-3: {backend}")

    except Exception as e:
        print(f"⚠️ IBM init failed → using AerSimulator\nReason: {e}")

    IBM_INITIALIZED = True


def generate_qrng_key(key_size=256, use_ibm=True):
    """
    Generate AES-256 key using QRNG output + privacy amplification.

    Returns:
        key_bytes (32 bytes),
        qrng_bits (original 256-bit stream),
        key_entropy (entropy of final AES key bits)
    """
    if key_size != 256:
        raise ValueError("AES-256 requires key_size=256 only")

    if use_ibm:
        init_ibm_for_crypto()

    # 1) generate QRNG bits (256 bits)
    qrng_bits = get_bit_string(256)

    # 2) convert bits -> 32 bytes
    raw_bytes = int(qrng_bits, 2).to_bytes(32, byteorder="big")

    # 3) privacy amplification -> SHA-256 output 32 bytes (AES-256 key)
    key_bytes = hashlib.sha256(raw_bytes).digest()

    # 4) entropy should be measured for FINAL key bits (stronger for IEEE)
    key_bits = "".join(format(b, "08b") for b in key_bytes)
    key_entropy = shannon_entropy(key_bits)

    return key_bytes, qrng_bits, key_entropy
