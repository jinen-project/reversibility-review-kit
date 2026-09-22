"""
Regression lock for the IBE Maneuverability Observatory v0 (the top index).

Locks: maneuverability(config) bundles range-of-motion / concentration / P0 into
one comparable level; observe(trajectory) reports trend + first decline; the
falling-only alarm (momentary dip that recovers is NOT alarmed); P0 penalty.

Run:  python3 engine/test_maneuverability.py
"""
import unittest

from detector import Observation
from placement import Placement
from maneuverability import maneuverability, observe, render


def _base():
    return Observation(label="site")


class Index(unittest.TestCase):
    def test_empty_config_is_maximally_maneuverable(self):
        m = maneuverability(_base())
        self.assertEqual(m.properties_held, 4)      # all range-of-motion properties held
        self.assertEqual(m.unmitigated_risks, 0)
        self.assertEqual(m.level, 4.0)

    def test_concentration_lowers_level(self):
        obs = Observation(label="x", closing_present=("fix_single_axis",))
        self.assertLess(maneuverability(obs).level, 4.0)

    def test_p0_open_penalizes(self):
        obs = Observation(label="x", closing_present=("erase_trace_r2_r3",))
        m = maneuverability(obs)
        self.assertTrue(m.p0_open)
        self.assertLessEqual(m.level, 1.0)          # held(3) - 0 - 2 = 1

    def test_counter_restores_level(self):
        capped = Observation(label="x", closing_present=("fix_single_axis",))
        countered = Observation(label="x", closing_present=("fix_single_axis",),
                                reopening_present=("keep_both_views_mediation", "keep_parallel_paths"))
        self.assertGreater(maneuverability(countered).level, maneuverability(capped).level)


class Observatory(unittest.TestCase):
    def test_accumulating_closures_fall(self):
        t = observe(_base(), (
            Placement(label="a", add_closing=("fix_single_axis",)),
            Placement(label="b", add_closing=("concentrate_authority_no_recall",)),
            Placement(label="c", add_closing=("remove_margin_exit",))))
        self.assertEqual(t.direction, "falling")
        self.assertLess(t.net, 0)
        self.assertEqual(t.first_decline_step, 1)   # erosion begins at step 1
        self.assertEqual(t.points[0].level, 4.0)
        self.assertLess(t.points[-1].level, 0.0)

    def test_counters_keep_room_flat_no_alarm(self):
        t = observe(_base(), (
            Placement(label="a", add_closing=("fix_single_axis",),
                      add_reopening=("keep_both_views_mediation", "keep_parallel_paths")),
            Placement(label="b", add_closing=("concentrate_authority_no_recall",),
                      add_reopening=("keep_parallel_paths",))))
        self.assertIn(t.direction, ("flat", "rising"))
        self.assertGreaterEqual(t.net, 0)
        # render must NOT raise the falling alarm for a non-falling trajectory
        self.assertNotIn("削られ始め", render(t))

    def test_render_alarms_only_on_falling(self):
        falling = observe(_base(), (Placement(label="a", add_closing=("remove_margin_exit",)),
                                    Placement(label="b", add_closing=("fix_single_axis",))))
        self.assertEqual(falling.direction, "falling")
        text = render(falling)
        self.assertIn("falling", text)
        self.assertIn("最終は HA", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
