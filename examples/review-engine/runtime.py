"""
IBE — Phase-1 Runtime v0.1 (engine/runtime.py)  [③ Phase-1 Runtime]
==================================================================
HA: ③ is NOT "wire the 10 layers" — it is running Input -> Cycle -> Output ONCE
with pseudo-data. The Engine is complete; the Runtime fixes WHO BRINGS WHAT, SEES
WHAT, TAKES BACK WHAT. Success is not "the placement was adopted" but "a PACKET
came back". This is the first Runtime Test: not "is the Engine correct" but "can a
human KEEP THINKING using the Engine".

The Runtime returns an OBSERVATION PACKET, not an ANSWER (classic DSS: return
judgment material to the decision-maker; do not decide). It does NOT judge whether
the placement is "correct" — only what it does to lock-in / reversibility / flow /
future alternative possibility, read from HA's declared Decision Context. Final is
HA.

Materializes the three Runtime schemas (Runtime Spec §7): Domain Profile (Phase-1 =
abstract only), Placement Log record, Output Packet. Hypothesis-conditional; real
input / real placement is HA-gated. Idempotent: same input -> same packet (no
wall-clock in the cycle).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from decision_context import DecisionContext, read_world_as_ha, evaluation_directive
from detector import Observation, detect
from placement import Placement, apply_placement, simulate
from audit import audit
from governance import govern, accumulate
from intervention import intervene
from maneuverability import observe


# --- Schema 1: Domain Profile (Runtime Spec §7 #1) ---------------------------
@dataclass(frozen=True)
class DomainProfile:
    """Phase-1 reuses the Engine's abstract archetype/resource/axis sets. Domain
    profiles (childcare / org / civilization) override these later (§7 #1); the
    Engine currently hardcodes abstract, so Phase-1 = abstract only."""
    profile_id: str = "abstract-v0"
    domain_type: str = "abstract"


ABSTRACT_PROFILE = DomainProfile()


# --- Schema 3: Output Packet (Runtime Spec §7 #4) — what HA takes back --------
@dataclass(frozen=True)
class Packet:
    profile_id: str
    declared_context: dict                 # HA's declared protect/increase/avoid
    constraint_change: str                 # the candidate placement label
    detection: Tuple[str, ...]             # W|HA reading (conditioned items)
    placement_audit: str                   # STOP / HOLD / OK + reason
    governance: str                        # recommendation + concentration
    interventions: Tuple[str, ...]         # reopening candidates (境界/余白/媒介)
    fap: str                               # FAP trend (observation only)
    decision_menu: Tuple[str, ...]         # HA's declared options (transparent)


DECISION_MENU = ("採用", "保留", "棄却", "縮退", "分散", "実験")


# --- Schema 2: Placement Log record (Runtime Spec §7 #2) ---------------------
@dataclass(frozen=True)
class LogRecord:
    placement_id: str
    ts: str                                # caller-stamped (deterministic; not wall-clock)
    declared_context: dict
    baseline_label: str
    candidate_label: str
    audit_result: str
    governance: str
    fap: str
    execution_phase: str = "Phase-1-pseudo"


# --- Cycle: Input -> one pass -> Output Packet -------------------------------
def run_cycle(ctx: DecisionContext, baseline: Observation, placement: Placement,
              profile: DomainProfile = ABSTRACT_PROFILE) -> Packet:
    """One Runtime cycle: detect (W|HA) -> placement audit -> governance ->
    intervention -> FAP. Returns an observation Packet, never an answer. Idempotent."""
    after = apply_placement(baseline, placement)

    # Detector, read FROM HA's declared position (W | HA)
    detection = tuple(f"[{it.touches}] ({it.axis}) {it.label}"
                      for it in read_world_as_ha(detect(after), ctx))

    # Placement Audit (No irrecoverable harm > Flow)
    av = audit(simulate(baseline, placement))
    placement_audit = f"{av.decision} — {av.reason}"

    # Governance Audit (cumulative) + Intervention (recovery)
    gov = govern(accumulate(baseline, (placement,)))
    unmit = [r.label for r in gov.risks if r.present and not r.mitigated]
    governance = f"{gov.recommended}" + (f" — concentration: {', '.join(unmit)}" if unmit else " — concentration なし")
    interventions = tuple(f"{iv.label} → {iv.recovery}" for iv in intervene(gov))

    # FAP Observatory (observation only — trend, not a trigger)
    trend = observe(baseline, (placement,))
    fap = f"{trend.direction} (net {trend.net:+.0f})"

    return Packet(
        profile_id=profile.profile_id,
        declared_context={"protect": list(ctx.protect), "increase": list(ctx.increase), "avoid": list(ctx.avoid)},
        constraint_change=placement.label,
        detection=detection,
        placement_audit=placement_audit,
        governance=governance,
        interventions=interventions,
        fap=fap,
        decision_menu=DECISION_MENU,
    )


def to_log_record(p: Packet, placement_id: str, ts: str = "") -> LogRecord:
    return LogRecord(
        placement_id=placement_id, ts=ts, declared_context=p.declared_context,
        baseline_label="", candidate_label=p.constraint_change,
        audit_result=p.placement_audit, governance=p.governance, fap=p.fap)


def render(p: Packet) -> str:
    lines = [f"CDSS Packet (observation, not an answer · profile={p.profile_id} · 最終は HA)",
             f"  Decision Context (HA 宣言): protect={p.declared_context['protect']} "
             f"increase={p.declared_context['increase']} avoid={p.declared_context['avoid']}",
             f"  Candidate Placement: {p.constraint_change}", "",
             "  Detection (W | HA):"]
    lines += [f"    - {d}" for d in p.detection] or ["    - (none)"]
    lines += ["", f"  Audit:        {p.placement_audit}",
              f"  Governance:   {p.governance}"]
    if p.interventions:
        lines.append("  Intervention:")
        lines += [f"    - {iv}" for iv in p.interventions]
    lines += [f"  FAP:          {p.fap}", "",
              f"  → どうしますか: {' / '.join(p.decision_menu)}  (Runtime は判定しない・観測のみ)"]
    return "\n".join(lines)


# --- Worked example: one cycle (HA's example, illustrative) ------------------
def _demo() -> None:
    print("=" * 70)
    print("IBE — Phase-1 Runtime v0.1 (Input -> Cycle -> Output, run once)")
    print("=" * 70)

    # Input (minimal): a declared Decision Context + a candidate placement.
    ctx = DecisionContext(protect=("reversibility",), increase=("flow",), avoid=("lock-in",))

    # Baseline: an org with attention & trust flow stuck.
    baseline = Observation(label="org", resources_stuck=("attention", "trust"))

    # Candidate placement: "新しい対話プロトコルを組織へ導入する". HA describes its
    # effect (the Runtime does not know what it "really" is): this protocol unblocks
    # attention (dialogue raises flow) but CENTRALIZES facilitation (single
    # interpretation authority). Illustrative — HA declares the effect via the
    # placement's closing/reopening/resource edits.
    placement = Placement(
        label="新しい対話プロトコルを組織へ導入する（集約的設計）",
        add_closing=("concentrate_authority_no_recall",),
        unblock_resources=("attention",))

    packet = run_cycle(ctx, baseline, placement)
    print()
    print(render(packet))
    print("\n  success-condition: packet が返ってきた =", packet is not None)
    print("\n" + "=" * 70)
    print("the Runtime returned judgment material; the human keeps thinking. HA decides.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
