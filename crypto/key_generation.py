# crypto/key_generation.py
# FINAL VERSION (QRNG + PRNG SUPPORT FOR MODULE-3)

import os
import hashlib
import math
import random
from dotenv import load_dotenv

# QRNG bit generator
from qrng import get_bit_string

# IBM init functions
from qrng.quantum_rng import (
    set_provider_as_IBMQ,
    set_backend_interactive,
    get_backend_name
)


# ======================================================
# GLOBAL FLAG (init IBM only once)
# ======================================================

IBM_INITIALIZED = False


# ======================================================
# SHANNON ENTROPY
# ======================================================

def shannon_entropy(bits: str) -> float:

    p0 = bits.count("0") / len(bits)
    p1 = bits.count("1") / len(bits)

    H = 0.0

    if p0 > 0:
        H -= p0 * math.log2(p0)

    if p1 > 0:
        H -= p1 * math.log2(p1)

    return H


# ======================================================
# IBM INITIALIZATION
# ======================================================

def init_ibm_for_crypto():

    global IBM_INITIALIZED

    if IBM_INITIALIZED:
        return

    load_dotenv()

    token = os.getenv("IBM_API_KEY")

    if not token:
        print("⚠️ IBM_API_KEY not found → using AerSimulator")
        IBM_INITIALIZED = True
        return

    try:

        print("✅ Loading IBM token from .env...")
        set_provider_as_IBMQ(token)

        print("✅ Select IBM backend for Module-3:")
        set_backend_interactive()

        backend = get_backend_name()

        print(f"✅ Using backend: {backend}")

    except Exception as e:

        print(f"⚠️ IBM init failed → using simulator\nReason: {e}")

    IBM_INITIALIZED = True


# ======================================================
# QRNG KEY GENERATION
# ======================================================

def generate_qrng_key(key_size=256, use_ibm=True):

    if key_size != 256:
        raise ValueError("AES-256 requires key_size=256")

    if use_ibm:
        init_ibm_for_crypto()

    # generate QRNG bits
    qrng_bits = get_bit_string(256)

    raw_bytes = int(qrng_bits, 2).to_bytes(32, byteorder="big")

    # privacy amplification
    key_bytes = hashlib.sha256(raw_bytes).digest()

    key_bits = "".join(format(b, "08b") for b in key_bytes)

    entropy = shannon_entropy(key_bits)

    return {
        "generator": "QRNG",
        "key_bytes": key_bytes,
        "key_bits": key_bits,
        "entropy": entropy
    }


# ======================================================
# PRNG KEY GENERATION (MERSENNE TWISTER)
# ======================================================

def generate_prng_key(key_size=256):

    if key_size != 256:
        raise ValueError("AES-256 requires key_size=256")

    bits = "".join(str(random.getrandbits(1)) for _ in range(256))

    raw_bytes = int(bits, 2).to_bytes(32, byteorder="big")

    key_bytes = hashlib.sha256(raw_bytes).digest()

    key_bits = "".join(format(b, "08b") for b in key_bytes)

    entropy = shannon_entropy(key_bits)

    return {
        "generator": "PRNG_MersenneTwister",
        "key_bytes": key_bytes,
        "key_bits": key_bits,
        "entropy": entropy
    }