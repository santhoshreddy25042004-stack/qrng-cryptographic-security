# qrng/quantum_rng.py
"""
Module-1: Quantum RNG Core (FINAL IEEE + IBM Version)
-----------------------------------------------------
✅ Supports:
- IBM Quantum hardware (Runtime)
- AerSimulator fallback

✅ Features:
- Correct sampling using job.memory (NO max(counts))
- Von Neumann extractor for bias reduction
- TRUE extractor mode (variable output length) for IEEE noise analysis
- Fixed-length output mode for crypto/statistics (AES keys, Module-2)

Author: Santhosh (Final IEEE project)
"""

import os
import math
import json
import struct
from datetime import datetime
from dotenv import load_dotenv

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, transpile

# =========================================================
# Load environment variables
# =========================================================
load_dotenv()
IBM_API_KEY = os.getenv("IBM_API_KEY")

VERBOSE = False


def _log(msg: str):
    if VERBOSE:
        print(msg)


# =========================================================
# Globals
# =========================================================
service = None
_backend = None
_circuit = None
_bitCache = ""

DEFAULT_QUBITS = 8  # good balance


# =========================================================
# IBM Provider Setup
# =========================================================
def set_provider_as_IBMQ(token: str | None = None, instance: str | None = None):
    """
    Initialize IBM Quantum Runtime Service if token is provided.
    If token is None -> simulator mode.
    """
    global service

    try:
        if not token:
            raise ValueError("No IBM token. Using simulator fallback.")

        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService(
            channel="ibm_cloud",
            token=token,
            instance=instance
        )
        _log("✅ Connected to IBM Quantum Runtime Service")

    except Exception as e:
        _log(f"⚠️ IBM Quantum init failed: {e}")
        service = None


# =========================================================
# Circuit Creation
# =========================================================
def _create_circuit(n: int):
    global _circuit

    qr = QuantumRegister(n)
    cr = ClassicalRegister(n)
    qc = QuantumCircuit(qr, cr)

    qc.h(qr)
    qc.measure(qr, cr)

    _circuit = qc


# =========================================================
# Backend Setup (Interactive)
# =========================================================
def set_backend_interactive():
    """
    Select IBM backend interactively.
    If IBM not available -> AerSimulator.
    """
    global _backend, service

    # IBM not available -> simulator
    if service is None:
        from qiskit_aer import AerSimulator
        _backend = AerSimulator()
        _create_circuit(DEFAULT_QUBITS)
        print("✅ IBM not available → using AerSimulator")
        return

    try:
        backends = service.backends()
        if not backends:
            raise RuntimeError("No IBM backends found")

        print("\n🔍 Available IBM Quantum Backends:")
        for i, b in enumerate(backends, start=1):
            print(f"{i}. {b.name}")

        choice = input("\n👉 Select backend number (or press Enter for simulator): ").strip()

        if not choice:
            raise RuntimeError("User selected simulator")

        idx = int(choice) - 1
        if idx < 0 or idx >= len(backends):
            raise ValueError("Invalid backend selection")

        _backend = backends[idx]
        print(f"✅ Using IBM backend: {_backend.name}")

    except Exception as e:
        _log(f"⚠️ Backend selection failed: {e}")
        from qiskit_aer import AerSimulator
        _backend = AerSimulator()
        print("✅ Using AerSimulator")

    _create_circuit(DEFAULT_QUBITS)


# =========================================================
# QRNG Sampling (Correct method using memory)
# =========================================================
def _request_bits(num_shots: int):
    """
    Request num_shots samples, each gives DEFAULT_QUBITS bits.
    Uses result.get_memory() to collect all raw samples.
    """
    global _bitCache, _backend, _circuit, service

    if _backend is None or _circuit is None:
        set_backend_interactive()

    backend_name = getattr(_backend, "name", "")

    def _append_memory(mem_list):
        """
        ✅ IMPORTANT:
        Qiskit memory bitstrings may have reversed order depending on backend.
        Normalize by reversing each shot string.
        """
        global _bitCache
        _bitCache += "".join(s[::-1] for s in mem_list)

    # ---------------- IBM hardware backend ----------------
    if service is not None and backend_name and backend_name.startswith("ibm"):
        try:
            compiled = transpile(_circuit, _backend)
            job = _backend.run(compiled, shots=num_shots, memory=True)
            result = job.result()
            mem = result.get_memory()
            _append_memory(mem)
            return
        except Exception as e:
            _log(f"⚠️ IBM run failed: {e} → fallback to simulator")

    # ---------------- Aer simulator fallback ----------------
    from qiskit_aer import AerSimulator
    sim = AerSimulator()
    compiled = transpile(_circuit, sim)
    job = sim.run(compiled, shots=num_shots, memory=True)
    mem = job.result().get_memory()
    _append_memory(mem)


# =========================================================
# Backend Info Helpers
# =========================================================
def get_backend_name():
    global _backend
    return getattr(_backend, "name", "AerSimulator")


def get_readout_error_rate():
    """
    Try to read readout errors from backend properties.
    Returns None if simulator or not available.
    """
    global _backend, service
    try:
        if service is None or _backend is None:
            return None

        backend_name = getattr(_backend, "name", None)
        if not backend_name:
            return None

        ibm_backend = service.backend(backend_name)
        props = ibm_backend.properties()
        if props is None:
            return None

        readout_errors = []
        for q in range(props.num_qubits):
            try:
                readout_errors.append(props.readout_error(q))
            except Exception:
                pass

        if not readout_errors:
            return None

        return {
            "avg_readout_error": sum(readout_errors) / len(readout_errors),
            "min_readout_error": min(readout_errors),
            "max_readout_error": max(readout_errors),
        }

    except Exception:
        return None


