"""
Regression lock for the IBE Reachability Simulator (Phase 1).

Locks the worked-example numbers and the discipline invariants so that adding
Layer 2 (Trajectory Bundle) later cannot silently break the built behavior.

Run:  python3 engine/test_reachability.py    (or: python3 -m unittest -v)
stdlib only · no dependencies.
"""
import unittest

from reachability import (
    Constraint, ConstraintSet, reachable_region, region_delta, enclosure_risk,
    confidence_layer, ABSTRACT_AXES, POSSIBLE, IMPOSSIBLE, UNCONSTRAINED,
)


def _base() -> ConstraintSet:
    return ConstraintSet(axes=ABSTRACT_AXES, constraints=(
        Constraint("enabling_safety", 0.90, ("exploration", "challenge")),
        Constraint("solitude_available", 0.80, ("exploration", "emergence")),
        Constraint("answer_withheld", 0.85, ("dialogue", "emergence")),
    ))


class ReachableRegion(unittest.TestCase):
    def test_intersection_min(self):
        r = reachable_region(_base())
        # exploration = min(0.90, 0.80); emergence = min(0.80, 0.85)
        self.assertEqual(r.widths, {"exploration": 0.80, "challenge": 0.90,
                                    "dialogue": 0.85, "emergence": 0.80})
        self.assertTrue(all(v == POSSIBLE for v in r.verdict.values()))

    def test_enclosure_risk(self):
        # 1 - mean(0.80, 0.90, 0.85, 0.80) = 0.1625
        self.assertAlmostEqual(enclosure_risk(reachable_region(_base())), 0.1625, places=4)

    def test_unconstrained_axis(self):
        cs = ConstraintSet(axes=("a", "b"),
                           constraints=(Constraint("c", 0.5, ("a",)),))
        r = reachable_region(cs)
        self.assertEqual(r.verdict["b"], UNCONSTRAINED)  # no constraint speaks to b
        self.assertEqual(r.widths["b"], 1.0)             # full width, but NOT licensed-open

    def test_impossible_at_zero(self):
        cs = ConstraintSet(axes=("a",), constraints=(Constraint("c", 0.0, ("a",)),))
        r = reachable_region(cs)
        self.assertEqual(r.verdict["a"], IMPOSSIBLE)
        self.assertEqual(r.widths["a"], 0.0)


class RegionDelta(unittest.TestCase):
    def test_strengthen_shrinks(self):
        base = _base()
        edit = base.add(Constraint("strict_failure_management", 0.20,
                                   ("exploration", "challenge")))
        rd = region_delta(base, edit)
        self.assertAlmostEqual(rd.delta["exploration"], -0.60, places=4)
        self.assertAlmostEqual(rd.delta["challenge"], -0.70, places=4)
        self.assertEqual(rd.delta["dialogue"], 0.0)
        self.assertEqual(rd.after["exploration"], POSSIBLE)  # shrank but still reachable

    def test_edit_to_impossible(self):
        base = _base()
        edit = base.add(Constraint("dialogue_forbidden", 0.0, ("dialogue",)))
        rd = region_delta(base, edit)
        self.assertAlmostEqual(rd.delta["dialogue"], -0.85, places=4)
        self.assertEqual(rd.before["dialogue"], POSSIBLE)
        self.assertEqual(rd.after["dialogue"], IMPOSSIBLE)

    def test_remove_to_unconstrained(self):
        base = _base()
        edit = base.remove("answer_withheld")  # dialogue loses its only cap
        rd = region_delta(base, edit)
        self.assertAlmostEqual(rd.delta["dialogue"], 0.15, places=4)  # 0.85 -> 1.0
        self.assertEqual(rd.after["dialogue"], UNCONSTRAINED)


class ConfidenceLayer(unittest.TestCase):
    def test_full_discrimination(self):
        conf = confidence_layer(reachable_region(_base()))
        self.assertEqual(conf["confidence"], 1.0)  # all 4 axes determined

    def test_unconstrained_lowers_confidence(self):
        conf = confidence_layer(reachable_region(_base().remove("answer_withheld")))
        self.assertEqual(conf["confidence"], 0.75)  # 3/4 determined

    def test_fail_closed_flags(self):
        conf = confidence_layer(reachable_region(_base()))
        self.assertFalse(conf["coupling"]["reality_coupled"])
        self.assertFalse(conf["coupling"]["wte_hte_coupled"])
        # the three uncomputed terms are deferred, NOT silently 1.0
        for term in ("evidence_strength", "wte_consistency", "hte_consistency"):
            self.assertIn("deferred", conf["terms"][term])


class EditorDiscipline(unittest.TestCase):
    def test_immutability(self):
        base = _base()
        before = base.constraints
        base.add(Constraint("x", 0.5, ("exploration",)))
        self.assertEqual(base.constraints, before)  # original untouched

    def test_knob_clamps(self):
        base = _base()
        self.assertEqual(base.weaken("enabling_safety", 5.0)._names()["enabling_safety"], 1.0)
        self.assertEqual(base.strengthen("enabling_safety", 5.0)._names()["enabling_safety"], 0.0)

    def test_unknown_axis_raises(self):
        with self.assertRaises(ValueError):
            ConstraintSet(axes=("a",), constraints=(Constraint("c", 0.5, ("ghost",)),))

    def test_duplicate_name_raises(self):
        with self.assertRaises(ValueError):
            ConstraintSet(axes=("a",), constraints=(
                Constraint("c", 0.5, ("a",)), Constraint("c", 0.3, ("a",))))

    def test_out_of_range_setting_raises(self):
        with self.assertRaises(ValueError):
            ConstraintSet(axes=("a",), constraints=(Constraint("c", 1.5, ("a",)),))

    def test_edit_missing_name_fail_closed(self):
        base = _base()
        for op in (lambda: base.remove("nope"),
                   lambda: base.set_value("nope", 0.5),
                   lambda: base.weaken("nope", 0.1),
                   lambda: base.strengthen("nope", 0.1)):
            with self.assertRaises(KeyError):
                op()


if __name__ == "__main__":
    unittest.main(verbosity=2)
