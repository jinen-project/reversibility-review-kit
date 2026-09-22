"""
Regression lock for IBE L2 — Reachable Trajectory Bundle.

Locks: bundle = reachable simple paths; IMPOSSIBLE axes drop their paths;
Transition Surface (appeared / disappeared + verdict shifts); undetermined paths
through UNCONSTRAINED axes; split confidence (constraint / trajectory / inference
= weakest link); fail-closed graph validation; no silent cap.

Run:  python3 engine/test_trajectory.py
"""
import unittest

from reachability import Constraint, ConstraintSet, ABSTRACT_AXES, IMPOSSIBLE, POSSIBLE
from trajectory import (
    TransitionGraph, ABSTRACT_GRAPH, trajectory_bundle, transition_surface,
    split_confidence, propose,
)


def _all_live() -> ConstraintSet:
    return ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("a", 0.90, ("exploration",)),
        Constraint("b", 0.80, ("challenge",)),
        Constraint("c", 0.85, ("dialogue",)),
        Constraint("d", 0.80, ("emergence",)),
    ))


class BundleEnumeration(unittest.TestCase):
    def test_all_live_full_bundle(self):
        b = trajectory_bundle(_all_live(), ABSTRACT_GRAPH)
        self.assertEqual(set(b.trajectories), {
            ("exploration", "challenge"),
            ("exploration", "dialogue"),
            ("challenge", "emergence"),
            ("dialogue", "emergence"),
            ("exploration", "challenge", "emergence"),
            ("exploration", "dialogue", "emergence"),
        })
        self.assertEqual(len(b.determinate), 6)
        self.assertEqual(len(b.undetermined), 0)
        self.assertFalse(b.capped)  # no silent cap on a small graph

    def test_impossible_axis_drops_its_paths(self):
        cs = _all_live().set_value("b", 0.0)  # challenge IMPOSSIBLE
        b = trajectory_bundle(cs, ABSTRACT_GRAPH)
        self.assertEqual(set(b.trajectories), {
            ("exploration", "dialogue"),
            ("dialogue", "emergence"),
            ("exploration", "dialogue", "emergence"),
        })
        self.assertTrue(all("challenge" not in t for t in b.trajectories))

    def test_unconstrained_axis_makes_paths_undetermined(self):
        cs = _all_live().remove("c")  # dialogue loses its only cap -> UNCONSTRAINED
        b = trajectory_bundle(cs, ABSTRACT_GRAPH)
        self.assertEqual(len(b.trajectories), 6)        # dialogue still live
        self.assertEqual(len(b.determinate), 3)         # paths not through dialogue
        self.assertEqual(len(b.undetermined), 3)        # paths through dialogue


class TransitionSurfaceTest(unittest.TestCase):
    def test_appeared_on_opening_axis(self):
        before = _all_live().set_value("b", 0.0)        # challenge IMPOSSIBLE
        after = before.set_value("b", 0.70)             # challenge POSSIBLE
        surf = transition_surface(before, after, ABSTRACT_GRAPH)
        self.assertEqual(surf.verdict_shifts, {"challenge": (IMPOSSIBLE, POSSIBLE)})
        self.assertEqual(set(surf.appeared), {
            ("challenge", "emergence"),
            ("exploration", "challenge"),
            ("exploration", "challenge", "emergence"),
        })
        self.assertEqual(surf.disappeared, ())

    def test_disappeared_on_closing_axis(self):
        before = _all_live()
        after = before.set_value("b", 0.0)              # close challenge
        surf = transition_surface(before, after, ABSTRACT_GRAPH)
        self.assertEqual(surf.appeared, ())
        self.assertEqual(set(surf.disappeared), {
            ("challenge", "emergence"),
            ("exploration", "challenge"),
            ("exploration", "challenge", "emergence"),
        })


class SplitConfidence(unittest.TestCase):
    def test_three_terms_and_weakest_link(self):
        cs = _all_live().remove("c")  # dialogue UNCONSTRAINED
        conf = split_confidence(cs, ABSTRACT_GRAPH)
        self.assertEqual(conf["constraint_confidence"], 0.75)   # 3/4 axes determined
        self.assertEqual(conf["trajectory_confidence"], 0.5)    # 3/6 paths determinate
        self.assertEqual(conf["inference_confidence"], 0.5)     # min(0.75, 0.5)

    def test_fail_closed_terms_deferred(self):
        conf = split_confidence(_all_live(), ABSTRACT_GRAPH)
        self.assertFalse(conf["coupling"]["reality_coupled"])
        for term in ("evidence_strength", "wte_consistency", "hte_consistency"):
            self.assertIn("deferred", conf["deferred"][term])


class ProposalForm(unittest.TestCase):
    def test_proposal_shape(self):
        before = _all_live().set_value("b", 0.0)
        after = before.set_value("b", 0.70)
        text = propose(17, "psychological_safety up", before, after, ABSTRACT_GRAPH)
        for token in ("Proposal #17", "Transition Surface:", "Confidence:",
                      "採用? 保留? 棄却?"):
            self.assertIn(token, text)


class GraphValidation(unittest.TestCase):
    def test_unknown_axis_raises(self):
        bad = TransitionGraph(edges=(("ghost", "exploration"),))
        with self.assertRaises(ValueError):
            trajectory_bundle(_all_live(), bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
