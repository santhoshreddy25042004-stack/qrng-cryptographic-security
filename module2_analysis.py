"""
Module-2: Statistical Randomness Analysis (FINAL IEEE + IBM Version)
-------------------------------------------------------------------
✅ Supports QRNG testing on:
   1) IBM REAL hardware  (slow queue)
   2) AerSimulator       (fast)

✅ Tests:
- Shannon Entropy
- Chi-Square
- NIST Frequency (Monobit)
- NIST Runs
- NIST Block Frequency
- NIST Approximate Entropy
- 95% Confidence Intervals (Mean ± CI)

✅ Stores in SQLite DB: testing_results_ieee
✅ Shows runtime performance
"""

import os
import sqlite3
import numpy as np
import math
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from scipy.stats import entropy

# QRNG bits
from qrng import get_bit_string

# ✅ IBM init functions from Module-1 QRNG
from qrng.quantum_rng import (
    set_provider_as_IBMQ,
    set_backend_interactive,
    get_backend_name
)

# NIST Tests
from randomness_testsuite.FrequencyTest import FrequencyTest
from randomness_testsuite.RunTest import RunTest
from randomness_testsuite.ApproximateEntropy import ApproximateEntropy


# ============================================================
# DATABASE SETTINGS
# ============================================================
DB_FILE = "results.db"
TABLE_NAME = "testing_results_ieee"


