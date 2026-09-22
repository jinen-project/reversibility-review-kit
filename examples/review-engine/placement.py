"""
IBE — Placement Simulator v0 (engine/placement.py)
==================================================
Phase-1 (HA): a PRE-PLACEMENT AUDIT device, NOT a future-prediction simulator and
NOT a Posterior Engine. The central question is not "what is true" but "which
PLACEMENT preserves the future's range of motion".

Given a placement (an intervention on an Observation), it asks:
    Does Lock-in increase or decrease?
    Does Reversibility recover or erode?
    Does Flow recover or stagnate?

This is the IBE `C -> C' -> ΔR` pattern applied to the three Detector axes:
detect(before) vs detect(after the placement), comparing the OPEN LOAD per axis
(candidates whose return-path counter is absent, plus stuck flows). It does NOT
predict the future; it reports the change in the candidate sets, hypothesis-
conditionally. Posterior_W/Posterior_H are not protagonists here — they are the
Detector's internal state.

Same form for childcare / org / business / democracy / civilization. At the
civilizational layer the lock-in candidates read as single-platform / single-
funding / single-value / single-authority dependence. HA's values
(world-peace / resource-circulation / margin / stop) all point one way:
Flow ↑ / Reversibility ↑ / Lock-in ↓.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from detector import Observation, Detection, detect


@dataclass(frozen=True)
class Placement:
    """An intervention applied to an Observation: which closing patterns it
    introduces/removes, which reopening counter-moves it adds/removes, which
    Resource-Layer flows it unblocks/blocks. Hypothesis-conditional."""
    label: str
    add_closing: Tuple[str, ...] = ()
    remove_closing: Tuple[str, ...] = ()
    add_reopening: Tuple[str, ...] = ()
    remove_reopening: Tuple[str, ...] = ()
    unblock_resources: Tuple[str, ...] = ()
    block_resources: Tuple[str, ...] = ()


def _merge(base: Tuple[str, ...], add: Tuple[str, ...], remove: Tuple[str, ...]) -> Tuple[str, ...]:
    out = [x for x in base if x not in remove]
    for x in add:
        if x not in out:
            out.append(x)
    return tuple(out)


def apply_placement(obs: Observation, p: Placement) -> Observation:
    """The Observation after the placement (a new object; obs is not mutated)."""
    return Observation(
        label=f"{obs.label} + {p.label}",
        closing_present=_merge(obs.closing_present, p.add_closing, p.remove_closing),
        reopening_present=_merge(obs.reopening_present, p.add_reopening, p.remove_reopening),
        resources_stuck=_merge(obs.resources_stuck, p.block_resources, p.unblock_resources),
    )


# OPEN LOAD per axis = the unmitigated concern: lock-in / reversibility candidates
# whose return-path counter is ABSENT, plus stuck flows.
def _open(d: Detection):
    lock = {c.archetype for c in d.lockin_candidates if not c.counter_present}
    rev = {c.archetype for c in d.reversibility_candidates if not c.counter_present}
    flow = {f.resource for f in d.flow_candidates}
    return lock, rev, flow


@dataclass(frozen=True)
class AxisDelta:
    axis: str
    before: int
    after: int
    appeared: Tuple[str, ...]      # open concerns the placement INTRODUCED
    disappeared: Tuple[str, ...]   # open concerns the placement RESOLVED
    direction: str                 # "recovers room" | "closes room" | "unchanged"


@dataclass(frozen=True)
class PlacementAudit:
    placement_label: str
    lock_in: AxisDelta
    reversibility: AxisDelta
    flow: AxisDelta
    preserves_room: str            # "yes" | "no" | "mixed"  (all candidate)


def _axis_delta(axis: str, before: set, after: set) -> AxisDelta:
    # for lock-in: more open = worse; for reversibility/flow: more open = worse too
    # (reversibility "open" = a return path still absent; flow "open" = still stuck).
    if len(after) < len(before):
        direction = "recovers room"
    elif len(after) > len(before):
        direction = "closes room"
    else:
        direction = "unchanged"
    return AxisDelta(axis, len(before), len(after),
                     tuple(sorted(after - before)), tuple(sorted(before - after)), direction)


def simulate(baseline: Observation, p: Placement) -> PlacementAudit:
    """Pre-placement audit: detect before, detect after the placement, compare the
    open load per axis. Returns candidates, not a prediction."""
    b_lock, b_rev, b_flow = _open(detect(baseline))
    a_lock, a_rev, a_flow = _open(detect(apply_placement(baseline, p)))
    lock = _axis_delta("lock-in", b_lock, a_lock)
    rev = _axis_delta("reversibility", b_rev, a_rev)
    flow = _axis_delta("flow", b_flow, a_flow)
    closes = any(x.direction == "closes room" for x in (lock, rev, flow))
    recovers = any(x.direction == "recovers room" for x in (lock, rev, flow))
    preserves = "mixed" if (closes and recovers) else ("no" if closes else ("yes" if recovers else "unchanged"))
    return PlacementAudit(p.label, lock, rev, flow, preserves)


def render(audit: PlacementAudit) -> str:
    arrow = {"recovers room": "↓ room↑", "closes room": "↑ room↓", "unchanged": "= "}
    # lock-in load down = room up; reversibility/flow load down = room up
    lines = [f"Pre-placement audit — {audit.placement_label}",
             "(candidates only · hypothesis-conditional · not a prediction; "
             "the question is 'does this placement preserve future range-of-motion?')", ""]
    for ad in (audit.lock_in, audit.reversibility, audit.flow):
        verb = {"recovers room": "可動域を残す", "closes room": "可動域を閉じる", "unchanged": "変化なし"}[ad.direction]
        lines.append(f"  {ad.axis:<14} open {ad.before}→{ad.after}  [{verb}]")
        if ad.disappeared:
            lines.append(f"                 解消: {', '.join(ad.disappeared)}")
        if ad.appeared:
            lines.append(f"                 新規: {', '.join(ad.appeared)}")
    verdict = {"yes": "可動域を残す配置（candidate）", "no": "可動域を閉じる配置（candidate）",
               "mixed": "両義（一部残し・一部閉じ・candidate）", "unchanged": "変化なし"}[audit.preserves_room]
    lines += ["", f"判定: {verdict}  ／ 最終は HA（採用/保留/棄却）"]
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    print("=" * 70)
    print("IBE — Placement Simulator v0 (pre-placement audit; not prediction)")
    print("=" * 70)

    # A baseline placement-site with open concerns: an exit removed (lock-in),
    # traces erased R2->R3 (irreversible/P0, no archive), relation flow stuck.
    baseline = Observation(
        label="site",
        closing_present=("remove_margin_exit", "erase_trace_r2_r3"),
        resources_stuck=("relation",),
    )

    # Placement A: leaves a return path (archive + unhurried margin) and unblocks
    # relation -> should recover room on all three axes.
    a = Placement(
        label="placement-A (戻る道を残す)",
        add_reopening=("archive_instead_of_erase", "unhurried_felt_understood"),
        unblock_resources=("relation",),
    )
    # Placement B: concentrates authority and blocks attention -> closes room.
    b = Placement(
        label="placement-B (集約・遮断)",
        add_closing=("concentrate_authority_no_recall",),
        block_resources=("attention",),
    )

    print()
    print(render(simulate(baseline, a)))
    print()
    print(render(simulate(baseline, b)))
    print("\n" + "=" * 70)
    print("compared two placements by what each does to room-to-move; HA decides.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
