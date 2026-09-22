"""
IBE — Governance Layer v0 (engine/governance.py)
================================================
HA: this is no longer about wiring end-to-end. A layer ABOVE the Placement Audit
is rising: GOVERNANCE. Placement Audit is LOCAL ("is THIS placement dangerous?");
but at the civilizational layer the real danger is CUMULATIVE lock-in — A passes,
B passes, C passes, yet A+B+C+D together ossify into single-interpretation /
no-exit / single-piping / single-resource dependence. So No irrecoverable harm is
best read NOT as one Audit item but as the TOP-LEVEL CONSTRAINT running through
the whole Governance Layer: the loss of FUTURE RANGE OF MOTION.

Governance Audit looks at a GROUP of placements (the cumulative configuration):
  Concentration Risk : Single Interpretation / Single Resource / Single Axis /
                       Single Dependency
  Range-of-Motion    : Exitability / Alternative Paths / Plurality / Archiveability
Human Final is extended beyond adopt/hold/reject to also degrade / distribute /
experiment. This is closer to a Civilizational Decision Support System than a
Placement Simulator. Center: not "explain the world" but "preserve future range
of motion". Candidates only; final is HA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

from detector import Observation, FLOW_RESOURCES
from placement import Placement, apply_placement

# Extended Human-Final options (HA): beyond adopt/hold/reject.
DECISION_OPTIONS = ("採用", "保留", "棄却", "縮退", "分散", "実験")

# Concentration risks (cumulative single-X lock-in): a closing marker present
# without its mitigating reopening = an unmitigated concentration.
_RISKS = (
    # (name, closing_marker, mitigating_reopening, label)
    ("single-interpretation", "concentrate_authority_no_recall", "keep_parallel_paths", "解釈権集中"),
    ("single-axis",           "fix_single_axis",                 "keep_both_views_mediation", "単一軸／単一価値観"),
    ("no-exit",               "remove_margin_exit",              "unhurried_felt_understood", "退出不能"),
)


@dataclass(frozen=True)
class ConcentrationRisk:
    name: str
    present: bool
    mitigated: bool
    label: str


@dataclass(frozen=True)
class RangeOfMotion:
    name: str
    held: bool
    note: str


@dataclass(frozen=True)
class GovernanceVerdict:
    risks: Tuple[ConcentrationRisk, ...]
    properties: Tuple[RangeOfMotion, ...]
    recommended: str                    # one of DECISION_OPTIONS (candidate; final is HA)
    reason: str
    no_irrecoverable_harm: str          # the top constraint reading over the whole config
    p0_unrecoverable: bool = False      # archive-less erase = future range-of-motion foreclosed


def accumulate(baseline: Observation, placements: Tuple[Placement, ...]) -> Observation:
    """The cumulative configuration after applying a sequence of placements."""
    obs = baseline
    for p in placements:
        obs = apply_placement(obs, p)
    return obs


def _resource_concentration(obs: Observation) -> ConcentrationRisk:
    # coarse proxy: broad stagnation = single-resource / single-dependency pressure.
    # (single-platform / single-funding are domain instances — profile extensions.)
    stuck = len(set(obs.resources_stuck))
    present = stuck >= (len(FLOW_RESOURCES) + 1) // 2
    return ConcentrationRisk("single-resource", present, mitigated=False, label="資源集中／単一依存")


def govern(obs: Observation) -> GovernanceVerdict:
    """Governance audit of a cumulative configuration. Candidates only; final HA."""
    closing, reopening = set(obs.closing_present), set(obs.reopening_present)
    risks = [ConcentrationRisk(name, marker in closing, mit in reopening, label)
             for name, marker, mit, label in _RISKS]
    risks.append(_resource_concentration(obs))

    properties = (
        RangeOfMotion("exitability",
                      "remove_margin_exit" not in closing or "unhurried_felt_understood" in reopening,
                      "退出口が残っているか"),
        RangeOfMotion("alternative-paths",
                      "fix_single_axis" not in closing or "keep_parallel_paths" in reopening,
                      "別解／並走経路が残っているか"),
        RangeOfMotion("plurality",
                      "keep_both_views_mediation" in reopening or "concentrate_authority_no_recall" not in closing,
                      "複数の読みが併存しているか"),
        RangeOfMotion("archiveability",
                      "erase_trace_r2_r3" not in closing or "archive_instead_of_erase" in reopening,
                      "痕跡が取り返せる形で残るか"),
    )

    unmitigated = [r for r in risks if r.present and not r.mitigated]
    lost = [p for p in properties if not p.held]

    # No irrecoverable harm (top constraint over the whole Governance Layer):
    # the irreversible erase with no archive = future range-of-motion being foreclosed.
    p0_unrecoverable = "erase_trace_r2_r3" in closing and "archive_instead_of_erase" not in reopening
    nih = ("⚠ 将来の可動域が不可逆に閉じつつある（archive 無き痕跡消去）" if p0_unrecoverable
           else ("注意: 累積 concentration が可動域を狭めつつある" if unmitigated
                 else "可動域は保たれている（candidate）"))

    if p0_unrecoverable:
        recommended, reason = "棄却", "No irrecoverable harm: 不可逆な可動域消失 — 配置群を棄却 or 縮退"
    elif len(unmitigated) >= 2:
        recommended, reason = "縮退", f"累積 concentration {len(unmitigated)} 件（{', '.join(r.label for r in unmitigated)}）— 縮退 or 分散"
    elif len(unmitigated) == 1:
        recommended, reason = "分散", f"concentration: {unmitigated[0].label} — 分散 or 実験で代替経路を保つ"
    elif lost:
        recommended, reason = "実験", f"range-of-motion 低下（{', '.join(p.name for p in lost)}）— 実験的に代替を確保"
    else:
        recommended, reason = "採用", "concentration なし・可動域保持（採用候補）"

    return GovernanceVerdict(tuple(risks), properties, recommended, reason, nih, p0_unrecoverable)


def render(v: GovernanceVerdict) -> str:
    lines = [f"Governance Audit — recommended: {v.recommended}  "
             f"(of {'/'.join(DECISION_OPTIONS)} · candidate · 最終は HA)",
             f"  理由: {v.reason}",
             f"  No irrecoverable harm（最上位制約）: {v.no_irrecoverable_harm}", "",
             "  Concentration Risk（累積 single-X lock-in）:"]
    for r in v.risks:
        if r.present:
            state = "緩和済" if r.mitigated else "⚠ 未緩和"
            lines.append(f"    [{state}] {r.name}: {r.label}")
    if not any(r.present for r in v.risks):
        lines.append("    (none)")
    lines += ["", "  Range-of-Motion（可動域の property）:"]
    for p in v.properties:
        lines.append(f"    [{'保持' if p.held else '⚠ 低下'}] {p.name}: {p.note}")
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    print("=" * 70)
    print("IBE — Governance Layer v0 (cumulative lock-in; No irrecoverable harm = top)")
    print("=" * 70)

    baseline = Observation(label="site")

    # Each placement might pass a LOCAL audit, but cumulatively they concentrate.
    concentrating = (
        Placement(label="p1", add_closing=("fix_single_axis",)),
        Placement(label="p2", add_closing=("concentrate_authority_no_recall",)),
        Placement(label="p3", add_closing=("remove_margin_exit",)),
    )
    print("\n--- cumulative A+B+C (each may pass locally) ---")
    print(render(govern(accumulate(baseline, concentrating))))

    # Same closings but each placement also leaves a counter -> mitigated.
    plural = (
        Placement(label="q1", add_closing=("fix_single_axis",), add_reopening=("keep_both_views_mediation",)),
        Placement(label="q2", add_closing=("concentrate_authority_no_recall",), add_reopening=("keep_parallel_paths",)),
        Placement(label="q3", add_closing=("remove_margin_exit",), add_reopening=("unhurried_felt_understood",)),
    )
    print("\n--- cumulative with counters left (plurality kept) ---")
    print(render(govern(accumulate(baseline, plural))))
    print("\n" + "=" * 70)
    print("local pass != governance pass; cumulative concentration is what bites.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
