from qrng import get_bit_string
import hashlib

def generate_qrng_key(key_size=256):
    """
    Generate cryptographic key using QRNG output
    """
    bitstream = get_bit_string(key_size)

    # Convert bitstream to bytes
    raw_bytes = int(bitstream, 2).to_bytes(key_size // 8, byteorder="big")

    # Privacy amplification using SHA-256
    hashed_key = hashlib.sha256(raw_bytes).digest()

    return hashed_key[: key_size // 8]
