"""
Regression lock for IBE Phase-1 Runtime v0.1 (③).

Locks the FIRST Runtime Test: a PACKET comes back (success != "placement adopted").
The Runtime returns an OBSERVATION packet, not an answer (no correctness verdict;
it does not decide — it surfaces HA's declared decision menu). Idempotent
(same input -> same packet). W|HA detection; No-irrecoverable-harm > Flow veto
visible in the packet; log record marked Phase-1-pseudo.

Run:  python3 engine/test_runtime.py
"""
import unittest

from decision_context import DecisionContext
from detector import Observation
from placement import Placement
from runtime import run_cycle, to_log_record, render, Packet, DECISION_MENU, ABSTRACT_PROFILE


def _ctx():
    return DecisionContext(protect=("reversibility",), increase=("flow",), avoid=("lock-in",))


def _baseline():
    return Observation(label="org", resources_stuck=("attention", "trust"))


def _placement():
    return Placement(label="集約的対話プロトコル",
                     add_closing=("concentrate_authority_no_recall",),
                     unblock_resources=("attention",))


class RuntimeTest(unittest.TestCase):
    def test_packet_comes_back(self):
        # the success condition: a packet is returned (not "placement adopted")
        p = run_cycle(_ctx(), _baseline(), _placement())
        self.assertIsInstance(p, Packet)
        # all packet fields populated
        self.assertTrue(p.detection and p.placement_audit and p.governance and p.fap)
        self.assertEqual(p.decision_menu, DECISION_MENU)
        self.assertEqual(p.profile_id, ABSTRACT_PROFILE.profile_id)

    def test_idempotent_same_input_same_packet(self):
        a = run_cycle(_ctx(), _baseline(), _placement())
        b = run_cycle(_ctx(), _baseline(), _placement())
        self.assertEqual(a, b)   # no wall-clock in the cycle

    def test_observation_not_answer(self):
        # the Runtime does not decide / judge correctness — it returns the menu, not a choice
        p = run_cycle(_ctx(), _baseline(), _placement())
        text = render(p)
        self.assertIn("observation, not an answer", text)
        self.assertIn("Runtime は判定しない", text)
        self.assertIn("最終は HA", text)
        # no "correct/正しい" verdict anywhere
        self.assertNotIn("正しい", text)

    def test_w_given_ha_detection_surfaces_avoided_axis(self):
        # HA avoids lock-in -> a lock-in detection item is tagged [avoid] and surfaces
        p = run_cycle(_ctx(), _baseline(), _placement())
        self.assertTrue(any(d.startswith("[avoid] (lock-in)") for d in p.detection))

    def test_no_irrecoverable_harm_over_flow_in_packet(self):
        # placement recovers flow (unblock attention) BUT introduces lock-in -> HOLD veto
        p = run_cycle(_ctx(), _baseline(), _placement())
        self.assertTrue(p.placement_audit.startswith("HOLD"))
        self.assertIn("Flow より上位", p.placement_audit)
        self.assertTrue(p.governance.startswith("分散"))
        self.assertTrue(p.interventions)               # recovery offered
        self.assertTrue(p.fap.startswith("falling"))   # FAP observed declining

    def test_log_record_is_phase1_pseudo(self):
        p = run_cycle(_ctx(), _baseline(), _placement())
        rec = to_log_record(p, placement_id="pl-0001", ts="t0")
        self.assertEqual(rec.execution_phase, "Phase-1-pseudo")
        self.assertEqual(rec.candidate_label, p.constraint_change)
        self.assertEqual(rec.audit_result, p.placement_audit)

    def test_clean_placement_is_ok(self):
        # a placement that only restores a return path -> OK, concentration なし
        p = run_cycle(_ctx(), _baseline(),
                      Placement(label="並走経路を足す", add_reopening=("keep_parallel_paths",)))
        self.assertTrue(p.placement_audit.startswith("OK"))
        self.assertIn("concentration なし", p.governance)


if __name__ == "__main__":
    unittest.main(verbosity=2)
