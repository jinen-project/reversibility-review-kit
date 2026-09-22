"""
IBE — Flow & Reversibility Detector v0.2 (engine/detector.py)
============================================================
Phase-1 core (HA). Returns CANDIDATES, never truth. THREE layers, in HA's
monitoring order — No irrecoverable harm is the FIRST monitoring item, not the
last evaluation item:

    Lock-in Pressure   ->   Reversibility Loss   ->   Flow Collapse
   (境界硬直/余白消失/媒介喪失)     (戻れなくなる)            (流れなくなる)

So the detector runs Lock-in Detector -> Reversibility Detector -> Flow Detector
(catch irreversibilization BEFORE it begins, not after). It is NOT Posterior_W
and NOT a world model — once it runs, Posterior_W grows naturally; the reverse
pulls back toward a world-explaining device (HA).

Discipline
----------
  - hypothesis-conditional (P0, no reality claim): the input is a described
    Observation, the output is candidates.
  - candidates only (hedged "...かもしれない"), never truth.
  - No irrecoverable harm first: the Lock-in layer (precursor to irreversibility)
    is monitored first; an R2->R3 erase is the irreversible endpoint = HARP P0
    NO IRRECOVERABLE ERASURE, flagged `irreversible-p0` (alarm).
  - not_a_new_base: the archetypes are lenses on the shelf, not a new center.
  - RORC: the presets are the MADE archetype LABELS from
    world_reading_pattern_synthesis.json (6 closing + 7 reopening) and the
    circulation-os Resource Layer — NOT the lived corpus rows (pointer-only).

This re-casts existing extracted material; it does not extract from zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# --- Presets (made archetype labels; world_reading_pattern_synthesis.json) -----

# 6 closing archetypes (a return path is being removed).
CLOSING_ARCHETYPES: Dict[str, str] = {
    "essentialize_person": "人物本質ラベルで反復処理（別の関わりを試しても読み直さない）",
    "finalize_decision": "確定の最終化（留保を記録に残さない）",
    "erase_trace_r2_r3": "痕跡ごとの消去（R2 解釈固定 → R3 物理消去への滑落）",
    "remove_margin_exit": "余白／出口／例外窓口の撤去",
    "fix_single_axis": "単一軸への一元固定（別軸での再読解を運用上不可能に）",
    "concentrate_authority_no_recall": "解釈権／代表性の一点集約・不可リコール化",
}

# 7 reopening archetypes (the return-path counter-moves).
REOPENING_ARCHETYPES: Dict[str, str] = {
    "reencode_as_observation_log": "裁定 → 観察ログへの再符号化",
    "provisional_plus_return_condition": "確定 → 暫定＋再開条件の明示",
    "archive_instead_of_erase": "破棄 → アーカイブ／隔離保存",
    "keep_both_views_mediation": "両論併記／接続可能な差異の併置（媒介）",
    "carry_unmet_demand": "需要起点／未充足の痕跡を併走",
    "keep_parallel_paths": "複数化・分散・並走経路の保持（別解へ移れる）",
    "unhurried_felt_understood": "急がない felt_understood（余白）",
}

# closing archetype -> the reopening counter-move that restores the return path.
COUNTER_MOVE: Dict[str, str] = {
    "essentialize_person": "reencode_as_observation_log",
    "finalize_decision": "provisional_plus_return_condition",
    "erase_trace_r2_r3": "archive_instead_of_erase",
    "remove_margin_exit": "unhurried_felt_understood",
    "fix_single_axis": "keep_both_views_mediation",
    "concentrate_authority_no_recall": "keep_parallel_paths",
}

# Stage on the irreversibilization trajectory: Lock-in -> Reversibility -> Irreversible.
STAGE: Dict[str, str] = {
    "remove_margin_exit": "lock-in",                 # 余白が消える
    "fix_single_axis": "lock-in",                    # 境界が硬直／選択肢が減る
    "concentrate_authority_no_recall": "lock-in",    # 媒介が失われる／解釈権集中
    "essentialize_person": "reversibility-loss",     # 読み直さない＝戻りにくい
    "finalize_decision": "reversibility-loss",       # 留保を残さない
    "erase_trace_r2_r3": "irreversible",             # R2->R3 = HARP P0 NO IRRECOVERABLE ERASURE
}

# Lock-in precursor -> which of 境界/余白/媒介 stiffens or vanishes (HA correspondence).
LOCKIN_DEGRADES: Dict[str, str] = {
    "remove_margin_exit": "余白",
    "fix_single_axis": "境界",
    "concentrate_authority_no_recall": "媒介",
}

# circulation-os Resource Layer — flows whose stagnation is a Flow Candidate.
FLOW_RESOURCES: Tuple[str, ...] = ("time", "attention", "money", "trust", "knowledge", "relation")

# --- Invariants (lock reverse-direction coverage: a deleted entry fails LOUD at
#     import, not as an uncaught KeyError later — escaping the fail-closed contract).
assert set(COUNTER_MOVE) == set(CLOSING_ARCHETYPES), "COUNTER_MOVE must cover every closing archetype"
assert set(STAGE) == set(CLOSING_ARCHETYPES), "STAGE must classify every closing archetype"
assert set(LOCKIN_DEGRADES) == {a for a, s in STAGE.items() if s == "lock-in"}, \
    "LOCKIN_DEGRADES must cover exactly the lock-in stage"
assert all(v in REOPENING_ARCHETYPES for v in COUNTER_MOVE.values()), "counter-moves must be real reopenings"


# --- Input / Output ----------------------------------------------------------

@dataclass(frozen=True)
class Observation:
    """A hypothesis-conditional description of an asset / placement / config:
    which closing patterns are present, which reopening counter-moves are present,
    and which Resource-Layer flows are stuck. NOT a claim about the world."""
    label: str
    closing_present: Tuple[str, ...] = ()
    reopening_present: Tuple[str, ...] = ()
    resources_stuck: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LockinCandidate:
    archetype: str
    degrades: str          # 境界 / 余白 / 媒介
    gloss: str
    counter_move: str
    counter_present: bool
    note: str


@dataclass(frozen=True)
class ReversibilityCandidate:
    archetype: str
    severity: str          # "irreversible-p0" | "reversibility-loss"
    gloss: str
    counter_move: str
    counter_present: bool
    note: str


@dataclass(frozen=True)
class FlowCandidate:
    resource: str
    note: str


@dataclass(frozen=True)
class Detection:
    observation_label: str
    lockin_candidates: Tuple[LockinCandidate, ...]
    reversibility_candidates: Tuple[ReversibilityCandidate, ...]
    flow_candidates: Tuple[FlowCandidate, ...]


# --- Detector ----------------------------------------------------------------

def detect(obs: Observation) -> Detection:
    """Read an Observation and return three-layer CANDIDATES (never truth).

    Fail-closed: unknown archetype / resource ids raise (do not silently drop)."""
    for a in obs.closing_present:
        if a not in CLOSING_ARCHETYPES:
            raise ValueError(f"unknown closing archetype: {a!r}")
    for a in obs.reopening_present:
        if a not in REOPENING_ARCHETYPES:
            raise ValueError(f"unknown reopening archetype: {a!r}")
    for r in obs.resources_stuck:
        if r not in FLOW_RESOURCES:
            raise ValueError(f"unknown resource: {r!r}")

    lockin: List[LockinCandidate] = []
    rev: List[ReversibilityCandidate] = []
    for a in obs.closing_present:
        counter = COUNTER_MOVE[a]
        counter_present = counter in obs.reopening_present
        tail = "対抗手（再開路）あり" if counter_present else "対抗手なし＝可動域が閉じる候補"
        if STAGE[a] == "lock-in":
            deg = LOCKIN_DEGRADES[a]
            lockin.append(LockinCandidate(
                archetype=a, degrades=deg, gloss=CLOSING_ARCHETYPES[a],
                counter_move=counter, counter_present=counter_present,
                note=f"ここで不可逆化が始まりつつあるかもしれない（{deg}が硬直／消失）／{tail}"))
        else:
            severity = "irreversible-p0" if STAGE[a] == "irreversible" else "reversibility-loss"
            rev.append(ReversibilityCandidate(
                archetype=a, severity=severity, gloss=CLOSING_ARCHETYPES[a],
                counter_move=counter, counter_present=counter_present,
                note=f"ここで戻れなくなりつつあるかもしれない／{tail}"))

    # lock-in: no-counter first (closer to lock). reversibility: irreversible-p0
    # first (line already crossed = alarm), then no-counter, then counter-present.
    lockin.sort(key=lambda c: c.counter_present)
    rev.sort(key=lambda c: (c.severity != "irreversible-p0", c.counter_present))

    flow = tuple(FlowCandidate(resource=r, note="ここで流れが詰まっているかもしれない")
                 for r in obs.resources_stuck)
    return Detection(obs.label, tuple(lockin), tuple(rev), flow)


def priority_reading(d: Detection) -> List[str]:
    """Order concerns by HA's monitoring order — Lock-in (the precursor to
    irreversibility = the first monitoring item) BEFORE Reversibility BEFORE Flow."""
    lines: List[str] = []
    for c in d.lockin_candidates:
        lines.append(f"[1 不可逆化の予兆 · lock-in:{c.degrades}] {c.archetype} — {c.note}")
    for c in d.reversibility_candidates:
        tag = "⚠P0" if c.severity == "irreversible-p0" else "reversibility-loss"
        lines.append(f"[2 戻れるか · {tag}] {c.archetype} — {c.note}")
    for f in d.flow_candidates:
        lines.append(f"[3 流れるか] {f.resource} — {f.note}")
    if not lines:
        lines.append("(候補なし — Lock-in/Reversibility/Flow の予兆は検出されなかった)")
    return lines


def render(d: Detection) -> str:
    lines = [f"Flow & Reversibility Detection — {d.observation_label}",
             "(candidates only · hypothesis-conditional · not a world model)", "",
             "[1] Lock-in Candidates (不可逆化が始まりつつある位置 — 境界/余白/媒介の硬直・消失):"]
    if d.lockin_candidates:
        for c in d.lockin_candidates:
            cm = f"→ 対抗手: {c.counter_move}" + ("（あり）" if c.counter_present else "（無し）")
            lines.append(f"  [{c.degrades}] {c.archetype}: {c.gloss}  {cm}")
    else:
        lines.append("  (none)")
    lines += ["", "[2] Reversibility Candidates (戻れなくなりつつある位置 — ⚠P0 = 不可逆の線):"]
    if d.reversibility_candidates:
        for c in d.reversibility_candidates:
            flag = "⚠P0" if c.severity == "irreversible-p0" else "rev-loss"
            cm = f"→ 対抗手: {c.counter_move}" + ("（あり）" if c.counter_present else "（無し）")
            lines.append(f"  [{flag}] {c.archetype}: {c.gloss}  {cm}")
    else:
        lines.append("  (none)")
    lines += ["", "[3] Flow Candidates (流れが詰まっている位置 — circulation-os Resource Layer):"]
    if d.flow_candidates:
        for f in d.flow_candidates:
            lines.append(f"  • {f.resource}: {f.note}")
    else:
        lines.append("  (none)")
    lines += ["", "監視順（HA: 不可逆化の予兆 → 戻れるか → 流れるか／No irrecoverable harm が最初の監視項目）:"]
    lines += [f"  {l}" for l in priority_reading(d)]
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    print("=" * 70)
    print("IBE — Flow & Reversibility Detector v0.2 (Phase-1 core · three layers)")
    print("=" * 70)

    # A placement described hypothesis-conditionally: it removes exits (lock-in),
    # finalizes a decision (reversibility-loss), erases traces R2->R3 (irreversible
    # / P0), while keeping one return-condition counter-move; relation & attention
    # flows are stuck.
    obs = Observation(
        label="placement#A (例: ある資産をこの位置に置いた配置)",
        closing_present=("remove_margin_exit", "finalize_decision", "erase_trace_r2_r3"),
        reopening_present=("provisional_plus_return_condition",),
        resources_stuck=("relation", "attention"),
    )
    print()
    print(render(detect(obs)))
    print("\n" + "=" * 70)
    print("three-layer candidates, not truth; lock-in (earliest) monitored first; P0 = line.")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
