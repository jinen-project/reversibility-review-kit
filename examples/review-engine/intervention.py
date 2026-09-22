"""
IBE — Governance Intervention Engine / Reopening Engine v0 (engine/intervention.py)
==================================================================================
HA: the Governance Audit only DETECTS cumulative lock-in. The real value is the
next step — detect -> how to MITIGATE. At the civilizational layer the value shows
when the device returns "what to ADD to reduce the danger": how to distribute, how
to restore exitability, how to add alternative paths. Path-dependence research says
the same: the point is not to EXPLAIN lock-in but to INCREASE THE OPTIONS AGAIN
(interrupt the self-reinforcement and re-widen the scope for maneuver).

So after Governance Audit comes Governance Intervention. Its substance is exactly
boundary / margin / mediation restored (境界 / 余白 / 媒介 を戻す). The recovery
patterns are world-reading's 7 reopening archetypes — this is the INVERSE of the
Detector (closing detection): a Reopening Engine. The COUNTER_MOVE map already
pairs each closing with its reopening.

The engine returns intervention candidates and can construct the intervention as a
Placement (add the reopening moves); re-running the Governance Audit then shows the
risks mitigated — closing the detect -> recover loop. Candidates only; final is HA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from placement import Placement
from governance import GovernanceVerdict, govern, accumulate

# risk -> reopening interventions that restore the return path, mapped to
# boundary/margin/mediation and a recovery action (HA's "how to distribute / how
# to restore exitability / how to add alternative paths").
INTERVENTION = {
    "single-interpretation": {
        "reopening": ("keep_parallel_paths", "keep_both_views_mediation", "archive_instead_of_erase"),
        "restores": "媒介",
        "recovery": "解釈権を分散・複数読解を残す・アーカイブを残す",
    },
    "single-axis": {
        "reopening": ("keep_both_views_mediation", "keep_parallel_paths"),
        "restores": "境界／媒介",
        "recovery": "両論併記・別軸での再読解を戻す",
    },
    "no-exit": {
        "reopening": ("unhurried_felt_understood", "provisional_plus_return_condition"),
        "restores": "余白",
        "recovery": "退出口／例外窓口を戻す・暫定＋再開条件を添える",
    },
    "single-resource": {
        "reopening": ("keep_parallel_paths", "carry_unmet_demand"),
        "restores": "境界／媒介",
        "recovery": "資源経路を分散・未充足の痕跡を併走",
    },
}
# The irreversible (P0) erase intervention: restore recoverability.
P0_INTERVENTION = {
    "reopening": ("archive_instead_of_erase",),
    "restores": "余白",
    "recovery": "破棄でなくアーカイブ／隔離保存（痕跡を取り返せる形で残す）",
}


@dataclass(frozen=True)
class Intervention:
    risk: str
    label: str
    reopening: Tuple[str, ...]   # reopening archetypes to ADD
    restores: str                # 境界 / 余白 / 媒介
    recovery: str                # the recovery action (how to widen the scope for maneuver)


def intervene(v: GovernanceVerdict) -> Tuple[Intervention, ...]:
    """Return reopening interventions for each unmitigated concentration risk (and
    the P0 erase). These are the moves that re-widen the scope for maneuver."""
    out = []
    if v.p0_unrecoverable:
        out.append(Intervention("irreversible-p0", "不可逆な痕跡消去",
                                P0_INTERVENTION["reopening"], P0_INTERVENTION["restores"],
                                P0_INTERVENTION["recovery"]))
    for r in v.risks:
        if r.present and not r.mitigated and r.name in INTERVENTION:
            spec = INTERVENTION[r.name]
            out.append(Intervention(r.name, r.label, spec["reopening"], spec["restores"], spec["recovery"]))
    return tuple(out)


def to_placement(interventions: Tuple[Intervention, ...], label: str = "intervention") -> Placement:
    """Construct the intervention as a single Placement (add all reopening moves).
    Applying it and re-auditing shows the risks mitigated."""
    moves = []
    for iv in interventions:
        for m in iv.reopening:
            if m not in moves:
                moves.append(m)
    return Placement(label=label, add_reopening=tuple(moves))


def render(interventions: Tuple[Intervention, ...]) -> str:
    if not interventions:
        return "Governance Intervention — (介入不要：未緩和 concentration なし)"
    lines = ["Governance Intervention — 危険を減らすために何を足すか（境界／余白／媒介 を戻す・candidate・最終は HA）:"]
    for iv in interventions:
        lines.append(f"  ▸ {iv.risk}（{iv.label}）→ 戻す:{iv.restores}")
        lines.append(f"      reopening: {', '.join(iv.reopening)}")
        lines.append(f"      recovery:  {iv.recovery}")
    return "\n".join(lines)


# --- Worked example (the detect -> recover loop closes) ----------------------

def _demo() -> None:
    from detector import Observation

    print("=" * 70)
    print("IBE — Governance Intervention / Reopening Engine v0 (detect -> recover)")
    print("=" * 70)

    baseline = Observation(label="site")
    concentrating = (
        Placement(label="p1", add_closing=("fix_single_axis",)),
        Placement(label="p2", add_closing=("concentrate_authority_no_recall",)),
        Placement(label="p3", add_closing=("remove_margin_exit",)),
    )
    config = accumulate(baseline, concentrating)

    before = govern(config)
    print(f"\nGovernance before: recommended={before.recommended}  "
          f"(未緩和 {sum(1 for r in before.risks if r.present and not r.mitigated)} 件)")

    ivs = intervene(before)
    print()
    print(render(ivs))

    # apply the intervention and re-audit -> mitigated
    recovered = accumulate(config, (to_placement(ivs, "recovery"),))
    after = govern(recovered)
    print(f"\nGovernance after intervention: recommended={after.recommended}  "
          f"(未緩和 {sum(1 for r in after.risks if r.present and not r.mitigated)} 件)")
    print("\n" + "=" * 70)
    print("detect -> intervene -> re-audit: concentration mitigated; HA decides.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
