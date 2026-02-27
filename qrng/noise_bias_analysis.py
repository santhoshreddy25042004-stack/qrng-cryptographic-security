# qrng/noise_bias_analysis.py  ✅ FINAL IEEE READY

import math
from math import erfc, sqrt

# =========================================================
# BASIC METRICS (IEEE)
# =========================================================

def compute_bias(bits: str) -> float:
    """
    Bias = |P(1) - 0.5|
    """
    if not bits:
        return 0.0
    ones = bits.count("1")
    p1 = ones / len(bits)
    return abs(p1 - 0.5)


def shannon_entropy(bits: str) -> float:
    """
    Shannon entropy for binary sequence (bits).
    Output is in bits per bit (0..1).
    """
    if not bits:
        return 0.0

    zeros = bits.count("0")
    ones = bits.count("1")

    n = len(bits)
    p0 = zeros / n
    p1 = ones / n

    H = 0.0
    if p0 > 0:
        H -= p0 * math.log2(p0)
    if p1 > 0:
        H -= p1 * math.log2(p1)

    return H


# =========================================================
# NIST BASIC TESTS (for Conference Paper)
# =========================================================

def nist_frequency_monobit_test(bits: str) -> float:
    """
    NIST Frequency (Monobit) Test
    Returns: p-value (0..1)
    Pass if p-value >= 0.01
    """
    n = len(bits)
    if n == 0:
        return 0.0

    # Convert bits -> +1/-1 sum
    s = 0
    for b in bits:
        s += 1 if b == "1" else -1

    sobs = abs(s) / sqrt(n)
    p_value = erfc(sobs / sqrt(2))
    return float(p_value)


def nist_runs_test(bits: str) -> float:
    """
    NIST Runs Test
    Returns: p-value (0..1)
    Pass if p-value >= 0.01
    """
    n = len(bits)
    if n < 2:
        return 0.0

    ones = bits.count("1")
    pi = ones / n

    # Requirement from NIST: pi should not be too far from 0.5
    if abs(pi - 0.5) >= (2.0 / sqrt(n)):
        # test not applicable; sequence is too imbalanced
        return 0.0

    # Count runs
    runs = 1
    for i in range(1, n):
        if bits[i] != bits[i - 1]:
            runs += 1

    numerator = abs(runs - (2 * n * pi * (1 - pi)))
    denominator = 2 * sqrt(2 * n) * pi * (1 - pi)

    p_value = erfc(numerator / denominator) if denominator != 0 else 0.0
    return float(p_value)


# =========================================================
# IEEE REPORT METRICS
# =========================================================

def report_metrics(bits: str) -> dict:
    """
    Return IEEE-ready QRNG metrics for a given bitstream.
    Includes NIST Frequency + Runs test p-values.
    """
    if not bits:
        return {
            "length": 0,
            "zeros": 0,
            "ones": 0,
            "p0": 0.0,
            "p1": 0.0,
            "bias": 0.0,
            "entropy": 0.0,
            "freq_p_value": 0.0,
            "runs_p_value": 0.0,
        }

    zeros = bits.count("0")
    ones = bits.count("1")
    n = len(bits)

    return {
        "length": n,
        "zeros": zeros,
        "ones": ones,
        "p0": zeros / n,
        "p1": ones / n,
        "bias": compute_bias(bits),
        "entropy": shannon_entropy(bits),              # entropy per bit
        "freq_p_value": nist_frequency_monobit_test(bits),
        "runs_p_value": nist_runs_test(bits),
    }


# =========================================================
# BIT-FLIP PROBABILITY (Noise / Calibration)
# =========================================================

def bit_flip_probability(measured_bits: str, reference_bits: str) -> dict:
    """
    Compute Bit-Flip Probability:
      - P(0→1)
      - P(1→0)

    reference_bits : first sequence (ideal/expected)
    measured_bits  : second sequence (actual measured)

    Returns:
      {"p01": ..., "p10": ...}
    """
    n = min(len(measured_bits), len(reference_bits))
    if n == 0:
        return {"p01": 0.0, "p10": 0.0}

    zero_total = 0
    one_total = 0
    flip_01 = 0
    flip_10 = 0

    for i in range(n):
        ref = reference_bits[i]
        mea = measured_bits[i]

        if ref == "0":
            zero_total += 1
            if mea == "1":
                flip_01 += 1

        elif ref == "1":
            one_total += 1
            if mea == "0":
                flip_10 += 1

    p01 = flip_01 / zero_total if zero_total > 0 else 0.0
    p10 = flip_10 / one_total if one_total > 0 else 0.0

    return {"p01": p01, "p10": p10}


def readout_error_estimate(p01: float, p10: float) -> float:
    """
    Simple average estimate of readout error:
    Readout Error ≈ (P(0→1) + P(1→0)) / 2
    """
    return (p01 + p10) / 2.0
