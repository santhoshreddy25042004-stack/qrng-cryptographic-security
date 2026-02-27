# crypto/aes_classical.py  ✅ FINAL IEEE READY (Avalanche mean ± std)
"""
MODULE-3 (Classical): AES-256 Encryption using Classical RNG
-----------------------------------------------------------
✅ Options:
1) Classical RNG (Random seed)
2) Classical RNG (Fixed seed = deterministic)
3) Run BOTH (Random + Fixed) ✅

✅ Features:
- AES-256 CBC encryption/decryption
- Key entropy calculation
- Avalanche effect (5 trials → mean ± std)
- Stores result in SQLite DB: results.db (table: crypto_results)
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import random
import math
import sqlite3
import hashlib
import statistics


# ======================================================
# DB Setup (same as QRNG)
# ======================================================
DB_FILE = "results.db"
TABLE_NAME = "crypto_results"


def db_setup():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # ✅ Keep old structure + add avalanche_std safely
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

    # If table already exists from older runs without avalanche_std:
    try:
        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN avalanche_std REAL")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ======================================================
# Entropy
# ======================================================
def shannon_entropy(bitstream: str) -> float:
    if not bitstream:
        return 0.0
    p0 = bitstream.count("0") / len(bitstream)
    p1 = bitstream.count("1") / len(bitstream)
    H = 0.0
    if p0 > 0:
        H -= p0 * math.log2(p0)
    if p1 > 0:
        H -= p1 * math.log2(p1)
    return H


# ======================================================
# Store result
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
    print("PRNG (random)     Medium/High    Medium            Possible")
    print("PRNG (fixed seed) Medium/High    VERY HIGH         VERY HIGH")
    print("QRNG              High           Minimal           Negligible")
    print("=============================================================\n")


# ======================================================
# Key Generator (Classical)
# ======================================================
def generate_classical_key(fixed_seed: bool):
    """
    Generates AES-256 key from Python PRNG.
    If fixed_seed=True -> deterministic key (same every run)
    """
    if fixed_seed:
        random.seed(42)   # 🔴 deterministic
        rng_type = "classical_fixed_seed"
        note = "⚠️ Fixed seed used: SAME key every run"
    else:
        random.seed(None)  # ✅ unpredictable seed
        rng_type = "classical_random"
        note = "✅ Random seed used: different key every run"

    key_material = str(random.random()).encode()
    key_bytes = hashlib.sha256(key_material).digest()  # 32 bytes (256 bits)

    key_bits = "".join(format(b, "08b") for b in key_bytes)
    key_entropy = shannon_entropy(key_bits)

    return rng_type, key_bytes, key_entropy, note


# ======================================================
# RUN ONE MODE
# ======================================================
def run_classical_mode(fixed_seed: bool, plaintext: str, avalanche_trials: int = 5):
    rng_type, key, key_entropy, note = generate_classical_key(fixed_seed)

    print("\n✅ AES-256 Key generated (Classical)")
    print(f"RNG TYPE      : {rng_type}")
    print(f"🔑 Key Entropy : {key_entropy:.6f} bits")
    print(note)

    # Fixed IV for fair comparison
    iv = b"\x00" * 16
    plaintext_bytes = plaintext.encode()

    # Encrypt with original key
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext1 = cipher.encrypt(pad(plaintext_bytes, AES.block_size))

    # Decrypt check
    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(decipher.decrypt(ciphertext1), AES.block_size).decode(errors="ignore")

    print("\n========== AES OUTPUT ==========")
    print("Ciphertext:", ciphertext1)
    print("Decrypted :", decrypted)

    # -------------------------------------------------
    # Avalanche: 5 trials mean ± std
    # -------------------------------------------------
    avalanche_list = []
    print(f"\n========== AVALANCHE EFFECT ({avalanche_trials} Trials) ==========")

    key_bits_total = len(key) * 8  # ✅ AES key bits (AES-256 => 256 bits)

    for t in range(1, avalanche_trials + 1):
        bit_index = random.randint(0, key_bits_total - 1)  # ✅ 0..255
        flipped_key = flip_one_bit_in_key(key, bit_index=bit_index)

        cipher2 = AES.new(flipped_key, AES.MODE_CBC, iv)
        ciphertext2 = cipher2.encrypt(pad(plaintext_bytes, AES.block_size))

        av = avalanche_effect(ciphertext1, ciphertext2)
        avalanche_list.append(av)

        print(f"Trial {t}: flipped bit {bit_index:3d}  → Avalanche = {av:.2f} %")

    avalanche_mean = statistics.mean(avalanche_list)
    avalanche_std = statistics.pstdev(avalanche_list)  # population std

    print("\n✅ Avalanche Summary:")
    print(f"   Avalanche mean ± std = {avalanche_mean:.2f} % ± {avalanche_std:.2f} %")

    # Store result (store mean + std)
    store_crypto_result(
        rng_type=rng_type,
        key_entropy=key_entropy,
        ciphertext=ciphertext1,
        plaintext=plaintext,
        avalanche_percent=avalanche_mean,
        avalanche_std=avalanche_std
    )

    print("✅ Stored in DB:", DB_FILE, "| Table:", TABLE_NAME)


# ======================================================
# MENU
# ======================================================
def select_mode():
    print("\n==============================")
    print("MODULE-3 (Classical AES): Select Mode")
    print("==============================")
    print("1. Classical RNG (Random seed)")
    print("2. Classical RNG (Fixed seed = deterministic)")
    print("3. Run BOTH (Random + Fixed) ✅")
    return input("\nEnter choice (1-3): ").strip()


# ======================================================
# MAIN
# ======================================================
def main():
    print("\n🔐 MODULE-3: AES-256 Encryption using Classical RNG\n")

    db_setup()
    print_security_comparison()

    choice = select_mode()

    user_text = input("\nEnter message to encrypt: ").strip()
    if not user_text:
        print("❌ Empty message not allowed")
        return

    if choice == "1":
        print("\n==================== RUNNING: CLASSICAL_RANDOM ====================")
        run_classical_mode(fixed_seed=False, plaintext=user_text)

    elif choice == "2":
        print("\n==================== RUNNING: CLASSICAL_FIXED_SEED ====================")
        run_classical_mode(fixed_seed=True, plaintext=user_text)

    elif choice == "3":
        print("\n==================== RUNNING BOTH MODES ====================")

        print("\n------ (1/2) Classical RANDOM says ------")
        run_classical_mode(fixed_seed=False, plaintext=user_text)

        print("\n------ (2/2) Classical FIXED SEED says ------")
        run_classical_mode(fixed_seed=True, plaintext=user_text)

        print("\n✅ BOTH classical modes executed and stored in DB ✅")

    else:
        print("❌ Invalid choice")
        return


if __name__ == "__main__":
    main()