def db_setup():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            rng_type TEXT,
            backend TEXT,
            trial INTEGER,
            bit_length INTEGER,

            entropy REAL,
            chi_square REAL,
            chi_square_pass INTEGER,

            zeros INTEGER,
            ones INTEGER,

            frequency_p REAL,
            runs_p REAL,
            block_frequency_p REAL,
            approx_entropy_p REAL
        )
    """)

    conn.commit()
    conn.close()


def store_trial_result(
    rng_type: str,
    backend: str,
    trial: int,
    bit_length: int,
    bitstream: str,
    entropy_value: float,
    chi_square_val: float,
    chi_square_pass: bool,
    freq_p: float,
    runs_p: float,
    block_p: float,
    apen_p: float,
):
    zeros = bitstream.count("0")
    ones = bitstream.count("1")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO {TABLE_NAME}
        (timestamp, rng_type, backend, trial, bit_length,
         entropy, chi_square, chi_square_pass,
         zeros, ones,
         frequency_p, runs_p, block_frequency_p, approx_entropy_p)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        rng_type,
        backend,
        trial,
        bit_length,
        entropy_value,
        chi_square_val,
        1 if chi_square_pass else 0,
        zeros,
        ones,
        float(freq_p),
        float(runs_p),
        float(block_p),
        float(apen_p),
    ))

    conn.commit()
    conn.close()


# ============================================================
# RNG SOURCES
# ============================================================
def get_classical_bits(n: int, fixed_seed: bool = False) -> str:
    if fixed_seed:
        random.seed(42)
    else:
        random.seed(time.time())
    return "".join(str(random.randint(0, 1)) for _ in range(n))


# ============================================================
# STATISTICAL FUNCTIONS
# ============================================================
def shannon_entropy(bitstream: str) -> float:
    bits = np.array([int(b) for b in bitstream])
    counts = np.bincount(bits, minlength=2)
    probs = counts / len(bits)
    probs = probs[probs > 0]
    return entropy(probs, base=2)


def chi_square_test(bitstream: str):
    bits = [int(b) for b in bitstream]
    count_0 = bits.count(0)
    count_1 = bits.count(1)

    total = len(bits)
    expected = total / 2

    chi_square = ((count_0 - expected) ** 2) / expected + ((count_1 - expected) ** 2) / expected
    critical_value = 3.841  # df=1 alpha=0.05
    passed = chi_square < critical_value
    return chi_square, passed


def mean_ci_95(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean_val = float(np.mean(values))
    if n == 1:
        return mean_val, 0.0
    std = float(np.std(values, ddof=1))
    ci = 1.96 * (std / math.sqrt(n))
    return mean_val, ci


# ============================================================
# MENU
# ============================================================
def select_mode():
    print("\n==============================")
    print("MODULE-2: Select Testing Mode")
    print("==============================")
    print("1. QRNG using IBM Hardware (REAL BACKEND)  ⚠ slow")
    print("2. QRNG using AerSimulator (FAST)")
    print("3. Classical RNG (Random seed)")
    print("4. Classical RNG (Fixed seed - deterministic)")
    print("5. Compare ALL using IBM QRNG (IBM + classical random + fixed)")  # ✅ UPDATED
    return input("\nEnter choice (1-5): ").strip()


# ============================================================
# TRIAL RUNNER
# ============================================================
def run_trials(rng_type: str, bit_func, backend_label: str, trials=30, bit_length=10000):
    entropy_list, chi_list = [], []
    freq_list, runs_list = [], []
    block_list, apen_list = [], []

    chi_pass = freq_pass = runs_pass = block_pass = apen_pass = 0

    print(f"\n==================== RUNNING: {rng_type.upper()} ====================")
    print(f"Backend: {backend_label}")
    print(f"Trials={trials}, Bits per trial={bit_length}\n")

    start_total = time.time()
    trial_times = []

    for t in range(1, trials + 1):
        start_trial = time.time()

        bitstream = bit_func(bit_length)

        H = shannon_entropy(bitstream)
        entropy_list.append(H)

        chi_val, chi_ok = chi_square_test(bitstream)
        chi_list.append(chi_val)
        if chi_ok:
            chi_pass += 1

        freq_p, freq_ok = FrequencyTest.monobit_test(bitstream)
        freq_list.append(float(freq_p))
        if freq_ok:
            freq_pass += 1

        runs_p, runs_ok = RunTest.run_test(bitstream)
        runs_list.append(float(runs_p))
        if runs_ok:
            runs_pass += 1

        block_p, block_ok = FrequencyTest.block_frequency(bitstream, block_size=128)
        block_list.append(float(block_p))
        if block_ok:
            block_pass += 1

        apen_p, apen_ok = ApproximateEntropy.approximate_entropy_test(bitstream)
        apen_list.append(float(apen_p))
        if apen_ok:
            apen_pass += 1

        store_trial_result(
            rng_type=rng_type,
            backend=backend_label,
            trial=t,
            bit_length=bit_length,
            bitstream=bitstream,
            entropy_value=H,
            chi_square_val=chi_val,
            chi_square_pass=chi_ok,
            freq_p=freq_p,
            runs_p=runs_p,
            block_p=block_p,
            apen_p=apen_p
        )

        elapsed_trial = time.time() - start_trial
        trial_times.append(elapsed_trial)

        print(f"✅ Trial {t}/{trials} stored | Time: {elapsed_trial:.2f} sec")

    # Runtime summary
    total_time = time.time() - start_total
    avg_time = sum(trial_times) / len(trial_times) if trial_times else 0
    min_time = min(trial_times) if trial_times else 0
    max_time = max(trial_times) if trial_times else 0

    print("\n========== RUNTIME PERFORMANCE ==========")
    print(f"Total runtime : {total_time:.2f} sec")
    print(f"Avg / trial   : {avg_time:.2f} sec")
    print(f"Min / trial   : {min_time:.2f} sec")
    print(f"Max / trial   : {max_time:.2f} sec")

    # IEEE summary
    print("\n==================== IEEE FINAL SUMMARY ====================")

    mH, cH = mean_ci_95(entropy_list)
    print(f"Entropy = {mH:.6f} ± {cH:.6f} (95% CI)")

    mC, cC = mean_ci_95(chi_list)
    print(f"Chi-square = {mC:.6f} ± {cC:.6f} (95% CI) | PASS {chi_pass}/{trials}")

    mF, cF = mean_ci_95(freq_list)
    print(f"Frequency p = {mF:.6f} ± {cF:.6f} | PASS {freq_pass}/{trials}")

    mR, cR = mean_ci_95(runs_list)
    print(f"Runs p = {mR:.6f} ± {cR:.6f} | PASS {runs_pass}/{trials}")

    mB, cB = mean_ci_95(block_list)
    print(f"BlockFreq p = {mB:.6f} ± {cB:.6f} | PASS {block_pass}/{trials}")

    mA, cA = mean_ci_95(apen_list)
    print(f"ApproxEntropy p = {mA:.6f} ± {cA:.6f} | PASS {apen_pass}/{trials}")

    print("\n✅ DONE:", rng_type)


# ============================================================
# MAIN
# ============================================================
def main():
    print("\n🔬 MODULE-2: STATISTICAL ANALYSIS (FINAL IEEE VERSION)\n")
    db_setup()

    BIT_LENGTH = 10000
    TRIALS = 30

    choice = select_mode()

    # -------------------------
    # 1) IBM Hardware QRNG
    # -------------------------
    if choice == "1":
        load_dotenv()
        token = os.getenv("IBM_API_KEY")

        print("\n✅ Loading IBM token from .env ...")
        set_provider_as_IBMQ(token if token else None)

        print("\n✅ Select IBM backend now:")
        set_backend_interactive()

        backend_label = get_backend_name()
        print(f"\n✅ Using backend for Module-2: {backend_label}")

        run_trials(
            rng_type="qrng_ibm_hardware",
            bit_func=lambda n: get_bit_string(n),
            backend_label=backend_label,
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

    # -------------------------
    # 2) Simulator QRNG
    # -------------------------
    elif choice == "2":
        run_trials(
            rng_type="qrng_simulator",
            bit_func=lambda n: get_bit_string(n),
            backend_label="AerSimulator",
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

    # -------------------------
    # 3) Classical random seed
    # -------------------------
    elif choice == "3":
        run_trials(
            rng_type="classical_random",
            bit_func=lambda n: get_classical_bits(n, fixed_seed=False),
            backend_label="Python random()",
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

    # -------------------------
    # 4) Classical fixed seed
    # -------------------------
    elif choice == "4":
        run_trials(
            rng_type="classical_fixed_seed",
            bit_func=lambda n: get_classical_bits(n, fixed_seed=True),
            backend_label="Python random(seed=42)",
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

    # -------------------------
    # 5) Compare ALL using IBM QRNG  ✅ FIXED
    # -------------------------
    elif choice == "5":
        # ✅ Load IBM for comparison QRNG
        load_dotenv()
        token = os.getenv("IBM_API_KEY")

        print("\n✅ Loading IBM token from .env ...")
        set_provider_as_IBMQ(token if token else None)

        print("\n✅ Select IBM backend now:")
        set_backend_interactive()

        backend_label = get_backend_name()
        print(f"\n✅ Using backend for Compare ALL: {backend_label}")

        # ✅ QRNG IBM
        run_trials(
            rng_type="qrng_ibm_hardware",
            bit_func=lambda n: get_bit_string(n),
            backend_label=backend_label,
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

        # ✅ Classical random
        run_trials(
            rng_type="classical_random",
            bit_func=lambda n: get_classical_bits(n, fixed_seed=False),
            backend_label="Python random()",
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

        # ✅ Classical fixed seed (deterministic)
        run_trials(
            rng_type="classical_fixed_seed",
            bit_func=lambda n: get_classical_bits(n, fixed_seed=True),
            backend_label="Python random(seed=42)",
            trials=TRIALS,
            bit_length=BIT_LENGTH
        )

    else:
        print("❌ Invalid choice")
        return

    print(f"\n📥 Results saved in DB: {DB_FILE} (Table: {TABLE_NAME})")
    print("✅ MODULE-2 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
