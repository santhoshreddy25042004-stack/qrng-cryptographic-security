"""
MODULE-3 : HYBRID QRNG + AES-CTR DRBG
-------------------------------------
Trials: 20
Bits per trial: 1,000,000
"""

import os
import sqlite3
import numpy as np
import math
import time
from datetime import datetime
from dotenv import load_dotenv
from scipy.stats import chisquare

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from qrng.quantum_rng import (
    set_provider_as_IBMQ,
    set_backend_interactive,
    get_backend_name,
    get_bit_string
)

from randomness_testsuite.FrequencyTest import FrequencyTest
from randomness_testsuite.RunTest import RunTest
from randomness_testsuite.ApproximateEntropy import ApproximateEntropy
from randomness_testsuite.Serial import Serial
from randomness_testsuite.Spectral import SpectralTest
from randomness_testsuite.CumulativeSum import CumulativeSums
from randomness_testsuite.Matrix import Matrix
from randomness_testsuite.Complexity import ComplexityTest


DB_FILE="results.db"
TABLE="hybrid_results"


# =========================================================
# DATABASE
# =========================================================

def db_setup():

    conn=sqlite3.connect(DB_FILE)
    cur=conn.cursor()

    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE}(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    backend TEXT,
    trials INTEGER,
    bits_per_trial INTEGER,
    avg_entropy REAL,
    avg_min_entropy REAL,
    avg_collision_entropy REAL,
    avg_bias REAL,
    avg_autocorrelation REAL,
    avg_zeros REAL,
    avg_ones REAL,
    avg_freq_p REAL,
    avg_runs_p REAL,
    avg_apen_p REAL,
    avg_serial_p REAL,
    avg_fft_p REAL,
    avg_cusum_p REAL,
    avg_matrix_p REAL,
    avg_complexity_p REAL,
    nist_pass_rate REAL,
    chi_square_p REAL,
    predictability REAL,
    avg_generation_time REAL
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HYBRID QRNG + AES CTR DRBG
# =========================================================

def hybrid_qrng_aes_bits(n):

    # Quantum seed (256 bits)
    seed_bits=get_bit_string(256)

    key=int(seed_bits,2).to_bytes(32,"big")

    nonce=os.urandom(16)

    cipher=Cipher(
        algorithms.AES(key),
        modes.CTR(nonce),
        backend=default_backend()
    )

    encryptor=cipher.encryptor()

    data=encryptor.update(os.urandom(n))+encryptor.finalize()

    return "".join(format(b,"08b") for b in data)[:n]


# =========================================================
# ENTROPY
# =========================================================

def shannon_entropy(bits):

    zeros=bits.count("0")
    ones=bits.count("1")
    n=len(bits)

    p0=zeros/n
    p1=ones/n

    H=0

    if p0>0:
        H-=p0*math.log2(p0)

    if p1>0:
        H-=p1*math.log2(p1)

    return H


def nist_min_entropy(bits):

    n=len(bits)

    pmax=max(bits.count("0"),bits.count("1"))/n

    return -math.log2(pmax)


def collision_entropy(bits):

    zeros=bits.count("0")
    ones=bits.count("1")
    n=len(bits)

    p0=zeros/n
    p1=ones/n

    return -math.log2(p0*p0+p1*p1)


# =========================================================
# BIAS + AUTOCORR
# =========================================================

def bit_bias(bits):

    return abs((bits.count("0")/len(bits))-0.5)


def autocorrelation(bits):

    arr=np.array([int(b) for b in bits])

    if np.std(arr)==0:
        return 0

    return float(np.corrcoef(arr[:-1],arr[1:])[0,1])


# =========================================================
# CHI SQUARE
# =========================================================

def chi_square_test(bits):

    zeros=bits.count("0")
    ones=bits.count("1")

    chi,p=chisquare([zeros,ones],[len(bits)/2,len(bits)/2])

    return p


# =========================================================
# PREDICTABILITY
# =========================================================

def predictability_test(bits):

    observe=bits[:1000]
    target=bits[1000:2000]

    correct=0

    for i in range(len(target)):

        if observe[-1]==target[i]:
            correct+=1

        observe+=target[i]

    return correct/len(target)


# =========================================================
# SAFE P VALUE
# =========================================================

def extract_p(x):

    if isinstance(x,(tuple,list)):
        return extract_p(x[0])

    return float(x)


# =========================================================
# RUN HYBRID TRIALS
# =========================================================

def run_trials(backend):

    TRIALS=20
    BITS=1000000

    entropy=[]
    min_e=[]
    coll=[]
    bias=[]
    auto=[]
    pass_rates=[]
    chi_vals=[]
    pred=[]
    times=[]

    freq=[]
    runs=[]
    apen=[]
    serial=[]
    fft=[]
    cusum=[]
    matrix=[]
    complexity=[]

    zeros=[]
    ones=[]

    print("\nRunning HYBRID QRNG + AES\n")

    for t in range(TRIALS):

        start=time.time()

        bits=hybrid_qrng_aes_bits(BITS)

        end=time.time()

        times.append(end-start)

        zeros.append(bits.count("0"))
        ones.append(bits.count("1"))

        H=shannon_entropy(bits)
        entropy.append(H)

        min_e.append(nist_min_entropy(bits))
        coll.append(collision_entropy(bits))

        bias.append(bit_bias(bits))
        auto.append(autocorrelation(bits))

        chi_vals.append(chi_square_test(bits))
        pred.append(predictability_test(bits))

        freq_p=extract_p(FrequencyTest.monobit_test(bits))
        runs_p=extract_p(RunTest.run_test(bits))
        apen_p=extract_p(ApproximateEntropy.approximate_entropy_test(bits))
        serial_p=extract_p(Serial.serial_test(bits))
        fft_p=extract_p(SpectralTest.spectral_test(bits))
        cusum_p=extract_p(CumulativeSums.cumulative_sums_test(bits))
        matrix_p=extract_p(Matrix.binary_matrix_rank_text(bits))
        comp_p=extract_p(ComplexityTest.linear_complexity_test(bits))

        tests=[freq_p,runs_p,apen_p,serial_p,fft_p,cusum_p,matrix_p,comp_p]

        pass_rate=sum(1 for p in tests if p>=0.01)/len(tests)

        pass_rates.append(pass_rate)

        freq.append(freq_p)
        runs.append(runs_p)
        apen.append(apen_p)
        serial.append(serial_p)
        fft.append(fft_p)
        cusum.append(cusum_p)
        matrix.append(matrix_p)
        complexity.append(comp_p)

        print("Trial",t+1,"Entropy:",round(H,10),"PassRate:",round(pass_rate,3))

    conn=sqlite3.connect(DB_FILE)
    cur=conn.cursor()

    cur.execute(f"""
    INSERT INTO {TABLE} VALUES (
    NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
    """,(datetime.now(),backend,TRIALS,BITS,
    np.mean(entropy),np.mean(min_e),np.mean(coll),
    np.mean(bias),np.mean(auto),
    np.mean(zeros),np.mean(ones),
    np.mean(freq),np.mean(runs),np.mean(apen),np.mean(serial),
    np.mean(fft),np.mean(cusum),np.mean(matrix),np.mean(complexity),
    np.mean(pass_rates),np.mean(chi_vals),np.mean(pred),np.mean(times)
    ))

    conn.commit()
    conn.close()


# =========================================================
# MAIN
# =========================================================

def main():

    print("\nMODULE-3 HYBRID QRNG\n")

    db_setup()

    load_dotenv()

    token=os.getenv("IBM_API_KEY")

    set_provider_as_IBMQ(token)

    print("Select IBM backend")

    set_backend_interactive()

    backend=get_backend_name()

    print("Using:",backend)

    run_trials(backend)


if __name__=="__main__":
    main()