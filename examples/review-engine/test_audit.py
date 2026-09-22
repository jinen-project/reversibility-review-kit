"""
Regression lock for the IBE Audit Layer v0 (Phase 1.5).

Locks the priority/veto: No irrecoverable harm is ABOVE Flow.
  - new irreversible (P0) -> STOP, even if Flow recovers.
  - Lock-in / Reversibility closes room -> HOLD, even if Flow recovers (veto).
  - room recovers with nothing closing -> OK.
  - civilizational single-X dependence flagged from lock-in archetypes.

Run:  python3 engine/test_audit.py
"""
import unittest

from detector import Observation
from placement import Placement, simulate
from audit import audit, render, CIVILIZATIONAL_LOCKIN


def _baseline():
    return Observation(label="site", closing_present=("remove_margin_exit",),
                       resources_stuck=("relation",))


class Priority(unittest.TestCase):
    def test_p0_introduced_stops_even_with_flow_gain(self):
        # Flow recovers (unblock relation) BUT introduces irreversible erase -> STOP
        v = audit(simulate(_baseline(), Placement(
            label="C", add_closing=("erase_trace_r2_r3",), unblock_resources=("relation",))))
        self.assertEqual(v.decision, "STOP")
        self.assertIn("No irrecoverable harm", v.reason)

    def test_lockin_closes_holds_even_with_flow_gain(self):
        # Flow recovers BUT concentrates authority (lock-in closes) -> HOLD (veto over Flow)
        v = audit(simulate(_baseline(), Placement(
            label="B", add_closing=("concentrate_authority_no_recall",), unblock_resources=("relation",))))
        self.assertEqual(v.decision, "HOLD")
        self.assertIn("Flow より上位", v.reason)

    def test_reversibility_closes_holds(self):
        # introduce a non-P0 reversibility loss (finalize) -> HOLD
        v = audit(simulate(_baseline(), Placement(label="R", add_closing=("finalize_decision",))))
        self.assertEqual(v.decision, "HOLD")

    def test_room_recovers_is_ok(self):
        v = audit(simulate(_baseline(), Placement(
            label="A", add_reopening=("unhurried_felt_understood",), unblock_resources=("relation",))))
        self.assertEqual(v.decision, "OK")

    def test_unchanged_is_ok(self):
        v = audit(simulate(_baseline(), Placement(label="noop")))
        self.assertEqual(v.decision, "OK")

    def test_p0_takes_precedence_over_lockin(self):
        # both a new lock-in AND a new P0 -> STOP wins (No irrecoverable harm first)
        v = audit(simulate(_baseline(), Placement(
            label="X", add_closing=("erase_trace_r2_r3", "fix_single_axis"))))
        self.assertEqual(v.decision, "STOP")


class Civilizational(unittest.TestCase):
    def test_single_authority_flag(self):
        v = audit(simulate(_baseline(), Placement(
            label="B", add_closing=("concentrate_authority_no_recall",))))
        self.assertTrue(any("single-authority" in f for f in v.civilizational_flags))

    def test_vocabulary_maps_lockin_archetypes(self):
        self.assertEqual(set(CIVILIZATIONAL_LOCKIN),
                         {"concentrate_authority_no_recall", "fix_single_axis", "remove_margin_exit"})

    def test_render_shows_order_and_veto(self):
        text = render(audit(simulate(_baseline(), Placement(
            label="C", add_closing=("erase_trace_r2_r3",)))))
        self.assertIn("No irrecoverable harm が最上位", text)
        self.assertIn("最終は HA", text)
        self.assertIn("verdict: STOP", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
