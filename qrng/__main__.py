# qrng/main.py  ✅ FINAL READY VERSION (MODULE-1 GRAPH DATA STORAGE)

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
# DATABASE CONFIG
# =========================================================

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results.db"))
TABLE_M1_GRAPH = "module1_graph_results"


# =========================================================
# CREATE TABLE
# =========================================================

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

        raw_zeros INTEGER,
        raw_ones INTEGER,
        final_zeros INTEGER,
        final_ones INTEGER,

        raw_bias REAL,
        final_bias REAL,

        raw_entropy REAL,
        final_entropy REAL,

        raw_freq_p REAL,
        raw_runs_p REAL,

        final_freq_p REAL,
        final_runs_p REAL,

        efficiency REAL
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# SAVE DATA
# =========================================================

def save_module1_graph_row(backend, shots, n_final_bits, before, after, stats):

    ensure_module1_graph_table()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    efficiency = None
    if stats and stats.get("efficiency") is not None:
        efficiency = stats["efficiency"]

    cur.execute(f"""
    INSERT INTO {TABLE_M1_GRAPH} (

        time, backend, shots, n_final_bits,

        raw_zeros, raw_ones,
        final_zeros, final_ones,

        raw_bias, final_bias,

        raw_entropy, final_entropy,

        raw_freq_p, raw_runs_p,
        final_freq_p, final_runs_p,

        efficiency
    )

    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (

        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        backend,
        shots,
        n_final_bits,

        before["zeros"],
        before["ones"],
        after["zeros"],
        after["ones"],

        before["bias"],
        after["bias"],

        before["entropy"],
        after["entropy"],

        before.get("freq_p_value"),
        before.get("runs_p_value"),
        after.get("freq_p_value"),
        after.get("runs_p_value"),

        efficiency
    ))

    conn.commit()
    conn.close()

    print(f"✅ Module-1 data stored in DB table: {TABLE_M1_GRAPH}")


# =========================================================
# PRINT METRICS
# =========================================================

def print_metrics(title, m):

    print(f"\n========== {title} ==========")

    print(f"Length      : {m['length']}")
    print(f"Zeros       : {m['zeros']}")
    print(f"Ones        : {m['ones']}")
    print(f"P(0)        : {m['p0']}")
    print(f"P(1)        : {m['p1']}")
    print(f"Bias        : {m['bias']}")
    print(f"Entropy     : {m['entropy']}")

    if "freq_p_value" in m:
        print(f"Freq p-value: {m['freq_p_value']}")

    if "runs_p_value" in m:
        print(f"Runs p-value: {m['runs_p_value']}")


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n🔑 Quantum Random Number Generator (Module-1)\n")

    token = os.getenv("IBM_API_KEY")

    if not token:
        token = input("Enter IBM Quantum API key (or press Enter for simulator): ")

    set_provider_as_IBMQ(token if token else None)
    set_backend_interactive()

    print("\n========== BACKEND ==========")
    print("Backend:", get_backend_name())

    ro = get_readout_error_rate()

    if ro:
        print("Avg readout error:", ro["avg_readout_error"])

    print("\nChoose option:")
    print("1. 32-bit integer")
    print("2. 64-bit integer")
    print("3. Float")
    print("4. Double")
    print("5. Noise & Randomness Analysis")

    choice = input("\nEnter choice (1-5): ")

    # -----------------------------------------------------

    if choice == "5":

        from .noise_bias_analysis import report_metrics
        from .calibration_noise import estimate_bit_flip_probabilities
        from .quantum_rng import _backend

        n = int(input("How many FINAL bits? (example 10000): ") or "10000")

        print("\n========== HARDWARE CALIBRATION ==========")

        noise = estimate_bit_flip_probabilities(_backend, shots=8192)

        print("Shots:", noise["shots"])
        print("P(0→1):", noise["p01"])
        print("P(1→0):", noise["p10"])

        # -------------------------------------------------

        raw_bits = get_raw_bit_string(n)

        final_bits, stats = get_bit_string(n, True, return_stats=True)

        before = report_metrics(raw_bits)
        after = report_metrics(final_bits)

        # -------------------------------------------------

        print_metrics("RAW METRICS", before)
        print_metrics("FINAL METRICS", after)

        print("\n========== SUMMARY ==========")

        print("Bias BEFORE :", before["bias"])
        print("Bias AFTER  :", after["bias"])

        print("Entropy BEFORE :", before["entropy"])
        print("Entropy AFTER  :", after["entropy"])

        # -------------------------------------------------

        save_module1_graph_row(
            backend=get_backend_name(),
            shots=noise["shots"],
            n_final_bits=n,
            before=before,
            after=after,
            stats=stats
        )

        # -------------------------------------------------

        print("\n========== EXTRACTOR EFFICIENCY ==========")

        print("Raw bits used :", stats["raw_bits_used"])

        if stats.get("efficiency"):
            print("Efficiency :", stats["efficiency"])

        print("\nRAW bits sample:\n", raw_bits[:256])
        print("\nFINAL bits sample:\n", final_bits[:256])


# =========================================================

if __name__ == "__main__":
    main()