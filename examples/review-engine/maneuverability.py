"""
IBE — Future Alternative Possibility / Maneuverability Observatory v0
(engine/maneuverability.py)  [hold-both naming]
====================================================================
Definition review (HA, survey §22): is the top index "range of motion" or
"Future Alternative Possibility (未来の別解可能性)"? Conclusion (candidate, final
is HA): it is FUTURE ALTERNATIVE POSSIBILITY — "range of motion" is the downstream
symptom (how much you can move WITHIN one world); the real thing is whether you can
still BRANCH TO A DIFFERENT FUTURE (are multiple futures being preserved). HA's
reason is decisive: single-interpretation / single-value / single-resource /
single-platform are bad not only because Flow stops or Reversibility drops, but
because "you can no longer go to a different world". Difference from DMDU/Adaptive
Pathways: DMDU = multiple-futures -> robust choice; this system = multiple-futures
-> are multiple futures still PRESERVED (plurality itself). It is the same thing
IBE handled from the start (L2 Trajectory Bundle = the set of reachable
trajectories; possible-world carving; appears-same != is-same).

So NO layer above Governance is needed — the top index is RECENTERED, not added:
the four range-of-motion properties (exitability / alternative-paths / plurality /
archiveability) are the FOUR WAYS A DIFFERENT FUTURE STAYS REACHABLE. The 10 layers
close. This OBSERVATORY reads a TRAJECTORY (placements over time) and reports the
TREND and WHERE alternative possibility started declining — continuous monitoring,
not per-placement judgement. The level is a comparable proxy (components exposed —
no false precision); the goal it folds in is world-peace / circulation / margin /
No irrecoverable harm. Candidates only; final is HA.

Role lock (survey §23, CDSS_CHARTER_v1.0): FAP is the TOP OBSERVATION INDEX (a
metric) — not the final goal. No irrecoverable harm (P0) is the TOP CONSTRAINT (a
deontic veto, LOCKED), enforced upstream in audit.py (P0 -> STOP) and governance.py
(archive-less erase -> 棄却). They are different KINDS: P0 bounds,
FAP is optimized WITHIN it. FAP is necessary but not sufficient (futures may all
remain yet all be bad — the constitution is the reason to keep alternatives).
boundary / margin / mediation PRODUCE FAP (they are its source, not its parts).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from detector import Observation
from placement import Placement, apply_placement
from governance import govern


@dataclass(frozen=True)
class Maneuverability:
    properties_held: int       # range-of-motion properties held (0..4)
    unmitigated_risks: int     # unmitigated concentration risks
    p0_open: bool              # archive-less erase (irreversible)
    level: float               # higher = more future maneuverability (comparable proxy)


def maneuverability(obs: Observation) -> Maneuverability:
    """One upper index over a configuration, bundling Lock-in / Reversibility /
    Flow via the Governance audit. NOT a truth; a comparable proxy for future
    range-of-motion (its components are exposed)."""
    v = govern(obs)
    held = sum(1 for p in v.properties if p.held)
    unmit = sum(1 for r in v.risks if r.present and not r.mitigated)
    p0 = v.p0_unrecoverable
    level = float(held - unmit - (2 if p0 else 0))
    return Maneuverability(held, unmit, p0, level)


# The four ways a DIFFERENT future stays reachable (= Future Alternative Possibility).
# maneuverability().level is the comparable proxy; these name the alternatives directly.
ALTERNATIVE_DIMENSIONS = {
    "exitability": "別の経路へ抜けられる",
    "alternative-paths": "並走する別解が在る",
    "plurality": "複数の読みが併存する",
    "archiveability": "別の過去へ戻れる（取り返せる）",
}


def alternatives_open(obs: Observation) -> Tuple[str, ...]:
    """Future Alternative Possibility reading: which of the four ways a different
    future stays reachable currently hold (the recentered meaning of the index)."""
    return tuple(p.name for p in govern(obs).properties if p.held)


@dataclass(frozen=True)
class TrendPoint:
    step: int
    label: str
    level: float


@dataclass(frozen=True)
class ManeuverabilityTrend:
    points: Tuple[TrendPoint, ...]
    direction: str             # "rising" | "falling" | "flat"
    first_decline_step: int    # step where maneuverability started declining (-1 if none)
    net: float                 # last - first


def observe(baseline: Observation, placements: Tuple[Placement, ...]) -> ManeuverabilityTrend:
    """Watch the cumulative trajectory: maneuverability level at each step, the
    overall trend, and WHERE it started declining (the early warning HA wants —
    'where does future range-of-motion start being eroded')."""
    points = [TrendPoint(0, baseline.label, maneuverability(baseline).level)]
    obs = baseline
    for i, p in enumerate(placements, 1):
        obs = apply_placement(obs, p)
        points.append(TrendPoint(i, p.label, maneuverability(obs).level))

    first_decline = -1
    for i in range(1, len(points)):
        if points[i].level < points[i - 1].level:
            first_decline = i
            break
    net = points[-1].level - points[0].level
    direction = "rising" if net > 0 else ("falling" if net < 0 else "flat")
    return ManeuverabilityTrend(tuple(points), direction, first_decline, net)


def render(t: ManeuverabilityTrend) -> str:
    lines = ["Maneuverability Observatory — 累積の可動域だけを見る "
             "(個別評価でない・candidate・最終は HA)",
             f"  trend: {t.direction}   net: {t.net:+.0f}", "",
             "  trajectory (step: level):"]
    for p in t.points:
        mark = ("  ← 削られ始める" if (t.direction == "falling" and p.step == t.first_decline_step)
                else ("  ← 一時低下" if p.step == t.first_decline_step else ""))
        lines.append(f"    {p.step}. {p.label:<18} level={p.level:+.0f}{mark}")
    if t.direction == "falling":
        lines.append(f"\n  ⚠ 可動域は falling（step {t.first_decline_step} から削られ始め・net {t.net:+.0f}）（candidate）")
    elif t.first_decline_step != -1:
        lines.append(f"\n  可動域は保持（step {t.first_decline_step} で一時低下→回復・net {t.net:+.0f}）（candidate）")
    else:
        lines.append("\n  可動域は削られていない（candidate）")
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    print("=" * 70)
    print("IBE — Maneuverability Observatory v0 (the top index; watch the trajectory)")
    print("=" * 70)

    baseline = Observation(label="site")

    # Trajectory A: each placement adds a closing, no counters -> maneuverability falls.
    a = (Placement(label="fix-axis", add_closing=("fix_single_axis",)),
         Placement(label="concentrate", add_closing=("concentrate_authority_no_recall",)),
         Placement(label="remove-exit", add_closing=("remove_margin_exit",)))
    print("\n--- Trajectory A (accumulating closures) ---")
    print(render(observe(baseline, a)))

    # Trajectory B: each placement leaves its counter -> maneuverability holds.
    b = (Placement(label="fix+both", add_closing=("fix_single_axis",), add_reopening=("keep_both_views_mediation",)),
         Placement(label="auth+parallel", add_closing=("concentrate_authority_no_recall",), add_reopening=("keep_parallel_paths",)),
         Placement(label="exit+margin", add_closing=("remove_margin_exit",), add_reopening=("unhurried_felt_understood",)))
    print("\n--- Trajectory B (closures with counters left) ---")
    print(render(observe(baseline, b)))
    print("\n" + "=" * 70)
    print("the observatory reads only the trajectory of room-to-move; HA decides.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
