"""
IBE — HA Position / Decision Context (engine/decision_context.py)
================================================================
Phase-1 next step (HA): make the HA Position explicit. NOT a personality model —
a DECLARED Decision Context: what HA wants to PROTECT / INCREASE / AVOID. The
human (HA) declares it; the engine NEVER infers it (HTE discipline: do not model
the human; felt_understood != adopted_self).

It conditions the world reading into "World as read from HA" (W | HA): the same
Detector candidates, re-prioritized through HA's Decision Context. HA remains not
as a philosophical center but as an OPERATIONAL requirement — a decision-support
system needs the position of the one who finally decides (the exit).

Final evaluation direction (HA): Lock-in ↓ / Reversibility ↑ / Flow ↑ /
Resource Circulation ↑ / Deployment Reachability ↑. This is a PLACEMENT-SUPPORT
device — "where to place so flow recovers, a return path remains, resources
circulate" — not a world-explaining device.

Discipline: the engine provides the APPARATUS (the DecisionContext structure +
conditioning); it does not generate, infer, or fill in a DecisionContext. The
demo values are ILLUSTRATIVE, not HA's real values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from detector import Detection

# Evaluation axes (controlled vocabulary) and their default desired direction.
AXES: Dict[str, str] = {
    "lock-in": "down",                  # 不可逆化の予兆 — avoid
    "reversibility": "up",              # 戻る道 — protect
    "flow": "up",                       # 流れ — increase
    "resource-circulation": "up",       # 資源循環 — increase
    "deployment-reachability": "up",    # 出せる範囲 — increase
}
ARROW = {"down": "↓", "up": "↑"}

# Which evaluation axis each Detector layer reports on.
LAYER_AXIS = {"lockin": "lock-in", "reversibility": "reversibility", "flow": "flow"}


@dataclass(frozen=True)
class DecisionContext:
    """The HA Position, DECLARED BY HA (never inferred by the engine). Each tuple
    names AXES (see AXES) HA wants to protect / increase / avoid. NOT a personality
    model — a decision frame that conditions the reading and the evaluation."""
    protect: Tuple[str, ...] = ()
    increase: Tuple[str, ...] = ()
    avoid: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for group in (self.protect, self.increase, self.avoid):
            for a in group:
                if a not in AXES:
                    raise ValueError(f"unknown axis in DecisionContext: {a!r} (must be one of {list(AXES)})")


@dataclass(frozen=True)
class ConditionedItem:
    axis: str
    label: str          # archetype id or resource name
    touches: str        # "avoid" | "protect" | "increase" | "background"
    note: str


def touches(axis: str, ctx: DecisionContext) -> str:
    if axis in ctx.avoid:
        return "avoid"
    if axis in ctx.protect:
        return "protect"
    if axis in ctx.increase:
        return "increase"
    return "background"


def read_world_as_ha(d: Detection, ctx: DecisionContext) -> Tuple[ConditionedItem, ...]:
    """W | HA — the Detector reading re-prioritized through HA's Decision Context.
    Items on an axis HA flagged (avoid/protect/increase) surface first; within each
    band the Detector's own monitoring order (lock-in -> reversibility -> flow) is
    preserved (stable sort)."""
    raw: List[Tuple[str, str, str]] = []
    for c in d.lockin_candidates:
        raw.append(("lock-in", c.archetype, c.note))
    for c in d.reversibility_candidates:
        raw.append(("reversibility", c.archetype, c.note))
    for c in d.flow_candidates:
        raw.append(("flow", c.resource, c.note))
    items = [ConditionedItem(axis, label, touches(axis, ctx), note) for axis, label, note in raw]
    return tuple(sorted(items, key=lambda it: it.touches == "background"))  # flagged first, stable


def evaluation_directive(ctx: DecisionContext) -> Tuple[Tuple[str, str, str], ...]:
    """Final evaluation direction in HA's axes (axis, arrow, ha_emphasis).
    The directions are fixed (Lock-in down, the rest up); the Decision Context
    only annotates which axes HA emphasizes — it never flips a direction."""
    return tuple((axis, ARROW[AXES[axis]], touches(axis, ctx)) for axis in AXES)


def render(d: Detection, ctx: DecisionContext) -> str:
    lines = [f"World as read from HA (W | HA) — {d.observation_label}",
             "(HA Position is the exit's operational requirement, not a center; "
             "Decision Context declared by HA, not inferred)", ""]
    for it in read_world_as_ha(d, ctx):
        tag = f"[HA:{it.touches}]" if it.touches != "background" else "[background]"
        lines.append(f"  {tag} ({it.axis}) {it.label} — {it.note}")
    if not d.lockin_candidates and not d.reversibility_candidates and not d.flow_candidates:
        lines.append("  (候補なし)")
    lines += ["", "Evaluation directive (配置支援・HA axes):"]
    for axis, arrow, emph in evaluation_directive(ctx):
        tail = f"  ← HA {emph}" if emph != "background" else ""
        lines.append(f"  {axis} {arrow}{tail}")
    return "\n".join(lines)


# --- Worked example ----------------------------------------------------------

def _demo() -> None:
    from detector import Observation, detect

    print("=" * 70)
    print("IBE — HA Position / Decision Context (Phase-1: make HA Position explicit)")
    print("=" * 70)

    # ILLUSTRATIVE Decision Context — NOT HA's real values. HA declares the real
    # one; the engine never infers it.
    ctx = DecisionContext(
        protect=("reversibility",),
        avoid=("lock-in",),
        increase=("flow", "resource-circulation"),
    )
    obs = Observation(
        label="placement#A (illustrative)",
        closing_present=("remove_margin_exit", "erase_trace_r2_r3", "finalize_decision"),
        reopening_present=("provisional_plus_return_condition",),
        resources_stuck=("relation",),
    )
    print()
    print(render(detect(obs), ctx))
    print("\n" + "=" * 70)
    print("same Detector candidates, read from HA's declared position (illustrative).")
    print("=" * 70)


if __name__ == "__main__":
    _demo()
