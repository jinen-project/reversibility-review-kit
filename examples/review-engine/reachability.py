"""
IBE — Reachability Simulator (first build step · Phase 1 · hypothesis-conditional)
==================================================================================

Principles 0/1/2/3 (top guard · see PRINCIPLE_0.md):
    P0: This simulator does not model reality. It models the space of licensed
        inferences under a specified constraint system (Inference Model).
    P1: The inference is not the world, not the self, not the change itself —
        the Model is not the object either. world != model, HA != model.
    P2: Purpose is decision support under uncertainty, NOT reality identification.
        Output is a Proposal, never a Prediction.
    P3: The objective is not convergence to truth but reduction of decision
        uncertainty under explicit constraints. Crushing Posterior_W vs Posterior_H
        is Disagreement Compression, not truth-search; it always returns to
        adopt / hold / reject.
    True name (converging): Decision Uncertainty Navigation Engine
        (earlier read: Possibility & Constraint Navigation Engine; not Truth, not Prediction).

This is NOT a truth engine and NOT a prediction engine.

It computes how the REACHABLE REGION of an abstract state space changes when a
hypothesis-conditional Constraint Set is edited. It never claims what will happen
in the world; it reports which regions of possibility open, close, or stay
undetermined under a given set of constraints.

Discipline (do not break)
-------------------------
  - center stays empty (中心は空): the engine returns region-deltas; it never
    decides. adopt / hold / reject is Human Final.
  - hypothesis-conditional: constraints are WRITTEN BY A HUMAN, not extracted
    from real traces. No reality claim is made (GATE-1 first step is un-gated
    precisely because of this).
  - fail-closed: WTE/HTE (world-side / self-side trace evidence) are Phase 2+
    input sources and are ABSENT here. Their consistency terms are reported as
    `deferred`, never silently treated as 1.0.
  - Theseus stays (no phenomenon identification): editing a constraint until a
    region opens does NOT mean "that phenomenon occurred"; it means "the region
    where it could not appear got smaller."

Data model (spec embedded — Phase 1)
------------------------------------
State space  : an ordered tuple of named AXES (abstract regions of possibility).
               Each axis carries a reachable width in [0.0, 1.0].
               1.0 = fully reachable · 0.0 = closed off (impossible).
Constraint   : a named rule with a `setting` in [0.0, 1.0] (the knob; lower =
               more restrictive) that imposes that setting as an UPPER BOUND on
               the reachable width of each axis it speaks to (`axes`).
Reachability : R(C) — for each axis, reachable width = min over the settings of
               the constraints that speak to it (intersection of reachable sets).
               An axis touched by no constraint is UNCONSTRAINED (undetermined),
               NOT licensed-open.
Region delta : ΔR = R(C') − R(C) — per-axis change in reachable width.

Layer stack (roadmap — see ARCHITECTURE_v0.2_LAYERS.md; only L0–L1 + Confidence built here)
-------------------------------------------------------------------------------------------
  L0 Constraint Space   <- built       L3 Trace Network      <- HA-gated (real trace)
  L1 Reachable Region   <- built       L4 Observed Evidence  <- HA-gated (real trace)
  L2 Trajectory Bundle  <- next (un-gated, HA-sequenced AFTER this is hardened)
  Forward = generation; reverse (L4->...->L0) = inverse inference, yielding a
  Posterior P(Constraint | Evidence), NOT identification. That is why the output
  is Confidence, not Truth. The `terms` dict below is the seam where Confidence
  later decomposes into Inference / Trajectory / Constraint confidence.

Phase boundary (Phase 2+ deferred · HA-gated)
---------------------------------------------
  WTE and HTE are both `Trace Network → Constraint Extraction → Observed Boundary`
  (same type; world vs self need not be distinguished inside the simulator).
  They attach LATER as constraint-input sources. Do not build them first.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Tuple

# Possibility verdicts (compass: {POSSIBLE | IMPOSSIBLE | UNCONSTRAINED}).
POSSIBLE = "POSSIBLE"
IMPOSSIBLE = "IMPOSSIBLE"
UNCONSTRAINED = "UNCONSTRAINED"


# --- Data model --------------------------------------------------------------

@dataclass(frozen=True)
class Constraint:
    """A hypothesis-conditional rule. `setting` in [0,1] is the upper bound this
    constraint imposes on the reachable width of each axis in `axes`."""
    name: str
    setting: float
    axes: Tuple[str, ...]


@dataclass(frozen=True)
class ConstraintSet:
    """The full state space (`axes`) plus the constraints currently in effect.

    Validated on construction AND after every edit (edits go through
    `dataclasses.replace`, which re-runs `__post_init__`): constraint names are
    unique, every constraint speaks only to axes that exist, and raw settings are
    in [0,1]. Validation RAISES rather than silently dropping (fail-closed)."""
    axes: Tuple[str, ...]
    constraints: Tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        names = [c.name for c in self.constraints]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise ValueError(f"duplicate constraint name(s): {dupes}")
        axis_set = set(self.axes)
        for c in self.constraints:
            unknown = [a for a in c.axes if a not in axis_set]
            if unknown:
                raise ValueError(
                    f"constraint {c.name!r} references axes not in state space: {unknown}")
            if not 0.0 <= c.setting <= 1.0:
                raise ValueError(f"constraint {c.name!r} setting out of [0,1]: {c.setting}")

    def _names(self) -> Dict[str, float]:
        return {c.name: c.setting for c in self.constraints}

    # --- Constraint Editor (C -> C') -----------------------------------------
    # Every edit returns a NEW set; the original is never mutated (append-only
    # in spirit — the caller keeps both C and C' to compute ΔR). Editing a name
    # that does not exist RAISES (fail-closed), never a silent no-op.

    def add(self, c: Constraint) -> "ConstraintSet":
        return replace(self, constraints=self.constraints + (c,))  # __post_init__ re-validates

    def remove(self, name: str) -> "ConstraintSet":
        if name not in self._names():
            raise KeyError(f"no constraint named {name!r}")
        return replace(self, constraints=tuple(c for c in self.constraints if c.name != name))

    def set_value(self, name: str, setting: float) -> "ConstraintSet":
        if name not in self._names():
            raise KeyError(f"no constraint named {name!r}")
        return replace(self, constraints=tuple(
            replace(c, setting=_clamp(setting)) if c.name == name else c
            for c in self.constraints))

    def weaken(self, name: str, by: float) -> "ConstraintSet":
        """Loosen a constraint (raise its cap toward 1.0 — opens regions)."""
        cur = self._names()
        if name not in cur:
            raise KeyError(f"no constraint named {name!r}")
        return self.set_value(name, cur[name] + by)

    def strengthen(self, name: str, by: float) -> "ConstraintSet":
        """Tighten a constraint (lower its cap toward 0.0 — closes regions)."""
        cur = self._names()
        if name not in cur:
            raise KeyError(f"no constraint named {name!r}")
        return self.set_value(name, cur[name] - by)


@dataclass(frozen=True)
class Region:
    widths: Dict[str, float]      # axis -> reachable width [0,1]
    verdict: Dict[str, str]       # axis -> POSSIBLE / IMPOSSIBLE / UNCONSTRAINED


@dataclass(frozen=True)
class RegionDelta:
    delta: Dict[str, float]       # axis -> ΔR (width change)
    before: Dict[str, str]        # axis -> verdict before edit
    after: Dict[str, str]         # axis -> verdict after edit


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


# --- Reachability Simulator (C -> R(C)) --------------------------------------

def reachable_region(cs: ConstraintSet) -> Region:
    """Compute the reachable region as the intersection of constraint caps.

    NOTE this is a reachable-set computation, not a forecast: it answers "which
    states remain reachable under C", never "what state the world will be in".
    """
    widths: Dict[str, float] = {}
    verdict: Dict[str, str] = {}
    for axis in cs.axes:
        caps = [c.setting for c in cs.constraints if axis in c.axes]
        if not caps:
            widths[axis] = 1.0
            verdict[axis] = UNCONSTRAINED  # undetermined — NOT licensed-open
        else:
            w = _clamp(min(caps))
            widths[axis] = round(w, 4)
            verdict[axis] = IMPOSSIBLE if w <= 0.0 else POSSIBLE
    return Region(widths, verdict)


def enclosure_risk(region: Region) -> float:
    """閉域化リスク — mean closed fraction over axes that constraints speak to.

    Computed only over constrained axes; if nothing is constrained we cannot
    claim any enclosure (return 0.0 rather than inventing a value)."""
    constrained = [w for a, w in region.widths.items()
                   if region.verdict[a] != UNCONSTRAINED]
    if not constrained:
        return 0.0
    return round(1.0 - sum(constrained) / len(constrained), 4)


# --- Region Delta (ΔR = R(C') − R(C)) ----------------------------------------

def region_delta(before: ConstraintSet, after: ConstraintSet) -> RegionDelta:
    r0, r1 = reachable_region(before), reachable_region(after)
    delta = {a: round(r1.widths[a] - r0.widths[a], 4) for a in before.axes}
    return RegionDelta(delta, r0.verdict, r1.verdict)


# --- Confidence Layer (Phase-1 honest version) -------------------------------

def confidence_layer(region: Region) -> dict:
    """Of the compass's four confidence terms
    (Evidence × WTE-consistency × HTE-consistency × Discrimination), only the
    DISCRIMINATION term is licensed in Phase 1. The other three require real
    traces / WTE / HTE and are reported as `deferred` (fail-closed — never
    silently 1.0)."""
    n = len(region.verdict)
    determined = sum(1 for v in region.verdict.values() if v != UNCONSTRAINED)
    discrimination = round(determined / n, 4) if n else 0.0
    return {
        "confidence": discrimination,            # the only licensed term in Phase 1
        "terms": {
            "discrimination": discrimination,
            "evidence_strength": "deferred (no real trace)",
            "wte_consistency": "deferred (Phase 2+ input source)",
            "hte_consistency": "deferred (Phase 2+ input source)",
        },
        "coupling": {"reality_coupled": False, "wte_hte_coupled": False},
        "note": "structural / hypothesis-conditional / not a reality claim",
    }


# --- Human Decision presenter (the engine does NOT decide) -------------------

def format_region(region: Region) -> str:
    rows = [f"  {a:<13} {region.widths[a]:.2f}  {region.verdict[a]}" for a in region.widths]
    rows.append(f"  {'enclosure_risk':<13} {enclosure_risk(region):.2f}")
    return "\n".join(rows)


def present(proposal: str, before: ConstraintSet, after: ConstraintSet) -> str:
    """Format a decision-support proposal. Returns text only — adopt / hold /
    reject is Human Final; this function never chooses."""
    rd = region_delta(before, after)
    conf = confidence_layer(reachable_region(after))
    lines = [f"提案:      {proposal}", "期待変化:"]
    for a in before.axes:
        d, v0, v1 = rd.delta[a], rd.before[a], rd.after[a]
        if d == 0.0 and v0 == v1:
            continue
        shift = f"  {v0}→{v1}" if v0 != v1 else ""
        lines.append(f"           {a:<13} {d:+.2f}{shift}")
    risks = [a for a in before.axes if rd.after[a] == IMPOSSIBLE]
    risks += [f"{a}(undetermined)" for a in before.axes if rd.after[a] == UNCONSTRAINED]
    lines.append(f"confidence: {conf['confidence']:.2f}  [{conf['note']}]")
    lines.append(f"主要リスク: {', '.join(risks) if risks else '(none determinate)'}")
    lines.append("→ 採用? 保留? 棄却?   (Human Final — the engine does not decide)")
    return "\n".join(lines)


# --- Abstract profile + worked example (domain-independent core; profiles swap) -

ABSTRACT_AXES: Tuple[str, ...] = ("exploration", "challenge", "dialogue", "emergence")


def _demo() -> None:
    print("=" * 68)
    print("IBE Reachability Simulator — abstract profile (hypothesis-conditional)")
    print("=" * 68)

    # Constraint Editor: a human writes the constraint set C.
    base = ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("enabling_safety", 0.90, ("exploration", "challenge")),
        Constraint("solitude_available", 0.80, ("exploration", "emergence")),
        Constraint("answer_withheld", 0.85, ("dialogue", "emergence")),
    ))

    print("\nR(C) — reachable region under C:")
    print(format_region(reachable_region(base)))

    # Edit 1: strengthen restriction — add strict failure management.
    edit1 = base.add(Constraint("strict_failure_management", 0.20, ("exploration", "challenge")))
    print("\n--- edit 1 -------------------------------------------------------")
    print(present("add strict_failure_management (cap exploration/challenge at 0.20)",
                  base, edit1))

    # Edit 2: drive an axis to IMPOSSIBLE (setting 0.0).
    edit2 = base.add(Constraint("dialogue_forbidden", 0.0, ("dialogue",)))
    print("\n--- edit 2 -------------------------------------------------------")
    print(present("add dialogue_forbidden (cap dialogue at 0.00 -> IMPOSSIBLE)",
                  base, edit2))

    # Edit 3: remove a constraint -> an axis falls back to UNCONSTRAINED.
    edit3 = base.remove("answer_withheld")
    print("\n--- edit 3 -------------------------------------------------------")
    print(present("remove answer_withheld (dialogue loses its only cap -> UNCONSTRAINED)",
                  base, edit3))

    print("\n" + "=" * 68)
    print("center stays empty: the engine reported region-deltas, not a decision.")
    print("=" * 68)


if __name__ == "__main__":
    _demo()
