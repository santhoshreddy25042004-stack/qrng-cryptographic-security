import sqlite3

DB_FILE = "results.db"
TABLE = "crypto_results"


def safe_str(x):
    return str(x) if x is not None else "N/A"


def safe_float(x, digits=2):
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return "N/A"


def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT id, timestamp, rng_type,
                   key_entropy,
                   ciphertext_hash,
                   plaintext,
                   avalanche_percent,
                   avalanche_std
            FROM {TABLE}
            ORDER BY id DESC
            LIMIT 10
        """)
    except sqlite3.OperationalError as e:
        print("❌ DB error:", e)
        print("👉 Run Module-3 first: python -m crypto.aes_qrng / python -m crypto.aes_classical")
        return

    rows = cursor.fetchall()

    if not rows:
        print("❌ No crypto results found in database.")
        return

    print("\n==============================")
    print("🔐 CRYPTO RESULTS (Module-3)")
    print("==============================\n")

    for r in rows:
        print(f"""
ID                 : {safe_str(r[0])}
TIME               : {safe_str(r[1])}
RNG TYPE           : {safe_str(r[2])}
KEY ENTROPY        : {safe_float(r[3], 6)}

PLAINTEXT          : {safe_str(r[5])}
CIPHERTEXT HASH    : {safe_str(r[4])}

AVALANCHE MEAN (%) : {safe_float(r[6], 2)}
AVALANCHE STD  (%) : {safe_float(r[7], 2)}
-----------------------------------
""")

    # ✅ counts by rng type
    cursor.execute(f"SELECT rng_type, COUNT(*) FROM {TABLE} GROUP BY rng_type ORDER BY rng_type")
    counts = cursor.fetchall()

    print("\n==============================")
    print("📊 COUNTS BY RNG TYPE")
    print("==============================")
    for c in counts:
        print(f"{c[0]:22} : {c[1]}")

    conn.close()


if __name__ == "__main__":
    main()
