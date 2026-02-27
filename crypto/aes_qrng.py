# crypto/aes_qrng.py  ✅ FINAL IEEE READY (Avalanche mean ± std)

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import sqlite3
import hashlib
import random
import statistics

from crypto.key_generation import generate_qrng_key


# ======================================================
# DB Setup
# ======================================================
DB_FILE = "results.db"
TABLE_NAME = "crypto_results"


def db_setup():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # ✅ Keep old columns + add new ones safely
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

            rng_type TEXT,
            key_entropy REAL,

            ciphertext_hash TEXT,
            plaintext TEXT,

            avalanche_percent REAL,
            avalanche_std REAL
        )
    """)

    # If DB table already created earlier without avalanche_std column:
    try:
        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN avalanche_std REAL")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ======================================================
# Store Result
# ======================================================
def store_crypto_result(rng_type, key_entropy, ciphertext, plaintext, avalanche_percent, avalanche_std):
    cipher_hash = hashlib.sha256(ciphertext).hexdigest()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO {TABLE_NAME}
        (rng_type, key_entropy, ciphertext_hash, plaintext, avalanche_percent, avalanche_std)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (rng_type, key_entropy, cipher_hash, plaintext, avalanche_percent, avalanche_std))

    conn.commit()
    conn.close()


# ======================================================
# Avalanche Effect
# ======================================================
def flip_one_bit_in_key(key_bytes: bytes, bit_index: int) -> bytes:
    """
    Flip exactly 1 bit of AES key.
    bit_index: 0 .. (len(key_bytes)*8 - 1)

    ✅ AES-256 key length = 32 bytes = 256 bits
    so bit_index range must be 0..255
    """
    key_list = bytearray(key_bytes)

    total_bits = len(key_list) * 8
    if bit_index < 0 or bit_index >= total_bits:
        raise ValueError(f"bit_index must be in range 0..{total_bits - 1}")

    byte_index = bit_index // 8
    bit_in_byte = bit_index % 8

    key_list[byte_index] ^= (1 << bit_in_byte)
    return bytes(key_list)


def avalanche_effect(cipher1: bytes, cipher2: bytes) -> float:
    """
    % of bits changed in ciphertext
    """
    b1 = "".join(format(x, "08b") for x in cipher1)
    b2 = "".join(format(x, "08b") for x in cipher2)

    min_len = min(len(b1), len(b2))
    if min_len == 0:
        return 0.0

    changes = sum(1 for i in range(min_len) if b1[i] != b2[i])
    return (changes / min_len) * 100.0


# ======================================================
# Security Comparison Table (IEEE)
# ======================================================
def print_security_comparison():
    print("\n==================== SECURITY COMPARISON ====================")
    print("Key Source        Entropy        Predictability     Key Reuse Risk")
    print("-------------------------------------------------------------")
    print("PRNG              Lower          Higher            Possible")
    print("QRNG              Higher         Minimal           Negligible")
    print("=============================================================\n")


# ======================================================
# MAIN
# ======================================================
def main():
    print("\n🔐 MODULE-3: AES-256 Encryption using QRNG (IEEE Enhanced)\n")

    db_setup()
    print_security_comparison()

    # ✅ Generate QRNG AES-256 key
    key_bytes, qrng_bits, key_entropy = generate_qrng_key(256, use_ibm=True)
    print("✅ QRNG Key generated (AES-256)")
    print(f"🔑 Key Entropy = {key_entropy:.6f} bits")

    # IMPORTANT: fixed IV for fair comparison
    iv = b"\x00" * 16

    user_text = input("Enter message to encrypt: ").strip()
    if not user_text:
        print("❌ Empty message not allowed")
        return

    plaintext_bytes = user_text.encode()

    # ------------------------------
    # Encryption with ORIGINAL KEY
    # ------------------------------
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    ciphertext1 = cipher.encrypt(pad(plaintext_bytes, AES.block_size))

    print("\n========== AES OUTPUT ==========")
    print("Ciphertext (QRNG key):", ciphertext1)

    # ------------------------------
    # Decryption check
    # ------------------------------
    decipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted = unpad(decipher.decrypt(ciphertext1), AES.block_size)
    print("Decrypted:", decrypted.decode(errors="ignore"))

    # ------------------------------
    # Avalanche: 5 Trials (mean ± std)
    # ------------------------------
    trials = 5
    avalanche_list = []

    print("\n========== AVALANCHE EFFECT (5 Trials) ==========")

    key_bits_total = len(key_bytes) * 8  # ✅ AES key bits (AES-256 => 256 bits)

    for t in range(1, trials + 1):
        bit_index = random.randint(0, key_bits_total - 1)  # ✅ 0..255

        flipped_key = flip_one_bit_in_key(key_bytes, bit_index=bit_index)

        cipher2 = AES.new(flipped_key, AES.MODE_CBC, iv)
        ciphertext2 = cipher2.encrypt(pad(plaintext_bytes, AES.block_size))

        avalanche_percent = avalanche_effect(ciphertext1, ciphertext2)
        avalanche_list.append(avalanche_percent)

        print(f"Trial {t}: flipped bit {bit_index:3d}  → Avalanche = {avalanche_percent:.2f} %")

    avalanche_mean = statistics.mean(avalanche_list)
    avalanche_std = statistics.pstdev(avalanche_list)  # population std

    print("\n✅ Avalanche Summary:")
    print(f"   Avalanche mean ± std = {avalanche_mean:.2f} % ± {avalanche_std:.2f} %")

    # ------------------------------
    # Store mean + std in DB
    # ------------------------------
    store_crypto_result(
        rng_type="qrng",
        key_entropy=key_entropy,
        ciphertext=ciphertext1,
        plaintext=user_text,
        avalanche_percent=avalanche_mean,
        avalanche_std=avalanche_std
    )

    print("\n✅ QRNG crypto result stored in DB (crypto_results table)")


if __name__ == "__main__":
    main()
