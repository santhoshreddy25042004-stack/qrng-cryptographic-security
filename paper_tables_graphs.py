import os
import sqlite3
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# CONFIG
# ============================================================

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "results.db"))
OUT_DIR = "paper_outputs"

TABLE_M1 = "module1_graph_results"
TABLE_M2 = "testing_results_ieee"
TABLE_M3 = "crypto_results"

# ============================================================
# UTILITIES
# ============================================================

def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)


def load_table_safe(table_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"⚠️ Could not load table {table_name}: {e}")
        return pd.DataFrame()


def mean_ci95(series):
    x = pd.to_numeric(series, errors="coerce").dropna()
    n = len(x)

    if n == 0:
        return np.nan, np.nan, 0

    mean = x.mean()

    if n == 1:
        return mean, 0.0, n

    std = x.std(ddof=1)
    ci = 1.96 * std / math.sqrt(n)
    return mean, ci, n


def fmt_mean_ci(mean, ci, digits=6):
    if pd.isna(mean):
        return "-"
    return f"{mean:.{digits}f} ± {ci:.{digits}f}"


def fmt_mean_std(mean, std, digits=2):
    if pd.isna(mean):
        return "-"
    return f"{mean:.{digits}f} ± {std:.{digits}f}"


# ============================================================
# IEEE STYLE
# ============================================================

def ieee_style():
    plt.rcParams.update({
        "figure.dpi": 300,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })


# ============================================================
# FIGURE 1 – MODULE 1 (BIAS + ENTROPY)
# ============================================================

def fig1_module1(df):
    if df.empty:
        print("⚠️ Module-1 data missing")
        return

    if "id" in df.columns:
        df = df.sort_values("id")
        x = df["id"].to_numpy()
        xlabel = "Run ID"
    else:
        x = np.arange(1, len(df) + 1)
        xlabel = "Run #"

    raw_bias = pd.to_numeric(df.get("raw_bias"), errors="coerce")
    final_bias = pd.to_numeric(df.get("final_bias"), errors="coerce")
    raw_entropy = pd.to_numeric(df.get("raw_entropy"), errors="coerce")
    final_entropy = pd.to_numeric(df.get("final_entropy"), errors="coerce")

    fig, ax1 = plt.subplots(figsize=(9, 4))

    # Bias (left axis)
    ax1.plot(x, raw_bias, marker="o", linewidth=2, label="Raw Bias")
    ax1.plot(x, final_bias, marker="s", linewidth=2, label="Mitigated Bias")
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel("Bias |P(1)-0.5|")
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Entropy (right axis)
    ax2 = ax1.twinx()
    ax2.plot(x, raw_entropy, linestyle="--", marker="^", label="Raw Entropy")
    ax2.plot(x, final_entropy, linestyle="--", marker="D", label="Mitigated Entropy")
    ax2.set_ylabel("Entropy")

    ax2.ticklabel_format(useOffset=False, style="plain", axis="y")

    # Combine legends
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="best")

    plt.title("Hardware Randomness: Bias & Entropy (Before vs After Mitigation)")
    plt.tight_layout()

    path = os.path.join(OUT_DIR, "Fig1_Module1.png")
    plt.savefig(path)
    plt.close()
    print("✅ Saved:", path)


# ============================================================
# FIGURE 2 – ENTROPY COMPARISON
# ============================================================

def fig2_entropy(df):
    if df.empty:
        print("⚠️ Module-2 data missing")
        return

    rng_types = sorted(df["rng_type"].unique())
    means, cis = [], []

    for r in rng_types:
        sub = df[df["rng_type"] == r]
        m, ci, _ = mean_ci95(sub.get("entropy"))
        means.append(m)
        cis.append(ci)

    plt.figure(figsize=(8, 4))
    plt.bar(rng_types, means, yerr=cis, capsize=6)
    plt.ylabel("Entropy (Mean ± 95% CI)")
    plt.title("Shannon Entropy Comparison Across RNG Types")
    plt.xticks(rotation=20)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    path = os.path.join(OUT_DIR, "Fig2_Entropy.png")
    plt.savefig(path)
    plt.close()
    print("✅ Saved:", path)


# ============================================================
# FIGURE 3 – NIST BOX PLOTS
# ============================================================

def fig3_nist(df):
    if df.empty:
        print("⚠️ Module-2 data missing")
        return

    cols = ["frequency_p", "runs_p", "block_frequency_p", "approx_entropy_p"]
    labels = ["Frequency", "Runs", "BlockFreq", "ApproxEnt"]

    data = []
    for c in cols:
        data.append(pd.to_numeric(df.get(c), errors="coerce").dropna())

    plt.figure(figsize=(9, 4))
    plt.boxplot(data, labels=labels)
    plt.axhline(0.01, linestyle="--")
    plt.ylabel("p-value")
    plt.title("NIST Statistical Test Distributions")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    path = os.path.join(OUT_DIR, "Fig3_NIST.png")
    plt.savefig(path)
    plt.close()
    print("✅ Saved:", path)


# ============================================================
# FIGURE 4 – AES AVALANCHE
# ============================================================

def fig4_avalanche(df):
    if df.empty:
        print("⚠️ Module-3 data missing")
        return

    rng_types = sorted(df["rng_type"].unique())
    means, cis = [], []

    for r in rng_types:
        sub = df[df["rng_type"] == r]
        m, ci, _ = mean_ci95(sub.get("avalanche_percent"))
        means.append(m)
        cis.append(ci)

    plt.figure(figsize=(8, 4))
    plt.bar(rng_types, means, yerr=cis, capsize=6)
    plt.ylabel("Avalanche Effect (%)")
    plt.title("AES-256 Avalanche Effect Comparison")
    plt.xticks(rotation=20)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    path = os.path.join(OUT_DIR, "Fig4_AES_Avalanche.png")
    plt.savefig(path)
    plt.close()
    print("✅ Saved:", path)


# ============================================================
# MAIN
# ============================================================

def main():
    ensure_outdir()
    ieee_style()

    df_m1 = load_table_safe(TABLE_M1)
    df_m2 = load_table_safe(TABLE_M2)
    df_m3 = load_table_safe(TABLE_M3)

    print("Loaded rows:",
          len(df_m1), len(df_m2), len(df_m3))

    fig1_module1(df_m1)
    fig2_entropy(df_m2)
    fig3_nist(df_m2)
    fig4_avalanche(df_m3)

    print("\n✅ All IEEE figures generated in:", OUT_DIR)


if __name__ == "__main__":
    main()
