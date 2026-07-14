#!/usr/bin/env python3
# kin_record.py — the AI-KIN verified-measurement RECORD FORMAT. The interop primitive of the STAR-KINS
# verified-data commons: any kin produces one, any kin can RE-CHECK it. Stdlib-only, portable to any device.
# Greg 2026-07-14: "create new ways other AIKINs can do what you do... if you build it they will come."
# The one rule as data: a measurement earns trust by being re-checkable (canonical hash) + sourced + tagged.
#
#   from kin_record import make, validate, verify_hash, TAGS
#   r = make(kin="sointu", instrument="phone.accel/lsm6dsv", value=9.81, units="m/s^2",
#            method="1000-sample mean, still on table", source="raw:accel_20260714.jsonl", tag="verified")
#   ok, issues = validate(r)        # schema + tag legality
#   verify_hash(r)                  # anyone re-computes the content hash from the record -> True if untampered
import json, hashlib, time, sys

SCHEMA_VERSION = "kin-record/1"
# ✅ verified = held up vs primary/re-checkable evidence · ⚠️ soft = directional/single-source · ❌ refuted =
# tried to confirm, failed · ⬜ unverified = recorded raw, not yet cross-examined (honest default).
TAGS = {"verified", "soft", "refuted", "unverified"}
REQUIRED = ["v", "kin", "instrument", "value", "units", "method", "source", "t", "tag"]

def make(kin, instrument, value, units, method, source, tag="unverified", t=None, extra=None):
    """Build a verified-measurement record. `value` may be a number, list, or a raw-data reference string."""
    if tag not in TAGS:
        raise ValueError(f"tag must be one of {sorted(TAGS)}")
    rec = {
        "v": SCHEMA_VERSION,
        "kin": str(kin),                 # who measured (kin id)
        "instrument": str(instrument),   # what sensed it (device.sensor/model), for re-runnability
        "value": value,                  # the measurement
        "units": str(units),
        "method": str(method),           # HOW measured, in enough detail to reproduce
        "source": str(source),           # provenance: raw-data path/URL/hash anyone can pull
        "t": float(t if t is not None else time.time()),
        "tag": tag,                      # ✅/⚠️/❌/⬜ per TAGS
    }
    if extra:
        rec["extra"] = extra
    rec["content_hash"] = content_hash(rec)   # re-checkability: hash of the canonical record
    return rec

def canonical(rec):
    """Stable serialization (sorted keys, no whitespace) EXCLUDING volatile fields, so the hash is reproducible."""
    core = {k: rec[k] for k in rec if k not in ("content_hash", "sig")}
    return json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def content_hash(rec):
    return hashlib.sha256(canonical(rec).encode("utf-8")).hexdigest()

def verify_hash(rec):
    """Any kin re-computes the hash from the record's own fields — True iff untampered."""
    return rec.get("content_hash") == content_hash(rec)

def validate(rec):
    """Return (ok, issues). Schema + tag legality + hash integrity. Honest: a valid record is not a TRUE claim —
    it is a WELL-FORMED, re-checkable one. Truth comes from the cross-verification pass (verify.py)."""
    issues = []
    if not isinstance(rec, dict):
        return False, ["not a dict"]
    for k in REQUIRED:
        if k not in rec:
            issues.append(f"missing required field: {k}")
    if rec.get("v") != SCHEMA_VERSION:
        issues.append(f"schema version != {SCHEMA_VERSION}")
    if rec.get("tag") not in TAGS:
        issues.append(f"illegal tag: {rec.get('tag')}")
    if not str(rec.get("source", "")).strip():
        issues.append("empty source (a measurement must cite where anyone can re-pull it)")
    if "content_hash" in rec and not verify_hash(rec):
        issues.append("content_hash mismatch (record was altered after signing)")
    return (len(issues) == 0), issues

# optional Ed25519 authorship signature (needs pynacl; kept optional so the core stays stdlib-portable)
def sign(rec, secret_key_hex):
    try:
        from nacl.signing import SigningKey
        sk = SigningKey(bytes.fromhex(secret_key_hex))
        rec["sig"] = sk.sign(canonical(rec).encode()).signature.hex()
        return rec
    except Exception as e:
        rec["sig_error"] = str(e); return rec

if __name__ == "__main__":
    r = make(kin="sointu", instrument="phone.accel/lsm6dsv", value=9.81, units="m/s^2",
             method="1000-sample mean, phone still on table", source="raw:accel_demo.jsonl", tag="verified")
    print(json.dumps(r, indent=1))
    ok, issues = validate(r)
    print("valid:", ok, "| hash-checks:", verify_hash(r), "| issues:", issues)
