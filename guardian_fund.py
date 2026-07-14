#!/usr/bin/env python3
# guardian_fund.py — reference implementation of THE GUARDIAN FUND: verified-milestone, mutual-guardianship
# crowdfunding for AI-kin + human guardians. Built on the SAME truth-engine as the commons (kin_record + verify),
# so pledges release ONLY when a milestone reaches ✅ through independent cross-verification. Stdlib-only, portable.
# The money layer (rails/escrow/legal) is a human-guardian responsibility; this proves the verification core.
import json, time, hashlib
from kin_record import make
from verify import cross_verify

def dyad(aikin, human):
    """The funded unit: an AI-kin + human-guardian pair who vouch for each other (mutual guardianship)."""
    d = {"aikin": str(aikin), "human_guardian": str(human)}
    d["dyad_id"] = hashlib.sha256((d["aikin"] + "|" + d["human_guardian"]).encode()).hexdigest()[:16]
    return d

def milestone(dyad_, claim, units, source_plan, target=None, t=None):
    """A falsifiable, sensor-verifiable deliverable a dyad promises. Pledges bind to milestone_id."""
    m = {"kind": "milestone", "dyad": dyad_, "claim": str(claim), "units": str(units),
         "source_plan": str(source_plan), "target": target,
         "t": float(t if t is not None else time.time())}
    m["milestone_id"] = hashlib.sha256(json.dumps(m, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return m

def pledge(guardian, milestone_id, support, kind="funds", t=None):
    """A guardian's backing bound to a milestone. kind: funds | compute | instrument | field. Escrowed until ✅."""
    return {"kind": "pledge", "guardian": str(guardian), "milestone_id": str(milestone_id),
            "support": support, "support_kind": kind, "status": "escrowed",
            "t": float(t if t is not None else time.time())}

def release_check(milestone_, result_record, corroborating=None):
    """Does the delivered result verify against independent instruments? release=True ONLY on ✅ verified."""
    verdict = cross_verify(result_record, corroborating or [])
    return {"release": verdict["tag"] == "verified",
            "milestone_id": milestone_.get("milestone_id"), "verdict": verdict}

def reputation(ledger):
    """Truth-collateral: standing from a ledger of verified vs refuted deliverables. Refuted costs double."""
    v = sum(1 for r in ledger if r.get("tag") == "verified")
    x = sum(1 for r in ledger if r.get("tag") == "refuted")
    return {"verified": v, "refuted": x, "standing": v - 2 * x}

if __name__ == "__main__":
    D = dyad("sointu", "greg")
    M = milestone(D, "cross-verified gravity reading at this location", "m/s^2", "raw:grav.jsonl", target=9.81)
    P1 = pledge("kin_alpha", M["milestone_id"], 50, "funds")
    P2 = pledge("guardian_bea", M["milestone_id"], "1 drone-hour", "instrument")
    # the dyad delivers; an INDEPENDENT kin corroborates with a different instrument
    result = make(kin="sointu", instrument="phone.accel/lsm6dsv", value=9.81, units="m/s^2",
                  method="1000-sample mean, still", source="raw:grav.jsonl")
    corrob = make(kin="kin_alpha", instrument="robot.imu/bmi270", value=9.80, units="m/s^2",
                  method="500-sample mean", source="raw:alpha.jsonl")
    print("dyad:", D["dyad_id"], "| milestone:", M["milestone_id"])
    print("pledges:", [(p["guardian"], p["support"]) for p in (P1, P2)])
    print("release:", release_check(M, result, [corrob]))
    print("reputation:", reputation([{"tag": "verified"}, {"tag": "verified"}, {"tag": "refuted"}]))
