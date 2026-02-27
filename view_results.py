# view_module2_results.py
import sqlite3
import pandas as pd

DB_FILE = "results.db"
TABLE = "testing_results_ieee"


def load_table():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {TABLE}", conn)
    conn.close()
    return df


def print_db_summary(df):
    print("\n==============================")
    print("📊 MODULE-2 DATABASE SUMMARY")
    print("==============================")

    if df.empty:
        print("⚠️ No rows found in Module-2 table.")
        return

    for rng_type in sorted(df["rng_type"].unique()):
        sub = df[df["rng_type"] == rng_type]
        backend = str(sub["backend"].iloc[0]) if "backend" in sub.columns else "Unknown"
        print(f"RNG TYPE: {rng_type:<20} | BACKEND: {backend:<15} | Trials: {len(sub)}")


def print_latest_results(df, rng_type, n=3):
    sub = df[df["rng_type"] == rng_type].sort_values("id", ascending=False).head(n)

    print("\n====================================================")
    print(f"📌 LATEST RESULTS FOR: {rng_type.upper()}")
    print("====================================================\n")

    for _, row in sub.iterrows():
        print(f"ID                : {row.get('id')}")
        print(f"TIME              : {row.get('time')}")
        print(f"RNG TYPE          : {row.get('rng_type')}")
        print(f"BACKEND           : {row.get('backend')}")
        print(f"TRIAL             : {row.get('trial')}")
        print(f"BIT LENGTH        : {row.get('bit_length')}\n")

        print(f"ENTROPY           : {row.get('entropy')}")
        print(f"ZEROS             : {row.get('zeros')}")
        print(f"ONES              : {row.get('ones')}\n")

        print(f"CHI-SQUARE        : {row.get('chi_square')}")
        print(f"CHI PASS          : {bool(row.get('chi_square_pass'))}\n")

        print(f"FREQ P-VALUE      : {row.get('frequency_p')}")
        print(f"RUNS P-VALUE      : {row.get('runs_p')}")
        print(f"BLOCK FREQ P-VALUE: {row.get('block_frequency_p')}")
        print(f"APPROX ENT P-VALUE: {row.get('approx_entropy_p')}")
        print("------------------------------\n")


def main():
    df = load_table()

    print_db_summary(df)

    if df.empty:
        return

    for rng_type in sorted(df["rng_type"].unique()):
        print_latest_results(df, rng_type, n=3)


if __name__ == "__main__":
    main()
