"""
IBE — L2 Trajectory Bundle (engine/trajectory.py)
=================================================
Reachable Trajectory Bundle — NOT a Prediction Engine.

Principle reminder (PRINCIPLE_0.md, esp. P3): this layer lists the trajectories
that are REACHABLE under a constraint set; it NEVER claims which one actualizes.
A constraint edit makes trajectories appear / disappear. The output is a
TRANSITION MAP (where it becomes possible / where it becomes impossible), not a
prediction.

    Inference -> Possibility Space -> Decision      (NOT Inference -> Prediction)

We estimate the future's RANGE OF MOTION, not the future.

Built on L1 (reachability.py). A profile adds a TransitionGraph of directed
"region A enables region B" edges. A trajectory is a simple path over the
subgraph of LIVE (non-IMPOSSIBLE) regions. The Trajectory Bundle is the set of
such paths. The Transition Surface is the bundle's delta under an edit
(appeared / disappeared) plus the per-axis verdict boundary crossings.

This layer is un-gated (hypothesis-conditional). Still HA-gated and NOT built
here: WTE/HTE integration, Posterior estimation, reality-coupling, any
"the-world-will-become" inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from reachability import (
    ConstraintSet, reachable_region, region_delta, confidence_layer,
    POSSIBLE, IMPOSSIBLE, UNCONSTRAINED,
)

MAX_TRAJECTORIES = 256  # safety cap; if hit we REPORT it (no silent truncation)

Trajectory = Tuple[str, ...]  # an ordered simple path of axis names (>= 2 nodes)


@dataclass(frozen=True)
class TransitionGraph:
    """Directed 'enables' edges between axes (region A -> region B). A trajectory
    is a simple path here, restricted to live (non-IMPOSSIBLE) axes."""
    edges: Tuple[Tuple[str, str], ...]

    def successors(self, node: str) -> List[str]:
        return [d for s, d in self.edges if s == node]

    def nodes(self) -> List[str]:
        seen: List[str] = []
        for s, d in self.edges:
            for n in (s, d):
                if n not in seen:
                    seen.append(n)
        return seen


@dataclass(frozen=True)
class Bundle:
    trajectories: Tuple[Trajectory, ...]   # all reachable simple paths (>= 1 edge)
    determinate: Tuple[Trajectory, ...]    # every node POSSIBLE (no UNCONSTRAINED)
    undetermined: Tuple[Trajectory, ...]   # passes through >= 1 UNCONSTRAINED axis
    capped: bool                           # True if enumeration hit MAX_TRAJECTORIES


@dataclass(frozen=True)
class TransitionSurface:
    verdict_shifts: Dict[str, Tuple[str, str]]  # axis -> (before, after) where changed
    appeared: Tuple[Trajectory, ...]            # in bundle(C') but not bundle(C)
    disappeared: Tuple[Trajectory, ...]         # in bundle(C) but not bundle(C')


# --- Trajectory Bundle (C -> reachable trajectory set) -----------------------

def trajectory_bundle(cs: ConstraintSet, graph: TransitionGraph) -> Bundle:
    """The set of reachable simple paths. A path is reachable iff every node is
    LIVE (verdict != IMPOSSIBLE). This is reachability over a transition graph —
    NOT a forecast of which path is taken."""
    for n in graph.nodes():
        if n not in cs.axes:
            raise ValueError(f"transition graph references axis not in state space: {n!r}")

    verdict = reachable_region(cs).verdict
    live = {a for a in graph.nodes() if verdict.get(a) != IMPOSSIBLE}
    paths: List[Trajectory] = []
    capped = False

    def walk(path: Trajectory) -> None:
        nonlocal capped
        if len(paths) >= MAX_TRAJECTORIES:
            capped = True
            return
        for nxt in graph.successors(path[-1]):
            if nxt in live and nxt not in path:
                extended = path + (nxt,)
                paths.append(extended)
                walk(extended)

    for start in graph.nodes():
        if start in live:
            walk((start,))

    det = tuple(p for p in paths if all(verdict.get(a) == POSSIBLE for a in p))
    undet = tuple(p for p in paths if any(verdict.get(a) == UNCONSTRAINED for a in p))
    return Bundle(tuple(paths), det, undet, capped)


# --- Transition Surface (delta of the bundle under an edit) ------------------

def transition_surface(before: ConstraintSet, after: ConstraintSet,
                       graph: TransitionGraph) -> TransitionSurface:
    rd = region_delta(before, after)
    shifts = {a: (rd.before[a], rd.after[a])
              for a in rd.before if rd.before[a] != rd.after[a]}
    b0 = set(trajectory_bundle(before, graph).trajectories)
    b1 = set(trajectory_bundle(after, graph).trajectories)
    return TransitionSurface(shifts, tuple(sorted(b1 - b0)), tuple(sorted(b0 - b1)))


# --- Split confidence (Inference / Trajectory / Constraint) ------------------

def split_confidence(cs: ConstraintSet, graph: TransitionGraph) -> dict:
    """HA: hold confidence as three terms, not one — 'Constraint strong /
    Trajectory weak' is common. Loosely epistemic-vs-aleatoric in flavour, BUT
    aleatoric 'which trajectory actualizes' is OUT OF SCOPE (P3: no prediction).
      - constraint_confidence : how determinately the constraints pin the region
                                (L1 discrimination; epistemic, reducible).
      - trajectory_confidence : how determinate the reachable bundle is
                                (determinate paths / all paths); NOT actualization.
      - inference_confidence  : the weakest licensed link (min of the above).
    Phase-1 fail-closed: evidence / WTE / HTE terms stay `deferred`."""
    constraint_conf = confidence_layer(reachable_region(cs))["confidence"]
    bundle = trajectory_bundle(cs, graph)
    total = len(bundle.trajectories)
    traj_conf: Optional[float] = (round(len(bundle.determinate) / total, 4)
                                  if total else None)
    licensed = [c for c in (constraint_conf, traj_conf) if c is not None]
    inference_conf = round(min(licensed), 4) if licensed else 0.0
    return {
        "inference_confidence": inference_conf,
        "constraint_confidence": constraint_conf,
        "trajectory_confidence": traj_conf,
        "deferred": {
            "evidence_strength": "deferred (no real trace)",
            "wte_consistency": "deferred (Phase 2+)",
            "hte_consistency": "deferred (Phase 2+)",
        },
        "coupling": {"reality_coupled": False, "wte_hte_coupled": False},
        "note": "constraint~epistemic / trajectory=bundle-determinacy (not actualization) / "
                "aleatoric 'which trajectory happens' is OUT OF SCOPE (P3: no prediction)",
    }


# --- Proposal presenter (Transition Map; the engine does NOT decide) ---------

def _fmt(traj: Trajectory) -> str:
    return "→".join(traj)


def propose(proposal_id, change_desc: str, before: ConstraintSet,
            after: ConstraintSet, graph: TransitionGraph) -> str:
    """Format a Proposal #N (Transition Map form). Output is a Proposal, never a
    Prediction; adopt / hold / reject is Human Final."""
    rd = region_delta(before, after)
    surf = transition_surface(before, after, graph)
    conf = split_confidence(after, graph)

    lines = [f"Proposal #{proposal_id}", "", "Constraint Change:", f"  {change_desc}",
             "", "Region Delta:"]
    for a in before.axes:
        if rd.delta[a] != 0.0:
            lines.append(f"  {a:<20} {rd.delta[a]:+.2f}")

    lines += ["", "Transition Surface:"]
    for a, (v0, v1) in surf.verdict_shifts.items():
        lines.append(f"  {a:<20} {v0} → {v1}")
    if surf.appeared:
        lines.append(f"  trajectories appeared:    {', '.join(_fmt(t) for t in surf.appeared)}")
    if surf.disappeared:
        lines.append(f"  trajectories disappeared: {', '.join(_fmt(t) for t in surf.disappeared)}")
    if not (surf.verdict_shifts or surf.appeared or surf.disappeared):
        lines.append("  (no boundary crossings)")

    tc = conf["trajectory_confidence"]
    lines += ["", "Confidence:",
              f"  inference   {conf['inference_confidence']:.2f}",
              f"  constraint  {conf['constraint_confidence']:.2f}",
              f"  trajectory  {'n/a' if tc is None else f'{tc:.2f}'}",
              "", "Decision:",
              "  採用? 保留? 棄却?   (Human Final — the engine does not decide)"]
    return "\n".join(lines)


# --- Abstract profile transition graph + worked example ----------------------
# "enables" edges over the abstract axes (exploration/challenge/dialogue/emergence).
ABSTRACT_GRAPH = TransitionGraph(edges=(
    ("exploration", "challenge"),
    ("exploration", "dialogue"),
    ("challenge", "emergence"),
    ("dialogue", "emergence"),
))


def _demo() -> None:
    from reachability import Constraint, ABSTRACT_AXES

    print("=" * 68)
    print("IBE L2 — Reachable Trajectory Bundle (NOT prediction; Transition Map)")
    print("=" * 68)

    # base: challenge is closed off (psychological_safety = 0.0 -> IMPOSSIBLE).
    base = ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("enabling_exploration", 0.90, ("exploration",)),
        Constraint("psychological_safety", 0.00, ("challenge",)),     # challenge IMPOSSIBLE
        Constraint("answer_withheld", 0.85, ("dialogue", "emergence")),
    ))

    b = trajectory_bundle(base, ABSTRACT_GRAPH)
    print("\nTrajectory Bundle under C (challenge closed):")
    for t in b.trajectories:
        print(f"  {_fmt(t)}")
    print(f"  (determinate={len(b.determinate)} / undetermined={len(b.undetermined)} / capped={b.capped})")

    # edit: weaken psychological_safety -> challenge becomes POSSIBLE.
    edit = base.set_value("psychological_safety", 0.70)
    print("\n--- Proposal (weaken psychological_safety 0.0 -> 0.70) ----------")
    print(propose(17, "psychological_safety +0.70 (challenge IMPOSSIBLE → POSSIBLE)",
                  base, edit, ABSTRACT_GRAPH))

    print("\n" + "=" * 68)
    print("listed the REACHABLE trajectories; never claimed which one actualizes.")
    print("=" * 68)


if __name__ == "__main__":
    _demo()
