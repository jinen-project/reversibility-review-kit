"""
IBE — Audit Layer v0 (engine/audit.py)  [Phase 1.5]
===================================================
HA: do NOT wire the pipeline end-to-end yet. An independent AUDIT LAYER is rising.
After a placement, "Flow increased" is not enough — we want "is the future's
range of motion NOT shrinking?". The system's top principle is No irrecoverable
harm, which is ABOVE Flow:

    Flow ↑  but Reversibility ↓↓↓   -> STOP
    Flow →  but Reversibility ↑ / Lock-in ↓   -> acceptable (OK)

So the audit order is priority/veto: Lock-in Audit -> Reversibility Audit -> Flow
Audit (Flow is subordinate), then a Civilizational Audit (long-term lock-in
pressure: single-platform / single-funding / single-authority / single-value
dependence). Once the Audit Layer is solid, any Placement loads on top of it.

NOT a prediction. Operates on the Placement Simulator's three-axis delta
(engine/placement.py). The verdict is a candidate recommendation; the final
decision is HA. Same form for childcare / org / business / institution /
democracy / civilization.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from detector import STAGE
from placement import PlacementAudit, AxisDelta

# Structural single-X dependence (civilizational lock-in) the lock-in archetypes
# express. (single-platform / single-funding are domain instances of the same
# structure — profile extensions, not in the 6 base archetypes.)
CIVILIZATIONAL_LOCKIN = {
    "concentrate_authority_no_recall": "単一解釈権依存 (single-authority)",
    "fix_single_axis": "単一価値観／単一軸依存 (single-value)",
    "remove_margin_exit": "退出不能 (no-exit / 別解が消える)",
}


@dataclass(frozen=True)
class AuditVerdict:
    decision: str                          # "STOP" | "HOLD" | "OK"  (candidate; final is HA)
    reason: str
    lock_in: str                           # per-axis reading
    reversibility: str
    flow: str
    civilizational_flags: Tuple[str, ...]  # structural single-X dependence (introduced)


def _read(ad: AxisDelta) -> str:
    verb = {"recovers room": "可動域を残す", "closes room": "可動域を閉じる", "unchanged": "変化なし"}[ad.direction]
    extra = ""
    if ad.disappeared:
        extra += f"  解消[{', '.join(ad.disappeared)}]"
    if ad.appeared:
        extra += f"  新規[{', '.join(ad.appeared)}]"
    return f"{ad.before}→{ad.after} {verb}{extra}"


def audit(pa: PlacementAudit) -> AuditVerdict:
    """Apply the priority/veto audit — No irrecoverable harm first, ABOVE Flow."""
    # 1. No irrecoverable harm: did the placement INTRODUCE an irreversible (P0) concern?
    new_irreversible = tuple(a for a in pa.reversibility.appeared if STAGE.get(a) == "irreversible")
    lock_closes = pa.lock_in.direction == "closes room"
    rev_closes = pa.reversibility.direction == "closes room"
    any_recovers = any(x.direction == "recovers room"
                       for x in (pa.lock_in, pa.reversibility, pa.flow))

    civ = tuple(CIVILIZATIONAL_LOCKIN[a] for a in pa.lock_in.appeared if a in CIVILIZATIONAL_LOCKIN)

    if new_irreversible:
        decision, reason = "STOP", (
            f"No irrecoverable harm: 不可逆(P0)を新規導入 [{', '.join(new_irreversible)}] "
            "— Flow に依らず止める")
    elif rev_closes or lock_closes:
        which = "Reversibility" if rev_closes else "Lock-in"
        decision, reason = "HOLD", (
            f"{which} が可動域を閉じる — Flow より上位ゆえ保留（Flow↑でも許容しない）")
    elif any_recovers:
        decision, reason = "OK", "Lock-in/Reversibility は閉じず、可動域が回復（候補）"
    else:
        decision, reason = "OK", "可動域に変化なし（候補）"

    return AuditVerdict(decision, reason, _read(pa.lock_in), _read(pa.reversibility),
                        _read(pa.flow), civ)


def render(v: AuditVerdict) -> str:
    lines = [f"Civilizational / Pre-Placement Audit — verdict: {v.decision}  (candidate · 最終は HA)",
             f"  理由: {v.reason}", "",
             "  監査順（No irrecoverable harm が最上位・Flow は従属）:",
             f"    1. Lock-in:       {v.lock_in}",
             f"    2. Reversibility: {v.reversibility}",
             f"    3. Flow:          {v.flow}"]
    if v.civilizational_flags:
        lines += ["", "  Civilizational lock-in（長期・構造的 single-X 依存）:"]
        lines += [f"    ⚠ {f}" for f in v.civilizational_flags]
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    from detector import Observation
    from placement import Placement, simulate

    print("=" * 70)
    print("IBE — Audit Layer v0 (No irrecoverable harm > Flow; Phase 1.5)")
    print("=" * 70)

    baseline = Observation(
        label="site",
        closing_present=("remove_margin_exit",),
        resources_stuck=("relation",))

    # A: leaves a return path + unblocks relation -> OK (room recovers).
    a = Placement(label="A (戻る道を残す)",
                  add_reopening=("unhurried_felt_understood",), unblock_resources=("relation",))
    # B: Flow↑ (unblock relation) BUT concentrates authority -> Lock-in closes -> HOLD (veto over Flow).
    b = Placement(label="B (Flow↑ だが解釈権集中)",
                  add_closing=("concentrate_authority_no_recall",), unblock_resources=("relation",))
    # C: Flow↑ BUT introduces irreversible erase (P0) -> STOP (No irrecoverable harm).
    c = Placement(label="C (Flow↑ だが不可逆消去)",
                  add_closing=("erase_trace_r2_r3",), unblock_resources=("relation",))

    for p in (a, b, c):
        print()
        print(render(audit(simulate(baseline, p))))
    print("\n" + "=" * 70)
    print("No irrecoverable harm vetoes Flow gains; civilizational lock-in flagged.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
