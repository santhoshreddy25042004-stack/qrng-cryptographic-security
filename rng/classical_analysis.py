# rng/classical_analysis.py

from rng.classical_rng import generate_classical_bits

# IMPORT TEST FUNCTIONS FROM MODULE-2
from module2_analysis import (
    shannon_entropy,
    chi_square_test
)

from randomness_testsuite.FrequencyTest import FrequencyTest
from randomness_testsuite.RunTest import RunTest


def main():
    print("\n🔬 MODULE-2 (BASELINE): CLASSICAL RNG STATISTICAL ANALYSIS\n")

    BIT_LENGTH = 10000
    bitstream = generate_classical_bits(BIT_LENGTH)

    print("Classical bitstream generated successfully.")
    print("Sample (first 64 bits):", bitstream[:64], "\n")

    # Shannon Entropy
    print("📊 Shannon Entropy Test")
    H = shannon_entropy(bitstream)
    print(f"Entropy Value: {H:.6f}")
    print("Result:", "PASS\n" if H >= 0.99 else "FAIL\n")

    # Chi-Square
    print("📊 Chi-Square Test")
    chi_val, chi_result = chi_square_test(bitstream)
    print(f"Chi-Square Statistic: {chi_val:.6f}")
    print("Result:", "PASS\n" if chi_result else "FAIL\n")

    # NIST Frequency Test
    print("📊 NIST Frequency (Monobit) Test")
    p_val, result = FrequencyTest.monobit_test(bitstream)
    print(f"P-value: {p_val}")
    print("Result:", "PASS\n" if result else "FAIL\n")

    # NIST Runs Test
    print("📊 NIST Runs Test")
    p_val, result = RunTest.run_test(bitstream)
    print(f"P-value: {p_val}")
    print("Result:", "PASS\n" if result else "FAIL\n")

    print("✅ CLASSICAL RNG ANALYSIS COMPLETED")


if __name__ == "__main__":
    main()
