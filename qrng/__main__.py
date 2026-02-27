# qrng/main.py  ✅ FINAL READY IEEE VERSION (WITH MODULE-1 DB SAVE)

import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from .quantum_rng import (
    set_provider_as_IBMQ,
    set_backend_interactive,
    get_raw_bit_string,
    get_bit_string,
    get_backend_name,
    get_readout_error_rate,
)

# =========================================================
# ✅ Module-1 DB storage (Bias + Entropy BEFORE/AFTER)
# =========================================================

# ✅ Always store results.db in project root (not current folder)
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results.db"))
TABLE_M1_GRAPH = "module1_graph_results"


def ensure_module1_graph_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_M1_GRAPH} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        backend TEXT,
        shots INTEGER,
        n_final_bits INTEGER,
        raw_bias REAL,
        final_bias REAL,
        raw_entropy REAL,
        final_entropy REAL
    )
    """)
    conn.commit()
    conn.close()


def save_module1_graph_row(backend, shots, n_final_bits, before, after):
    """
    before = dict from report_metrics(raw_bits)
    after  = dict from report_metrics(final_bits)
    """
    ensure_module1_graph_table()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f"""
    INSERT INTO {TABLE_M1_GRAPH} (
        time, backend, shots, n_final_bits,
        raw_bias, final_bias, raw_entropy, final_entropy
    ) VALUES (?,?,?,?,?,?,?,?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(backend),
        int(shots),
        int(n_final_bits),
        float(before["bias"]),
        float(after["bias"]),
        float(before["entropy"]),
        float(after["entropy"]),
    ))

    conn.commit()
    conn.close()
    print(f"✅ Module-1 graph data saved to DB table: {TABLE_M1_GRAPH}")


# =========================================================
# Printing
# =========================================================
def _print_metrics_block(title: str, m: dict):
    print(f"\n========== {title} ==========")
    print(f"Length      : {m.get('length')}")
    print(f"Zeros       : {m.get('zeros')}")
    print(f"Ones        : {m.get('ones')}")
    print(f"P(0)        : {m.get('p0')}")
    print(f"P(1)        : {m.get('p1')}")
    print(f"Bias        : {m.get('bias')}")
    print(f"Entropy     : {m.get('entropy')}")
    if "freq_p_value" in m:
        print(f"Freq p-value: {m.get('freq_p_value')}")
    if "runs_p_value" in m:
        print(f"Runs p-value: {m.get('runs_p_value')}")


