"""
Regression lock for the IBE Placement Simulator v0 (pre-placement audit).

Locks: apply_placement merge (add/remove closing/reopening, unblock/block flow);
open-load delta per axis (counter-move resolves reversibility; unblock resolves
flow; new closing/block closes room); preserves_room verdict (yes/no/mixed/
unchanged); baseline immutability; candidates-not-prediction.

Run:  python3 engine/test_placement.py
"""
import unittest

from detector import Observation, detect
from placement import Placement, apply_placement, simulate, render


def _baseline():
    return Observation(
        label="site",
        closing_present=("remove_margin_exit", "erase_trace_r2_r3"),
        resources_stuck=("relation",))


class ApplyPlacement(unittest.TestCase):
    def test_merge_add_remove(self):
        obs = _baseline()
        p = Placement(label="p",
                      add_closing=("finalize_decision",), remove_closing=("remove_margin_exit",),
                      add_reopening=("archive_instead_of_erase",),
                      unblock_resources=("relation",), block_resources=("attention",))
        after = apply_placement(obs, p)
        self.assertEqual(set(after.closing_present), {"erase_trace_r2_r3", "finalize_decision"})
        self.assertEqual(set(after.reopening_present), {"archive_instead_of_erase"})
        self.assertEqual(set(after.resources_stuck), {"attention"})  # relation unblocked, attention blocked

    def test_baseline_not_mutated(self):
        obs = _baseline()
        before = (obs.closing_present, obs.reopening_present, obs.resources_stuck)
        apply_placement(obs, Placement(label="p", add_closing=("finalize_decision",)))
        self.assertEqual((obs.closing_present, obs.reopening_present, obs.resources_stuck), before)


class Simulate(unittest.TestCase):
    def test_placement_that_preserves_room(self):
        # add the counter-moves for both closings + unblock the stuck flow
        a = Placement(label="A",
                      add_reopening=("archive_instead_of_erase", "unhurried_felt_understood"),
                      unblock_resources=("relation",))
        audit = simulate(_baseline(), a)
        self.assertEqual(audit.lock_in.before, 1); self.assertEqual(audit.lock_in.after, 0)
        self.assertEqual(audit.reversibility.before, 1); self.assertEqual(audit.reversibility.after, 0)
        self.assertEqual(audit.flow.before, 1); self.assertEqual(audit.flow.after, 0)
        self.assertEqual(audit.preserves_room, "yes")
        self.assertIn("erase_trace_r2_r3", audit.reversibility.disappeared)

    def test_placement_that_closes_room(self):
        b = Placement(label="B",
                      add_closing=("concentrate_authority_no_recall",),
                      block_resources=("attention",))
        audit = simulate(_baseline(), b)
        self.assertEqual(audit.lock_in.direction, "closes room")
        self.assertIn("concentrate_authority_no_recall", audit.lock_in.appeared)
        self.assertEqual(audit.flow.direction, "closes room")
        self.assertEqual(audit.preserves_room, "no")

    def test_mixed_placement(self):
        # resolve reversibility (archive) but introduce a new lock-in
        m = Placement(label="M",
                      add_reopening=("archive_instead_of_erase",),
                      add_closing=("fix_single_axis",))
        audit = simulate(_baseline(), m)
        self.assertEqual(audit.reversibility.direction, "recovers room")
        self.assertEqual(audit.lock_in.direction, "closes room")
        self.assertEqual(audit.preserves_room, "mixed")

    def test_empty_placement_unchanged(self):
        audit = simulate(_baseline(), Placement(label="noop"))
        self.assertEqual(audit.preserves_room, "unchanged")
        for ad in (audit.lock_in, audit.reversibility, audit.flow):
            self.assertEqual(ad.direction, "unchanged")

    def test_counter_move_resolves_open_reversibility(self):
        # erase_trace_r2_r3 open (no counter) -> add archive -> no longer open
        audit = simulate(_baseline(), Placement(label="C",
                         add_reopening=("archive_instead_of_erase",)))
        self.assertIn("erase_trace_r2_r3", audit.reversibility.disappeared)
        self.assertEqual(audit.reversibility.after, 0)

    def test_render_is_audit_not_prediction(self):
        text = render(simulate(_baseline(), Placement(label="A",
                      add_reopening=("archive_instead_of_erase",))))
        self.assertIn("not a prediction", text)
        self.assertIn("range-of-motion", text)
        self.assertIn("最終は HA", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
