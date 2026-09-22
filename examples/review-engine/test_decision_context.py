"""
Regression lock for IBE HA Position / Decision Context (Phase-1).

Locks: DecisionContext is DECLARED (never inferred — default is empty); the 5
evaluation axes; touches() mapping; W|HA re-prioritization (flagged-first, stable
within band); evaluation_directive directions are FIXED (lock-in down, rest up)
and HA emphasis only annotates (never flips); fail-closed on unknown axis.

Run:  python3 engine/test_decision_context.py
"""
import unittest

from detector import Observation, detect
from decision_context import (
    DecisionContext, AXES, touches, read_world_as_ha, evaluation_directive, render,
)


class Context(unittest.TestCase):
    def test_axes_vocabulary(self):
        self.assertEqual(set(AXES), {"lock-in", "reversibility", "flow",
                                     "resource-circulation", "deployment-reachability"})
        self.assertEqual(AXES["lock-in"], "down")              # avoid
        self.assertTrue(all(v == "up" for k, v in AXES.items() if k != "lock-in"))

    def test_default_is_empty_not_inferred(self):
        # discipline: the engine never assumes HA's values — default Decision
        # Context is empty; HA must declare it.
        ctx = DecisionContext()
        self.assertEqual((ctx.protect, ctx.increase, ctx.avoid), ((), (), ()))

    def test_unknown_axis_raises(self):
        with self.assertRaises(ValueError):
            DecisionContext(protect=("happiness",))

    def test_touches(self):
        ctx = DecisionContext(protect=("reversibility",), avoid=("lock-in",), increase=("flow",))
        self.assertEqual(touches("lock-in", ctx), "avoid")
        self.assertEqual(touches("reversibility", ctx), "protect")
        self.assertEqual(touches("flow", ctx), "increase")
        self.assertEqual(touches("deployment-reachability", ctx), "background")


class ConditionedReading(unittest.TestCase):
    def _detection(self):
        return detect(Observation(
            label="x",
            closing_present=("remove_margin_exit", "finalize_decision"),
            resources_stuck=("relation",)))

    def test_flagged_axes_surface_first(self):
        # HA flags only flow; the flow item must come before unflagged lock-in/rev
        ctx = DecisionContext(increase=("flow",))
        items = read_world_as_ha(self._detection(), ctx)
        self.assertEqual(items[0].axis, "flow")
        self.assertEqual(items[0].touches, "increase")
        self.assertTrue(all(it.touches == "background" for it in items[1:]))

    def test_stable_within_band_preserves_detector_order(self):
        # all flagged -> Detector monitoring order preserved: lock-in, reversibility, flow
        ctx = DecisionContext(avoid=("lock-in",), protect=("reversibility",), increase=("flow",))
        axes = [it.axis for it in read_world_as_ha(self._detection(), ctx)]
        self.assertEqual(axes, ["lock-in", "reversibility", "flow"])

    def test_no_context_all_background(self):
        items = read_world_as_ha(self._detection(), DecisionContext())
        self.assertTrue(all(it.touches == "background" for it in items))
        # still present, just unprioritized
        self.assertEqual(len(items), 3)


class EvaluationDirective(unittest.TestCase):
    def test_directions_fixed_emphasis_only(self):
        ctx = DecisionContext(avoid=("lock-in",), protect=("reversibility",))
        d = {axis: (arrow, emph) for axis, arrow, emph in evaluation_directive(ctx)}
        self.assertEqual(d["lock-in"], ("↓", "avoid"))
        self.assertEqual(d["reversibility"], ("↑", "protect"))
        self.assertEqual(d["flow"], ("↑", "background"))        # not emphasized, still ↑
        self.assertEqual(d["deployment-reachability"], ("↑", "background"))

    def test_context_never_flips_direction(self):
        # even if HA (mistakenly) "avoids" reversibility, its direction stays ↑
        ctx = DecisionContext(avoid=("reversibility",))
        d = {axis: arrow for axis, arrow, emph in evaluation_directive(ctx)}
        self.assertEqual(d["reversibility"], "↑")
        self.assertEqual(d["lock-in"], "↓")


class Render(unittest.TestCase):
    def test_render_frames_w_given_ha(self):
        text = render(detect(Observation(label="x", closing_present=("finalize_decision",))),
                      DecisionContext(protect=("reversibility",)))
        self.assertIn("World as read from HA (W | HA)", text)
        self.assertIn("not a center", text)
        self.assertIn("Evaluation directive", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
