import os

import numpy as np

import matplotlib.pyplot as plt

from adjustText import adjust_text



# =====================================================

# ACADEMIC VISUAL STYLE

# =====================================================

plt.style.use('seaborn-v0_8-paper')

plt.rcParams.update({

    "font.family": "serif",

    "font.size": 10,

    "axes.titlesize": 12,

    "axes.labelsize": 10,

    "figure.dpi": 300,

    "savefig.dpi": 300,

    "axes.grid": True,

    "grid.alpha": 0.3

})



OUTPUT_DIR = "final_manuscript_graphs"

os.makedirs(OUTPUT_DIR, exist_ok=True)



# Dataset from your latest March 2026 Logs

algorithms = [

    "Hybrid (Quantum+AES-CTR)", "Quantum QRNG", "AES-CTR_DRBG",

    "Mersenne Twister", "OS_urandom", "CSPRNG (secrets)", "LCG (Control)"

]

nist_pass = [0.9938, 0.9912, 0.9938, 0.9875, 0.9875, 0.9875, 0.2500]

min_entropy = [0.999295, 0.998414, 0.999824, 0.999604, 0.999604, 1.000000, 1.000000]

av_means = [49.92, 49.69, 50.86, 48.12, 50.55, 48.44, 48.98]

bias_vals = [0.000309, 0.000310, 0.000367, 0.000326, 0.000394, 0.000507, 0.000000]

colors = ["#f1c40f", "#16a085", "#34495e", "#95a5a6", "#7f8c8d", "#2c3e50", "#c0392b"]



def add_labels(ax, bars, fmt=".4f"):

    """Adds bold value labels on top of bars."""

    for bar in bars:

        yval = bar.get_height()

        ax.annotate(f'{yval:{fmt}}', xy=(bar.get_x() + bar.get_width() / 2, yval),

                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',

                    fontsize=8, fontweight='bold')



# --- FIGURE 4: COMPARATIVE NIST RADAR ---

labels = ["Frequency", "Runs", "Spectral", "Approx Entropy", "Serial", "Matrix Rank"]

data_map = {

    "Hybrid (Quantum+AES-CTR-DRBG)": [0.596, 0.591, 0.648, 0.602, 0.559, 0.451],

    "Quantum QRNG": [0.512, 0.489, 0.521, 0.495, 0.470, 0.410],

    "AES-CTR_DRBG": [0.450, 0.420, 0.415, 0.390, 0.380, 0.350],

    "Mersenne Twister": [0.320, 0.310, 0.290, 0.280, 0.250, 0.210],

    "OS_urandom": [0.350, 0.340, 0.320, 0.300, 0.280, 0.260],

    "CSPRNG (secrets)": [0.380, 0.370, 0.350, 0.330, 0.310, 0.290],

    "LCG (Control)": [0.001, 0.002, 0.001, 0.001, 0.001, 0.001]

}

angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist() + [0]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

for i, (name, values) in enumerate(data_map.items()):

    v = values + [values[0]]

    ax.plot(angles, v, color=colors[i], linewidth=3 if "Hybrid" in name else 1.2, label=name)

    if "Hybrid" in name: ax.fill(angles, v, color=colors[i], alpha=0.15)

ax.set_thetagrids(np.degrees(angles[:-1]), labels)

ax.legend(loc='upper left', bbox_to_anchor=(1.1, 1.05))

plt.title("Figure 4: Comparative NIST Statistical Profile", pad=30)

plt.savefig(f"{OUTPUT_DIR}/fig4_radar.png", bbox_inches='tight')



# --- FIGURE 5: AVALANCHE STABILITY ---

fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(algorithms, av_means, color=colors, edgecolor='black')

ax.axhline(50, color='red', linestyle='--', label="Ideal (50%)")

ax.set_ylim(0, 65); ax.set_ylabel("Avalanche Mean (%)")

plt.xticks(rotation=25, ha='right'); add_labels(ax, bars, ".2f")

plt.title("Figure 5: AES-256 Avalanche Stability Analysis")

plt.savefig(f"{OUTPUT_DIR}/fig5_avalanche.png", bbox_inches='tight')



# --- FIGURE 6: ENTROPY DENSITY ---

fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(algorithms, min_entropy, color=colors, edgecolor='black')

ax.set_ylim(0.998, 1.0005); ax.set_ylabel("Min Entropy ($H_{min}$)")

plt.xticks(rotation=25, ha='right'); add_labels(ax, bars, ".6f")

plt.title("Figure 6: Security Comparison: Entropy Density")

plt.savefig(f"{OUTPUT_DIR}/fig6_entropy.png", bbox_inches='tight')



# --- FIGURE 7: SECURITY PARETO (THE TOP-LEFT SPOT) ---

fig, ax = plt.subplots(figsize=(8, 6))

texts = []

for i, name in enumerate(algorithms):

    # Plotting Bias (X) vs Entropy (Y)

    ax.scatter(bias_vals[i], min_entropy[i], s=350 if "Hybrid" in name else 150,

               color=colors[i], edgecolors='black', zorder=5)

   

    # Labeling for clear identification

    label_name = "HYBRID (QUANTUM+AES-CTR)" if "Hybrid" in name else name.split(" ")[0]

    texts.append(ax.text(bias_vals[i], min_entropy[i], label_name, fontsize=9, fontweight='bold'))



# Automatic repulsion of labels to prevent overlap

adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black', lw=0.5))



ax.set_xlabel("Average Output Bias (Lower is Better)")

ax.set_ylabel("Entropy Density ($H_{min}$) (Higher is Better)")

ax.set_ylim(0.998, 1.0005)

plt.title("Figure 7: Security Pareto Front (Optimization of Bias vs. Entropy)")

plt.savefig(f"{OUTPUT_DIR}/fig7_security_pareto.png", bbox_inches='tight')



print(f"\n✅ All manuscript-ready graphs saved successfully to: '{OUTPUT_DIR}'")

