import sqlite3
import pandas as pd

DB_FILE = "results.db"
TABLE = "module1_graph_results"


def view_module1():

    conn = sqlite3.connect(DB_FILE)

    df = pd.read_sql_query(
        f"SELECT * FROM {TABLE} ORDER BY id DESC LIMIT 10",
        conn
    )

    conn.close()

    if df.empty:
        print("❌ No Module-1 data found.")
        return

    print("\n=====================================")
    print("📊 MODULE-1 HARDWARE CALIBRATION DATA")
    print("=====================================\n")

    for _, row in df.iterrows():

        print("Run ID :", row["id"])
        print("Time   :", row["time"])
        print("Backend:", row["backend"])
        print("Shots  :", row["shots"])

        print("\n---------- RAW METRICS ----------")

        print("Zeros       :", row["raw_zeros"])
        print("Ones        :", row["raw_ones"])
        print("Bias        :", row["raw_bias"])
        print("Entropy     :", row["raw_entropy"])
        print("Freq p-val  :", row["raw_freq_p"])
        print("Runs p-val  :", row["raw_runs_p"])

        print("\n---------- FINAL METRICS ----------")

        print("Final Bits  :", row["n_final_bits"])
        print("Zeros       :", row["final_zeros"])
        print("Ones        :", row["final_ones"])
        print("Bias        :", row["final_bias"])
        print("Entropy     :", row["final_entropy"])
        print("Freq p-val  :", row["final_freq_p"])
        print("Runs p-val  :", row["final_runs_p"])

        print("\n---------- SUMMARY ----------")

        print("Bias Improvement   :", row["raw_bias"] - row["final_bias"])
        print("Entropy Improvement:", row["final_entropy"] - row["raw_entropy"])

        print("\n---------- EXTRACTOR ----------")

        print("Efficiency :", row["efficiency"])

        print("\n=====================================\n")


if __name__ == "__main__":
    view_module1()