"""
IBE — Domain Profile / Profile Translation (engine/profiles.py)  [Runtime Spec §7 #1]
=====================================================================================
⑥ Runtime Review: the STRONG scale-isomorphism test asks whether a domain modeled
on its OWN vocabulary still projects to the CDSS grammar. A DomainProfile IS the
"Profile Translation": a map from domain-specific terms -> the abstract grammar
(closing / reopening archetypes + Resource-Layer flows). The Engine consumes the
TRANSLATED (abstract) placement; the profile only renames — it adds no new
computation.

    domain placement (domain terms) -> [Profile Translation] -> abstract Placement
        -> Engine -> Verdict

If the translation is NATURAL across domains, scale-isomorphism is strong; if
FORCED, the break is in the Profile Translation, NOT the Engine. Phase-1 is the
abstract IDENTITY profile; domain-specific profiles are TRUSTED only after the ⑥
review judges their translation natural (the maps below are MECHANISM tests, not
validated domain claims). This module is the structural close of Runtime Spec §7 #1
(the Engine can now consume domain-labeled placements via a profile).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from detector import CLOSING_ARCHETYPES, REOPENING_ARCHETYPES, FLOW_RESOURCES
from placement import Placement


@dataclass(frozen=True)
class DomainProfile:
    """Profile Translation: domain term -> abstract grammar id. Validated on
    construction (every target must be a real archetype/resource — fail-closed)."""
    profile_id: str
    domain: str
    closing_map: Dict[str, str] = field(default_factory=dict)     # domain closing term -> closing archetype
    reopening_map: Dict[str, str] = field(default_factory=dict)   # domain reopening term -> reopening archetype
    resource_map: Dict[str, str] = field(default_factory=dict)    # domain resource term -> FLOW_RESOURCE

    def __post_init__(self) -> None:
        for term, a in self.closing_map.items():
            if a not in CLOSING_ARCHETYPES:
                raise ValueError(f"{self.profile_id}: closing '{term}' -> unknown archetype {a!r}")
        for term, a in self.reopening_map.items():
            if a not in REOPENING_ARCHETYPES:
                raise ValueError(f"{self.profile_id}: reopening '{term}' -> unknown archetype {a!r}")
        for term, r in self.resource_map.items():
            if r not in FLOW_RESOURCES:
                raise ValueError(f"{self.profile_id}: resource '{term}' -> unknown resource {r!r}")


# Phase-1 identity profile: domain terms ARE the abstract ids (no translation).
ABSTRACT_PROFILE = DomainProfile("abstract-v0", "abstract")


def _tr(term: str, m: Dict[str, str]) -> str:
    return m.get(term, term)   # identity fallback: an already-abstract id passes through


def translate(profile: DomainProfile, domain_placement: Placement) -> Placement:
    """Translate a domain-term placement into an abstract Placement the Engine
    consumes. The profile only renames; the Engine does the computation."""
    return Placement(
        label=f"[{profile.domain}] {domain_placement.label}",
        add_closing=tuple(_tr(t, profile.closing_map) for t in domain_placement.add_closing),
        remove_closing=tuple(_tr(t, profile.closing_map) for t in domain_placement.remove_closing),
        add_reopening=tuple(_tr(t, profile.reopening_map) for t in domain_placement.add_reopening),
        remove_reopening=tuple(_tr(t, profile.reopening_map) for t in domain_placement.remove_reopening),
        unblock_resources=tuple(_tr(t, profile.resource_map) for t in domain_placement.unblock_resources),
        block_resources=tuple(_tr(t, profile.resource_map) for t in domain_placement.block_resources),
    )


# --- MECHANISM-TEST profiles (illustrative; NOT validated domain claims — the ⑥
#     review judges whether such translations are natural or forced) ------------
CHILDCARE_PROFILE_DEMO = DomainProfile(
    "childcare-demo", "保育",
    closing_map={
        "単一発達指標で評価": "fix_single_axis",
        "一人の保育者に判断集約": "concentrate_authority_no_recall",
        "観察記録を破棄": "erase_trace_r2_r3",
        "自由遊びの余白を潰す": "remove_margin_exit",
    },
    reopening_map={
        "複数の見方を残す": "keep_both_views_mediation",
        "別の関わりを試せる": "keep_parallel_paths",
        "記録をアーカイブ": "archive_instead_of_erase",
    },
    resource_map={"信頼": "trust", "注意": "attention"})


def _demo() -> None:
    from decision_context import DecisionContext
    from detector import Observation
    from runtime import run_cycle, render

    print("=" * 70)
    print("IBE — Domain Profile / Profile Translation (Runtime Spec §7 #1)")
    print("=" * 70)

    ctx = DecisionContext(protect=("reversibility",), increase=("flow",), avoid=("lock-in",))
    base = Observation(label="保育園", resources_stuck=("trust",))

    # A placement written in CHILDCARE TERMS; translated to the abstract grammar.
    domain_pl = Placement(label="観察記録を破棄", add_closing=("観察記録を破棄",))
    abstract_pl = translate(CHILDCARE_PROFILE_DEMO, domain_pl)
    print(f"\ndomain term: {domain_pl.add_closing}  ->  abstract: {abstract_pl.add_closing}")
    print()
    print(render(run_cycle(ctx, base, abstract_pl)))
    print("\n" + "=" * 70)
    print("the same grammar reads a domain-term placement (mechanism); ⑥ judges if natural.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