def main():
    print("🔑 qRNG — Quantum Random Number Generator (Final IEEE Version)\n")

    # -------------------------------------------------
    # Load IBM token
    # -------------------------------------------------
    token = os.getenv("IBM_API_KEY")
    if token:
        print("✅ Loaded IBM API key from .env")
    else:
        token = input("Enter IBM Quantum API token (or press Enter for simulator): ").strip()

    # -------------------------------------------------
    # Setup provider + backend
    # -------------------------------------------------
    set_provider_as_IBMQ(token if token else None)
    set_backend_interactive()

    # -------------------------------------------------
    # Print backend info
    # -------------------------------------------------
    print("\n========== BACKEND INFORMATION ==========")
    print(f"✅ Backend Selected: {get_backend_name()}")

    ro_backend = get_readout_error_rate()
    if ro_backend is not None:
        print("✅ Readout Error (Hardware Noise):")
        print(f"   Avg Readout Error: {ro_backend['avg_readout_error']}")
        print(f"   Min Readout Error: {ro_backend['min_readout_error']}")
        print(f"   Max Readout Error: {ro_backend['max_readout_error']}")
    else:
        print("⚠️ Readout error not accessible from IBM API for this backend/plan.")
        print("✅ Noise will be measured using calibration circuits in option 5.")

    # -------------------------------------------------
    # Menu
    # -------------------------------------------------
    print("\nChoose output type:")
    print("1. 32-bit integer (show bits)")
    print("2. 64-bit integer (show bits)")
    print("3. Float (0–1) (show bits)")
    print("4. Double (0–1) (show bits)")
    print("5. Hardware Noise & Randomness Analysis (Before vs After Mitigation)")

    choice = input("\nEnter your choice (1–5): ").strip()
    print("\n🎲 Generating quantum output...\n")

    # -------------------------------------------------
    # OUTPUTS
    # -------------------------------------------------
    if choice == "1":
        raw_bits = get_raw_bit_string(64)
        final_bits = get_bit_string(32, True)
        number = int(final_bits, 2)

        print(f"🧩 RAW bits (64):   {raw_bits}")
        print(f"✅ FINAL bits (32): {final_bits}")
        print(f"🔹 32-bit integer:  {number}")

    elif choice == "2":
        raw_bits = get_raw_bit_string(128)
        final_bits = get_bit_string(64, True)
        number = int(final_bits, 2)

        print(f"🧩 RAW bits (128):  {raw_bits}")
        print(f"✅ FINAL bits (64): {final_bits}")
        print(f"🔹 64-bit integer:  {number}")

    elif choice == "3":
        bits = get_bit_string(32, True)
        value = int(bits, 2) / (2**32)

        print(f"✅ FINAL bits (32): {bits}")
        print(f"🔹 Float (0–1):     {value}")

    elif choice == "4":
        bits = get_bit_string(64, True)
        value = int(bits, 2) / (2**64)

        print(f"✅ FINAL bits (64): {bits}")
        print(f"🔹 Double (0–1):    {value}")

    elif choice == "5":
        # ✅ IEEE MODULE-1 FINAL ANALYSIS
        from .noise_bias_analysis import report_metrics
        from .calibration_noise import estimate_bit_flip_probabilities
        from .quantum_rng import _backend

        # ✅ Ask FINAL bits (not raw bits)
        n = int(input("How many FINAL bits? (Example: 10000): ").strip() or "10000")

        # -------------------------------------------------
        # (1) TRUE Hardware Noise Calibration
        # -------------------------------------------------
        print("\n========== HARDWARE CALIBRATION (TRUE NOISE) ==========")
        noise = estimate_bit_flip_probabilities(_backend, shots=8192)

        print(f"Shots used: {noise['shots']}")
        print(f"P(0→1) = {noise['p01']}")
        print(f"P(1→0) = {noise['p10']}")
        print(f"Estimated Readout Error = {noise['readout_error_estimate']}")

        # -------------------------------------------------
        # (2) BEFORE (RAW) bits
        # -------------------------------------------------
        raw_bits = get_raw_bit_string(n)

        # -------------------------------------------------
        # (3) AFTER extractor: fixed length + collect efficiency stats
        # -------------------------------------------------
        final_bits, stats = get_bit_string(n, True, return_stats=True)

        before = report_metrics(raw_bits)
        after = report_metrics(final_bits)

        # -------------------------------------------------
        # (4) Before vs After results (Formatted IEEE Print)
        # -------------------------------------------------
        _print_metrics_block("BEFORE (RAW) METRICS", before)
        _print_metrics_block("AFTER (EXTRACTED / MITIGATION) METRICS", after)

        print("\n========== SUMMARY COMPARISON ==========")
        print(f"Bias BEFORE     : {before['bias']}")
        print(f"Bias AFTER      : {after['bias']}")
        print(f"Entropy BEFORE  : {before['entropy']}")
        print(f"Entropy AFTER   : {after['entropy']}")
        print(f"Freq p BEFORE   : {before.get('freq_p_value')}")
        print(f"Freq p AFTER    : {after.get('freq_p_value')}")
        print(f"Runs p BEFORE   : {before.get('runs_p_value')}")
        print(f"Runs p AFTER    : {after.get('runs_p_value')}")

        # ✅ Save Module-1 data to DB for Fig1 (two-axes)
        save_module1_graph_row(
            backend=get_backend_name(),
            shots=noise["shots"],
            n_final_bits=n,
            before=before,
            after=after
        )

        # -------------------------------------------------
        # (5) Length + extractor efficiency (IEEE IMPORTANT)
        # -------------------------------------------------
        print("\n========== LENGTH / EFFICIENCY ==========")
        print(f"Raw length (for BEFORE)        : {len(raw_bits)}")
        print(f"Extracted length (FINAL bits)  : {len(final_bits)}")

        if stats and stats.get("raw_bits_used") is not None:
            print(f"Raw bits used to generate FINAL: {stats['raw_bits_used']}")
            if stats.get("efficiency") is not None:
                print(f"Von Neumann efficiency         : {stats['efficiency']:.4f}")

        # -------------------------------------------------
        # (6) Sample bits proof
        # -------------------------------------------------
        print("\n🧩 RAW bits (first 256):")
        print(raw_bits[:256])

        print("\n✅ FINAL bits (first 256):")
        print(final_bits[:256])

    else:
        print("❌ Invalid choice. Please enter 1–5.")


if __name__ == "__main__":
    main()
