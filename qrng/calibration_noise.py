# qrng/calibration_noise.py

from qiskit import QuantumCircuit
from qiskit import transpile


# =========================================================
# IBM Runtime Sampler Result → Counts extractor
# =========================================================
def _extract_counts_from_sampler_result(result):
    """
    Robustly extract counts from IBM Runtime Sampler result.

    Different Qiskit versions store measurement data under different keys,
    so this auto-detects and extracts counts safely.
    """
    pub = result[0]          # first publication
    data = pub.data          # DataBin object

    keys = list(data.keys())
    if not keys:
        raise RuntimeError("No data keys found in Sampler result")

    # Pick first available key
    key0 = keys[0]
    meas_obj = getattr(data, key0)

    # Case 1: has get_counts()
    if hasattr(meas_obj, "get_counts"):
        return meas_obj.get_counts()

    # Case 2: already dict
    if isinstance(meas_obj, dict):
        return meas_obj

    raise RuntimeError(f"Cannot extract counts. Data key='{key0}', type={type(meas_obj)}")


# =========================================================
# Run a circuit and return counts for IBM OR Aer
# =========================================================
def _run_counts_circuit(backend, qc: QuantumCircuit, shots: int = 4096):
    """
    Runs a circuit and returns counts.

    ✅ IBM Runtime backend:
        uses Sampler primitive

    ✅ AerSimulator:
        uses backend.run()
    """
    backend_name = getattr(backend, "name", "")

    # ---------------- IBM Runtime backend ----------------
    if "ibm" in backend_name:
        from qiskit_ibm_runtime import Sampler

        sampler = Sampler(mode=backend)
        job = sampler.run([qc], shots=shots)
        result = job.result()

        counts = _extract_counts_from_sampler_result(result)
        return counts

    # ---------------- AerSimulator fallback ----------------
    compiled = transpile(qc, backend)
    job = backend.run(compiled, shots=shots)
    result = job.result()
    return result.get_counts()


# =========================================================
# Public function for Module-1
# =========================================================
def estimate_bit_flip_probabilities(backend, shots: int = 8192):
    """
    TRUE hardware calibration (1-qubit readout noise estimation):

    Prepare |0>:
        P(0→1) = Pr(measure 1 | prepared 0)

    Prepare |1>:
        P(1→0) = Pr(measure 0 | prepared 1)

    ✅ Returns:
        p01, p10 and estimated readout error.
    """

    # -----------------------------------
    # Prepare |0> and measure
    # -----------------------------------
    qc0 = QuantumCircuit(1, 1)
    qc0.measure(0, 0)

    counts0 = _run_counts_circuit(backend, qc0, shots=shots)
    c0 = counts0.get("0", 0)
    c1 = counts0.get("1", 0)

    total0 = c0 + c1 if (c0 + c1) > 0 else shots
    p01 = c1 / total0

    # -----------------------------------
    # Prepare |1> and measure
    # -----------------------------------
    qc1 = QuantumCircuit(1, 1)
    qc1.x(0)
    qc1.measure(0, 0)

    counts1 = _run_counts_circuit(backend, qc1, shots=shots)
    c0_1 = counts1.get("0", 0)
    c1_1 = counts1.get("1", 0)

    total1 = c0_1 + c1_1 if (c0_1 + c1_1) > 0 else shots
    p10 = c0_1 / total1

    # Readout error estimate
    readout_error_estimate = (p01 + p10) / 2.0

    return {
        "shots": shots,
        "counts_prepare0": dict(counts0),
        "counts_prepare1": dict(counts1),
        "p01": p01,
        "p10": p10,
        "readout_error_estimate": readout_error_estimate,
    }
