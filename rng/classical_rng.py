# rng/classical_rng.py
import random

def generate_classical_bits(n=10000):
    """
    Generate n random bits using classical PRNG
    """
    return ''.join(str(random.randint(0, 1)) for _ in range(n))
