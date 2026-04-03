# crypto/aes_crypto_analysis.py
# MODULE-3 : AES-256 CRYPTOGRAPHIC AVALANCHE ANALYSIS

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Util import Counter

import os
import random
import secrets
import math
import sqlite3
import hashlib
import statistics
from datetime import datetime

# QRNG generator
from crypto.key_generation import generate_qrng_key

# ======================================================
# DATABASE
# ======================================================

DB_FILE = "results.db"
TABLE_NAME = "crypto_results"


def db_setup():

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,

        rng_type TEXT,
        key_entropy REAL,

        ciphertext_hash TEXT,
        plaintext TEXT,

        avalanche_percent REAL,
        avalanche_std REAL
    )
    """)

    conn.commit()
    conn.close()


# ======================================================
# ENTROPY
# ======================================================

def shannon_entropy(bits):

    p0 = bits.count("0") / len(bits)
    p1 = bits.count("1") / len(bits)

    H = 0

    if p0 > 0:
        H -= p0 * math.log2(p0)

    if p1 > 0:
        H -= p1 * math.log2(p1)

    return H


# ======================================================
# STORE RESULT
# ======================================================

def store_crypto_result(rng_type, key_entropy, ciphertext, plaintext, avalanche_mean, avalanche_std):

    cipher_hash = hashlib.sha256(ciphertext).hexdigest()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f"""
    INSERT INTO {TABLE_NAME}
    VALUES(NULL,?,?,?,?,?,?,?)
    """, (

        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        rng_type,
        key_entropy,
        cipher_hash,
        plaintext,
        avalanche_mean,
        avalanche_std
    ))

    conn.commit()
    conn.close()


# ======================================================
# KEY GENERATORS
# ======================================================

def bits_to_key(bits):

    key_bytes = int(bits, 2).to_bytes(32, "big")
    key_bits = "".join(format(b, "08b") for b in key_bytes)

    entropy = shannon_entropy(key_bits)

    return key_bytes, entropy


# ---------- PRNG (Mersenne Twister)

def generate_prng_key():

    bits = "".join(str(random.getrandbits(1)) for _ in range(256))

    key_bytes, entropy = bits_to_key(bits)

    return "PRNG_MersenneTwister", key_bytes, entropy


# ---------- CSPRNG (secrets)

def generate_secrets_key():

    key_bytes = secrets.token_bytes(32)

    bits = "".join(format(b, "08b") for b in key_bytes)

    entropy = shannon_entropy(bits)

    return "CSPRNG_secrets", key_bytes, entropy


# ---------- OS urandom

def generate_urandom_key():

    key_bytes = os.urandom(32)

    bits = "".join(format(b, "08b") for b in key_bytes)

    entropy = shannon_entropy(bits)

    return "OS_urandom", key_bytes, entropy


# ---------- AES CTR DRBG

def generate_aes_ctr_key():

    key = os.urandom(32)

    nonce = os.urandom(16)

    ctr = Counter.new(128, initial_value=int.from_bytes(nonce, "big"))

    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)

    stream = cipher.encrypt(os.urandom(32))

    bits = "".join(format(b, "08b") for b in stream)

    key_bytes, entropy = bits_to_key(bits[:256])

    return "AES_CTR_DRBG", key_bytes, entropy


# ---------- LCG (weak RNG control)

def generate_lcg_key():

    a = 1664525
    c = 1013904223
    m = 2**32

    x = int.from_bytes(os.urandom(4), "big")

    bits = []

    for _ in range(256):

        x = (a * x + c) % m
        bits.append(str(x & 1))

    bits = "".join(bits)

    key_bytes, entropy = bits_to_key(bits)

    return "LCG", key_bytes, entropy


# ---------- HYBRID QRNG + AES

def generate_hybrid_key():

    qrng_data = generate_qrng_key()

    seed = qrng_data["key_bytes"]

    nonce = os.urandom(16)

    ctr = Counter.new(128, initial_value=int.from_bytes(nonce, "big"))

    cipher = AES.new(seed, AES.MODE_CTR, counter=ctr)

    stream = cipher.encrypt(os.urandom(32))

    bits = "".join(format(b, "08b") for b in stream)

    key_bytes, entropy = bits_to_key(bits[:256])

    return "HYBRID_QRNG_AES", key_bytes, entropy


# ======================================================
# FLIP ONE BIT
# ======================================================

def flip_one_bit(key_bytes, bit_index):

    key_list = bytearray(key_bytes)

    byte_index = bit_index // 8
    bit_pos = bit_index % 8

    key_list[byte_index] ^= (1 << bit_pos)

    return bytes(key_list)


# ======================================================
# AVALANCHE EFFECT
# ======================================================

def avalanche_effect(c1, c2):

    b1 = "".join(format(x, "08b") for x in c1)
    b2 = "".join(format(x, "08b") for x in c2)

    changes = sum(1 for a, b in zip(b1, b2) if a != b)

    return (changes / len(b1)) * 100


# ======================================================
# RUN TEST
# ======================================================

def run_crypto_test(rng_type, key, key_entropy, plaintext, trials=10):

    print("\n==============================")
    print("Running:", rng_type)
    print("==============================")

    print("Key entropy:", round(key_entropy, 6))

    plaintext_bytes = plaintext.encode()

    iv = b"\x00" * 16

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext1 = cipher.encrypt(pad(plaintext_bytes, AES.block_size))

    avalanche_list = []

    print("\n========== AVALANCHE TEST ==========")

    for t in range(1, trials + 1):

        bit_index = random.randint(0, 255)

        flipped_key = flip_one_bit(key, bit_index)

        cipher2 = AES.new(flipped_key, AES.MODE_CBC, iv)
        ciphertext2 = cipher2.encrypt(pad(plaintext_bytes, AES.block_size))

        av = avalanche_effect(ciphertext1, ciphertext2)

        avalanche_list.append(av)

        print(f"Trial {t}: flipped bit {bit_index} → {av:.2f}%")

    avalanche_mean = statistics.mean(avalanche_list)
    avalanche_std = statistics.pstdev(avalanche_list)

    print("\nAvalanche mean ± std:", round(avalanche_mean,2), "% ±", round(avalanche_std,2))

    store_crypto_result(
        rng_type,
        key_entropy,
        ciphertext1,
        plaintext,
        avalanche_mean,
        avalanche_std
    )


# ======================================================
# MAIN
# ======================================================

def main():

    print("\nMODULE-3 : AES-256 Avalanche Analysis\n")

    db_setup()

    plaintext = input("Enter message to encrypt: ").strip()

    generators = [

        generate_prng_key,
        generate_secrets_key,
        generate_urandom_key,
        generate_aes_ctr_key,
        generate_lcg_key,
        generate_hybrid_key,
        generate_qrng_key
    ]

    for gen in generators:

        data = gen()

        if isinstance(data, tuple):

            rng_type, key, entropy = data

        else:

            rng_type = data["generator"]
            key = data["key_bytes"]
            entropy = data["entropy"]

        run_crypto_test(rng_type, key, entropy, plaintext)


# ======================================================

if __name__ == "__main__":
    main()