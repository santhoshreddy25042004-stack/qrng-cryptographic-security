import sqlite3

DB_FILE = "results.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

print("\n==============================")
print("📊 MODULE-2 DATABASE SUMMARY")
print("==============================")

# -----------------------------
# SUMMARY FROM final_results
# -----------------------------

cur.execute("""
SELECT rng, backend, COUNT(*)
FROM final_results
GROUP BY rng, backend
""")

for rng, backend, count in cur.fetchall():

    print(f"RNG TYPE: {rng:25} | BACKEND: {backend:20} | EXPERIMENTS: {count}")

# -----------------------------
# SUMMARY FROM hybrid_results
# -----------------------------

cur.execute("""
SELECT backend, COUNT(*)
FROM hybrid_results
GROUP BY backend
""")

for backend, count in cur.fetchall():

    print(f"RNG TYPE: {'HYBRID_QRNG_AES':25} | BACKEND: {backend:20} | EXPERIMENTS: {count}")

# ==========================================================
# FUNCTION TO PRINT RESULTS
# ==========================================================

def print_result(row, hybrid=False):

    print("\n====================================================")

    if hybrid:
        print("📌 LATEST RESULTS FOR: HYBRID_QRNG_AES")
    else:
        print(f"📌 LATEST RESULTS FOR: {row[2]}")

    print("====================================================\n")

    if hybrid:
        (
            id_,
            time,
            backend,
            trials,
            bits,
            entropy,
            min_entropy,
            collision,
            bias,
            autocorr,
            zeros,
            ones,
            freq,
            runs,
            apen,
            serial,
            fft,
            cusum,
            matrix,
            complexity,
            pass_rate,
            chi,
            pred,
            gen_time
        ) = row

        rng = "HYBRID_QRNG_AES"

    else:
        (
            id_,
            time,
            rng,
            backend,
            trials,
            bits,
            entropy,
            min_entropy,
            collision,
            bias,
            autocorr,
            zeros,
            ones,
            freq,
            runs,
            apen,
            serial,
            fft,
            cusum,
            matrix,
            complexity,
            pass_rate,
            chi,
            pred,
            gen_time
        ) = row

    print("ID                :", id_)
    print("TIME              :", time)
    print("RNG               :", rng)
    print("BACKEND           :", backend)
    print("TRIALS            :", trials)
    print("BITS PER TRIAL    :", f"{bits:,}")
    print("TOTAL BITS        :", f"{bits*trials:,}")

    print("\n------ RANDOMNESS METRICS ------")
    print("AVG ENTROPY       :", entropy)
    print("AVG MIN ENTROPY   :", min_entropy)
    print("COLLISION ENTROPY :", collision)
    print("BIAS              :", bias)
    print("AUTOCORRELATION   :", autocorr)

    print("\n------ BIT DISTRIBUTION ------")
    print("AVG ZEROS         :", int(zeros))
    print("AVG ONES          :", int(ones))

    print("\n------ NIST TEST RESULTS ------")
    print("FREQUENCY TEST P  :", freq)
    print("RUNS TEST P       :", runs)
    print("APPROX ENT P      :", apen)
    print("SERIAL TEST P     :", serial)
    print("SPECTRAL TEST P   :", fft)
    print("CUSUM TEST P      :", cusum)
    print("MATRIX TEST P     :", matrix)
    print("COMPLEXITY TEST P :", complexity)

    print("\n------ SUMMARY METRICS ------")
    print("NIST PASS RATE    :", pass_rate)
    print("CHI SQUARE P      :", chi)
    print("PREDICTABILITY    :", pred)

    print("\n------ PERFORMANCE ------")
    print("AVG GEN TIME (s)  :", gen_time)

    print("\n------------------------------")


# ==========================================================
# SHOW LATEST FROM final_results
# ==========================================================

cur.execute("""
SELECT *
FROM final_results
ORDER BY id DESC
""")

for row in cur.fetchall():
    print_result(row)

# ==========================================================
# SHOW LATEST FROM hybrid_results
# ==========================================================

cur.execute("""
SELECT *
FROM hybrid_results
ORDER BY id DESC
""")

for row in cur.fetchall():
    print_result(row, hybrid=True)

conn.close()