# =========================================================
# Von Neumann extractor (bias reduction)
# =========================================================
def von_neumann_extractor(bits: str) -> str:
    """
    00 -> discard
    11 -> discard
    01 -> 0
    10 -> 1
    """
    out = []
    for i in range(0, len(bits) - 1, 2):
        pair = bits[i:i + 2]
        if pair == "01":
            out.append("0")
        elif pair == "10":
            out.append("1")
    return "".join(out)


# =========================================================
# Metrics for paper
# =========================================================
def bit_metrics(bits: str) -> dict:
    if not bits:
        return {"length": 0, "zeros": 0, "ones": 0, "bias": None, "entropy": None}

    zeros = bits.count("0")
    ones = bits.count("1")

    p1 = ones / len(bits)
    p0 = zeros / len(bits)

    bias = abs(p1 - 0.5)

    entropy_val = 0.0
    if p0 > 0:
        entropy_val -= p0 * math.log2(p0)
    if p1 > 0:
        entropy_val -= p1 * math.log2(p1)

    return {
        "length": len(bits),
        "zeros": zeros,
        "ones": ones,
        "p0": p0,
        "p1": p1,
        "bias": bias,
        "entropy": entropy_val
    }


# =========================================================
# Public APIs
# =========================================================
def get_raw_bit_string(n_bits: int) -> str:
    """
    Return exactly n_bits RAW bits from hardware/simulator.
    """
    global _bitCache

    while len(_bitCache) < n_bits:
        needed_shots = max(1, math.ceil((n_bits - len(_bitCache)) / DEFAULT_QUBITS))
        _request_bits(needed_shots)

    raw = _bitCache[:n_bits]
    _bitCache = _bitCache[n_bits:]
    return raw


# =========================================================
# ✅ TRUE extractor output (IEEE accurate)
# =========================================================
def get_extracted_bits_true(raw_n_bits: int) -> tuple[str, str]:
    """
    TRUE extractor output (variable length).

    Returns:
        (raw_bits, extracted_bits)

    Use this in Module-1 option 5 noise/bias analysis.
    """
    raw_bits = get_raw_bit_string(raw_n_bits)
    extracted_bits = von_neumann_extractor(raw_bits)
    return raw_bits, extracted_bits


# =========================================================
# ✅ Fixed length QRNG bits (Module-2 / Module-3)
# =========================================================
def get_bit_string(n_bits: int, use_extractor: bool = True, return_stats: bool = False):
    """
    Returns exactly n_bits.
    - If use_extractor=True -> apply Von Neumann extractor
    - Keeps collecting raw bits until extracted has enough output

    If return_stats=True -> returns (final_bits, stats_dict)
    """
    if not use_extractor:
        final_bits = get_raw_bit_string(n_bits)
        if return_stats:
            return final_bits, {"raw_bits_used": n_bits, "final_bits": n_bits, "efficiency": 1.0}
        return final_bits

    extracted = ""
    raw_used = 0

    # VN extractor efficiency varies. On hardware, typically 20%–50%.
    # Start with a safe estimate.
    est_efficiency = 0.30

    while len(extracted) < n_bits:
        remaining = n_bits - len(extracted)

        # Adaptive raw size request (paper-friendly and faster)
        need_raw = int((remaining / est_efficiency) + DEFAULT_QUBITS * 4)

        raw = get_raw_bit_string(need_raw)
        raw_used += len(raw)

        out = von_neumann_extractor(raw)
        extracted += out

        # Update estimate using observed ratio
        if len(raw) > 0:
            observed = max(0.01, len(out) / len(raw))
            est_efficiency = 0.7 * est_efficiency + 0.3 * observed

    final_bits = extracted[:n_bits]

    if return_stats:
        stats = {
            "raw_bits_used": raw_used,
            "final_bits": n_bits,
            "efficiency": (n_bits / raw_used) if raw_used else None
        }
        return final_bits, stats

    return final_bits


# =========================================================
# Save outputs (optional)
# =========================================================
def save_qrng_outputs(raw_bits: str, final_bits: str, out_dir="qrng_outputs"):
    os.makedirs(out_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_file = os.path.join(out_dir, f"raw_bits_{timestamp}.txt")
    final_file = os.path.join(out_dir, f"final_bits_{timestamp}.txt")
    json_file = os.path.join(out_dir, f"metrics_{timestamp}.json")

    with open(raw_file, "w") as f:
        f.write(raw_bits)

    with open(final_file, "w") as f:
        f.write(final_bits)

    data = {
        "backend": get_backend_name(),
        "qubits": DEFAULT_QUBITS,
        "raw_metrics": bit_metrics(raw_bits),
        "final_metrics": bit_metrics(final_bits),
    }

    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Saved raw bits:   {raw_file}")
    print(f"✅ Saved final bits: {final_file}")
    print(f"✅ Saved metrics:    {json_file}")


# =========================================================
# Random numbers
# =========================================================
def get_random_int32() -> int:
    return int(get_bit_string(32), 2)


def get_random_int64() -> int:
    return int(get_bit_string(64), 2)


def get_random_float(min_val=0.0, max_val=1.0) -> float:
    unpacked = 0x3F800000 | (get_random_int32() >> 9)
    packed = struct.pack("I", unpacked)
    value = struct.unpack("f", packed)[0] - 1.0
    return (max_val - min_val) * value + min_val


def get_random_double(min_val=0.0, max_val=1.0) -> float:
    unpacked = 0x3FF0000000000000 | (get_random_int64() >> 12)
    packed = struct.pack("Q", unpacked)
    value = struct.unpack("d", packed)[0] - 1.0
    return (max_val - min_val) * value + min_val
