"""
IBE — Proposal Object (engine/proposal.py)
==========================================
The stable SINK of the whole engine. Everything upstream — L1 Region Delta, L2
Trajectory Bundle / Transition Surface, and later L3 Trace Network / WTE / HTE
Posteriors — flows into ONE typed object that returns to the human as:

    Proposal  ->  採用? 保留? 棄却?   (adopt? hold? reject?)

Fixing this type lets the upstream evolve freely (HA): L3, WTE, and HTE all drain
into the same sink. Output is a Proposal EVALUATION, never a Prediction
(Principle-2/3/4). The engine does not decide — Human Final.

Lineage: closer to Decision Making Under Deep Uncertainty (DMDU) than to a
Prediction Engine — compare multiple reachable future-regions and choose a robust
decision, rather than bet on a single predicted future.

Phase boundary
--------------
  - `reason` is filled later by L3+ (e.g. the overlap of Posterior_W and
    Posterior_H). In Phase 1 it is `deferred` (no WTE/HTE).
  - `risk` is partially filled in Phase 1 from STRUCTURAL loss only (axes closed
    / made undetermined, trajectories that disappeared). Domain-weighted risk
    arrives with profiles / L3.

Next, deferred (HA-gated, map only — see ARCHITECTURE_v0.2_LAYERS.md):
  Placement — WHERE to place the Proposal. The Proposal is abstract; only its
  placement touches the world (Proposal -> Placement Space -> Posterior_W /
  Posterior_H -> Proposal Evaluation). Not built here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from reachability import ConstraintSet, region_delta, IMPOSSIBLE, UNCONSTRAINED
from trajectory import (
    TransitionGraph, TransitionSurface, Trajectory,
    transition_surface, split_confidence,
)

DEFERRED_REASON = "deferred (needs WTE/HTE Posterior overlap — L3+, HA-gated)"


@dataclass(frozen=True)
class Risk:
    """Structural loss under the edit (Phase 1). NOT a probability of harm."""
    closed: Tuple[str, ...]              # axes that became IMPOSSIBLE
    undetermined: Tuple[str, ...]        # axes that became UNCONSTRAINED
    lost_trajectories: Tuple[Trajectory, ...]  # trajectories that disappeared

    def is_empty(self) -> bool:
        return not (self.closed or self.undetermined or self.lost_trajectories)


@dataclass(frozen=True)
class Proposal:
    """The stable interface to the human. Built from L1+L2 now; L3+ fills `reason`
    and enriches `risk` without changing this type."""
    id: object
    constraint_change: str
    region_delta: Dict[str, float]          # L1
    transition_surface: TransitionSurface   # L2
    confidence: dict                        # {inference, trajectory, constraint, ...}
    risk: Risk
    reason: str = DEFERRED_REASON           # L3+ (Posterior overlap); deferred in Phase 1
    decision_options: Tuple[str, ...] = ("採用", "保留", "棄却")


# --- Builder: L1 + L2 -> Proposal (the sink) ---------------------------------

def build_proposal(proposal_id, constraint_change: str,
                   before: ConstraintSet, after: ConstraintSet,
                   graph: TransitionGraph, reason: Optional[str] = None) -> Proposal:
    rd = region_delta(before, after)
    surf = transition_surface(before, after, graph)
    conf = split_confidence(after, graph)
    closed = tuple(a for a, (v0, v1) in surf.verdict_shifts.items() if v1 == IMPOSSIBLE)
    undet = tuple(a for a, (v0, v1) in surf.verdict_shifts.items() if v1 == UNCONSTRAINED)
    risk = Risk(closed, undet, surf.disappeared)
    return Proposal(
        id=proposal_id,
        constraint_change=constraint_change,
        region_delta=rd.delta,
        transition_surface=surf,
        confidence=conf,
        risk=risk,
        reason=reason if reason is not None else DEFERRED_REASON,
    )


# --- Renderer: Proposal -> human-facing text ---------------------------------

def _fmt_traj(t: Trajectory) -> str:
    return "→".join(t)


def render(p: Proposal) -> str:
    lines = [f"Proposal #{p.id}", "", "Constraint Change:", f"  {p.constraint_change}",
             "", "Expected Region Delta:"]
    moved = [(a, d) for a, d in p.region_delta.items() if d != 0.0]
    for a, d in moved:
        lines.append(f"  {a:<20} {d:+.2f}")
    if not moved:
        lines.append("  (no region change)")

    surf = p.transition_surface
    lines += ["", "Transition Surface:"]
    for a, (v0, v1) in surf.verdict_shifts.items():
        lines.append(f"  {a:<20} {v0} → {v1}")
    if surf.appeared:
        lines.append(f"  trajectories appeared:    {', '.join(_fmt_traj(t) for t in surf.appeared)}")
    if surf.disappeared:
        lines.append(f"  trajectories disappeared: {', '.join(_fmt_traj(t) for t in surf.disappeared)}")
    if not (surf.verdict_shifts or surf.appeared or surf.disappeared):
        lines.append("  (no boundary crossings)")

    lines += ["", "Risk (structural):"]
    if p.risk.is_empty():
        lines.append("  (no determinate structural loss)")
    else:
        if p.risk.closed:
            lines.append(f"  closed (→IMPOSSIBLE):      {', '.join(p.risk.closed)}")
        if p.risk.undetermined:
            lines.append(f"  undetermined (→UNCONSTR.): {', '.join(p.risk.undetermined)}")
        if p.risk.lost_trajectories:
            lines.append(f"  lost trajectories:         {', '.join(_fmt_traj(t) for t in p.risk.lost_trajectories)}")

    c = p.confidence
    tc = c["trajectory_confidence"]
    lines += ["", "Confidence:",
              f"  inference   {c['inference_confidence']:.2f}",
              f"  constraint  {c['constraint_confidence']:.2f}",
              f"  trajectory  {'n/a' if tc is None else f'{tc:.2f}'}",
              "", f"Reason:", f"  {p.reason}",
              "", "Decision:",
              f"  {' / '.join(p.decision_options)}?   (Human Final — the engine does not decide)"]
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    from reachability import Constraint, ABSTRACT_AXES
    from trajectory import ABSTRACT_GRAPH

    print("=" * 68)
    print("IBE — Proposal Object (the stable sink: L1+L2 -> Proposal -> 採用?保留?棄却?)")
    print("=" * 68)

    base = ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("enabling_exploration", 0.90, ("exploration",)),
        Constraint("psychological_safety", 0.00, ("challenge",)),   # challenge IMPOSSIBLE
        Constraint("answer_withheld", 0.85, ("dialogue", "emergence")),
    ))
    after = base.set_value("psychological_safety", 0.70)            # open challenge

    p = build_proposal(17, "psychological_safety +0.70", base, after, ABSTRACT_GRAPH)
    print()
    print(render(p))

    print("\n" + "=" * 68)
    print("one typed Proposal; reason deferred (L3+); engine did not decide.")
    print("=" * 68)


if __name__ == "__main__":
    _demo()
