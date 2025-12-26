"""
Module-2: Statistical Analysis of Quantum Random Numbers
-------------------------------------------------------
Tests implemented:
1. Shannon Entropy
2. NIST SP 800-22 Frequency Test (Monobit)
3. NIST SP 800-22 Runs Test

Input:
- Quantum random bitstream generated using Module-1 QRNG

Output:
- Entropy value
- NIST test p-values (PASS / FAIL)
"""

# -------------------------------------------------------
# Imports
# -------------------------------------------------------

# QRNG from Module-1
from qrng import set_backend
from qrng import get_bit_string

# NIST Tests
from randomness_testsuite.FrequencyTest import FrequencyTest
from randomness_testsuite.RunTest import RunTest

# Entropy calculation
import numpy as np
from scipy.stats import entropy


# -------------------------------------------------------
# Shannon Entropy Function
# -------------------------------------------------------
def shannon_entropy(bitstream: str) -> float:
    """
    Calculate Shannon entropy for a binary bitstream.
    Ideal entropy for true randomness ≈ 1.0
    """
    bits = np.array([int(b) for b in bitstream])
    counts = np.bincount(bits, minlength=2)
    probabilities = counts / len(bits)
    probabilities = probabilities[probabilities > 0]
    return entropy(probabilities, base=2)
# -------------------------------------------------------
# Chi-Square Test (Manual – no scipy dependency)
# -------------------------------------------------------
def chi_square_test(bitstream: str):
    """
    Perform Chi-Square test for uniformity of bits.
    """
    bits = [int(b) for b in bitstream]

    count_0 = bits.count(0)
    count_1 = bits.count(1)

    total = len(bits)
    expected = total / 2

    chi_square = ((count_0 - expected) ** 2) / expected + \
                 ((count_1 - expected) ** 2) / expected

    # Critical value for df=1 at α=0.05
    critical_value = 3.841

    result = chi_square < critical_value

    return chi_square, result



# -------------------------------------------------------
# Main Analysis
# -------------------------------------------------------
def main():
    print("\n🔬 MODULE-2: STATISTICAL ANALYSIS OF QRNG\n")

    # ---------------------------------------------------
    # Generate Quantum Random Bitstream
    # ---------------------------------------------------
    BIT_LENGTH = 10000
    print(f"Generating {BIT_LENGTH} quantum random bits...\n")

    bitstream = get_bit_string(BIT_LENGTH)

    print("Bitstream generated successfully.")
    print("Sample (first 64 bits):", bitstream[:64], "\n")

    # ---------------------------------------------------
    # Shannon Entropy Test
    # ---------------------------------------------------
    print("📊 Shannon Entropy Test")
    H = shannon_entropy(bitstream)
    print(f"Entropy Value: {H:.6f}")

    if H >= 0.99:
        print("Result: PASS (High entropy)\n")
    else:
        print("Result: FAIL (Low entropy)\n")

    # ---------------------------------------------------
    # Chi-Square Test
    # ---------------------------------------------------
    print("📊 Chi-Square Test")
    chi_square_stat, chi_square_result = chi_square_test(bitstream)
    print(f"Chi-Square Statistic: {chi_square_stat:.6f}")
    if chi_square_result:
        print("Result: PASS (Uniform distribution)\n")
    else:
        print("Result: FAIL (Non-uniform distribution)\n")

    # ---------------------------------------------------
    # NIST Frequency (Monobit) Test
    # ---------------------------------------------------
    print("📊 NIST Frequency (Monobit) Test")
    freq_p_value, freq_result = FrequencyTest.monobit_test(bitstream)

    print(f"P-value: {freq_p_value}")
    if freq_result:
        print("Result: PASS\n")
    else:
        print("Result: FAIL\n")

    # ---------------------------------------------------
    # NIST Runs Test
    # ---------------------------------------------------
    print("📊 NIST Runs Test")
    runs_p_value, runs_result = RunTest.run_test(bitstream)

    print(f"P-value: {runs_p_value}")
    if runs_result:
        print("Result: PASS\n")
    else:
        print("Result: FAIL\n")

    print("✅ MODULE-2 ANALYSIS COMPLETED SUCCESSFULLY")


# -------------------------------------------------------
# Entry Point
# -------------------------------------------------------
if __name__ == "__main__":
    main()

