"""
Regression lock for the IBE Proposal Object (the stable sink).

Locks: build_proposal composes L1 (region_delta) + L2 (transition_surface,
split_confidence) + structural risk; reason deferred by default and settable;
render() emits every section and the adopt/hold/reject line. This type is the
fixed interface L3/WTE/HTE will later feed without changing it.

Run:  python3 engine/test_proposal.py
"""
import unittest

from reachability import Constraint, ConstraintSet, ABSTRACT_AXES, IMPOSSIBLE, POSSIBLE
from trajectory import ABSTRACT_GRAPH
from proposal import build_proposal, render, Proposal, Risk, DEFERRED_REASON


def _all_live() -> ConstraintSet:
    return ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("a", 0.90, ("exploration",)),
        Constraint("b", 0.80, ("challenge",)),
        Constraint("c", 0.85, ("dialogue",)),
        Constraint("d", 0.80, ("emergence",)),
    ))


class BuildProposal(unittest.TestCase):
    def test_composes_l1_and_l2(self):
        before = _all_live().set_value("b", 0.0)   # challenge IMPOSSIBLE
        after = before.set_value("b", 0.70)         # open challenge
        p = build_proposal(17, "open challenge", before, after, ABSTRACT_GRAPH)
        self.assertIsInstance(p, Proposal)
        self.assertAlmostEqual(p.region_delta["challenge"], 0.70, places=4)         # L1
        self.assertEqual(p.transition_surface.verdict_shifts,                        # L2
                         {"challenge": (IMPOSSIBLE, POSSIBLE)})
        self.assertEqual(set(p.confidence.keys()) >= {
            "inference_confidence", "constraint_confidence", "trajectory_confidence"}, True)

    def test_risk_from_closure(self):
        before = _all_live()
        after = before.set_value("b", 0.0)          # close challenge
        p = build_proposal(1, "close challenge", before, after, ABSTRACT_GRAPH)
        self.assertEqual(p.risk.closed, ("challenge",))
        self.assertEqual(set(p.risk.lost_trajectories), {
            ("challenge", "emergence"),
            ("exploration", "challenge"),
            ("exploration", "challenge", "emergence"),
        })

    def test_no_structural_loss_on_opening(self):
        before = _all_live().set_value("b", 0.0)
        after = before.set_value("b", 0.70)         # opening -> nothing lost
        p = build_proposal(2, "open challenge", before, after, ABSTRACT_GRAPH)
        self.assertTrue(p.risk.is_empty())

    def test_reason_deferred_then_settable(self):
        before = _all_live()
        after = before.set_value("b", 0.0)
        self.assertEqual(build_proposal(3, "x", before, after, ABSTRACT_GRAPH).reason,
                         DEFERRED_REASON)
        p2 = build_proposal(4, "x", before, after, ABSTRACT_GRAPH,
                            reason="Posterior_W/Posterior_H overlap maximal")
        self.assertIn("overlap", p2.reason)


class RenderForm(unittest.TestCase):
    def test_all_sections_present(self):
        before = _all_live()
        after = before.set_value("b", 0.0)
        text = render(build_proposal(17, "close challenge", before, after, ABSTRACT_GRAPH))
        for token in ("Proposal #17", "Expected Region Delta:", "Transition Surface:",
                      "Risk (structural):", "Confidence:", "Reason:",
                      "採用 / 保留 / 棄却?"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
