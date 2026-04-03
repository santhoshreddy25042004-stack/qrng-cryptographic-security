"""
MODULE-2 : AES CTR DRBG TEST
-----------------------------
Runs AES-CTR DRBG only and stores results in existing database
"""

import os
import sqlite3
import numpy as np
import math
import time
from datetime import datetime
from scipy.stats import chisquare

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from randomness_testsuite.FrequencyTest import FrequencyTest
from randomness_testsuite.RunTest import RunTest
from randomness_testsuite.ApproximateEntropy import ApproximateEntropy
from randomness_testsuite.Serial import Serial
from randomness_testsuite.Spectral import SpectralTest
from randomness_testsuite.CumulativeSum import CumulativeSums
from randomness_testsuite.Matrix import Matrix
from randomness_testsuite.Complexity import ComplexityTest


DB_FILE = "results.db"
TABLE = "final_results"


# =========================================================
# AES CTR RNG
# =========================================================

def get_aes_ctr_bits(n):

    key = os.urandom(16)
    nonce = os.urandom(16)

    cipher = Cipher(
        algorithms.AES(key),
        modes.CTR(nonce),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()

    data = encryptor.update(os.urandom(n)) + encryptor.finalize()

    return "".join(format(b,"08b") for b in data)[:n]


# =========================================================
# ENTROPY
# =========================================================

def shannon_entropy(bits):

    zeros = bits.count("0")
    ones = bits.count("1")

    p0 = zeros/len(bits)
    p1 = ones/len(bits)

    H = 0

    if p0>0:
        H -= p0*math.log2(p0)

    if p1>0:
        H -= p1*math.log2(p1)

    return H


def nist_min_entropy(bits):

    pmax = max(bits.count("0"),bits.count("1"))/len(bits)

    return -math.log2(pmax)


def collision_entropy(bits):

    zeros = bits.count("0")
    ones = bits.count("1")

    p0 = zeros/len(bits)
    p1 = ones/len(bits)

    return -math.log2(p0*p0+p1*p1)


# =========================================================
# STATISTICS
# =========================================================

def bit_bias(bits):

    return abs((bits.count("0")/len(bits))-0.5)


def autocorrelation(bits):

    arr = np.array([int(b) for b in bits])

    if np.std(arr)==0:
        return 0

    return float(np.corrcoef(arr[:-1],arr[1:])[0,1])


def chi_square_test(bits):

    zeros = bits.count("0")
    ones = bits.count("1")

    chi,p = chisquare([zeros,ones],[len(bits)/2,len(bits)/2])

    return p


def predictability_test(bits):

    observe = bits[:1000]
    target = bits[1000:2000]

    correct = 0

    for i in range(len(target)):

        if observe[-1] == target[i]:
            correct += 1

        observe += target[i]

    return correct/len(target)


# =========================================================
# SAFE P VALUE
# =========================================================

def extract_p(x):

    if isinstance(x,(tuple,list)):
        return extract_p(x[0])

    return float(x)


# =========================================================
# RUN TRIALS
# =========================================================

def run_trials():

    TRIALS = 20
    BITS = 1000000

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

    print("\nRunning: AES_CTR_DRBG\n")

    for t in range(TRIALS):

        start=time.time()

        bits=get_aes_ctr_bits(BITS)

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


    print("\n==============================")
    print("FINAL AVERAGE RESULTS")
    print("==============================")

    print("Entropy:",round(np.mean(entropy),8))
    print("MinEntropy:",round(np.mean(min_e),8))
    print("CollisionEntropy:",round(np.mean(coll),8))

    print("\nBias:",round(np.mean(bias),8))
    print("Autocorrelation:",format(np.mean(auto),".8f"))

    print("\nZeros:",int(np.mean(zeros)))
    print("Ones :",int(np.mean(ones)))

    print("\nPassRate:",round(np.mean(pass_rates),3))
    print("ChiSquare:",round(np.mean(chi_vals),5))
    print("Predictability:",round(np.mean(pred),5))
    print("GenerationTime:",round(np.mean(times),3),"seconds")

    print("==============================\n")


    conn=sqlite3.connect(DB_FILE)
    cur=conn.cursor()

    cur.execute(f"""
    INSERT INTO {TABLE} VALUES (
    NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
    """,(datetime.now(),"AES_CTR_DRBG","AES-CTR",TRIALS,BITS,
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

if __name__=="__main__":

    run_trials()