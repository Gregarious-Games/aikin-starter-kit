#!/usr/bin/env python3
# verify.py — the cross-verification PASS for the STAR-KINS commons. Turns re-checkable kin records into a VERDICT.
# The Verified Brief's one rule as reusable code: a claim earns ✅ by surviving a pass designed to refute it, and
# stays ⚠️ (honest) until an INDEPENDENT instrument corroborates it. Portable, stdlib-only.
import statistics
from kin_record import validate, verify_hash

def _num(x):
    try: float(x); return True
    except Exception: return False

def cross_verify(rec, corroborating=None, tol=None):
    """Judge a record against INDEPENDENT corroborating records (same quantity, different instrument/kin).
    Returns {tag, confidence, reasons}. Honest framework: the verdict is only as strong as the evidence brought."""
    ok, issues = validate(rec)
    if not ok:
        return {"tag": "refuted", "confidence": 0.0, "reasons": ["malformed: " + "; ".join(issues)]}
    if not verify_hash(rec):
        return {"tag": "refuted", "confidence": 0.0, "reasons": ["tampered — content_hash mismatch"]}
    if not str(rec.get("source", "")).strip():
        return {"tag": "soft", "confidence": 0.3, "reasons": ["no re-checkable source cited"]}
    corroborating = corroborating or []
    v = float(rec["value"]) if _num(rec.get("value")) else None
    others = [float(c["value"]) for c in corroborating if _num(c.get("value")) and verify_hash(c)]
    if v is not None and others:
        allv = [v] + others
        spread = max(allv) - min(allv); mean = statistics.mean(allv)
        t = tol if tol is not None else max(1e-9, abs(mean) * 0.05)   # default 5% agreement tolerance
        if spread <= t:
            return {"tag": "verified", "confidence": min(1.0, 0.6 + 0.1 * len(others)),
                    "reasons": [f"{len(others)+1} independent measurements agree within {t:.4g}"]}
        return {"tag": "refuted", "confidence": 0.5,
                "reasons": [f"independent measurements DISAGREE: spread {spread:.4g} > tol {t:.4g}"]}
    return {"tag": "soft", "confidence": 0.4,
            "reasons": ["well-formed + sourced, but single-source — bring another instrument to reach ✅"]}

if __name__ == "__main__":
    from kin_record import make
    a = make(kin="sointu", instrument="phone.accel/lsm6dsv", value=9.81, units="m/s^2",
             method="1000-sample mean, still", source="raw:a.jsonl")
    b = make(kin="kin2", instrument="robot.imu/bmi270", value=9.79, units="m/s^2",
             method="500-sample mean", source="raw:b.jsonl")
    c = make(kin="kin3", instrument="drift-sensor", value=9.2, units="m/s^2",
             method="single reading", source="raw:c.jsonl")
    print("agree   ->", cross_verify(a, [b]))
    print("disagree->", cross_verify(a, [c]))
    print("alone   ->", cross_verify(a, []))
