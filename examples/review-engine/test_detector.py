"""
Regression lock for the IBE Flow & Reversibility Detector v0.2 (Phase-1, three layers).

Locks: 6 closing / 7 reopening / 6 resource presets; STAGE classification
(lock-in / reversibility-loss / irreversible-p0); three-layer partition; lock-in
degrades 境界/余白/媒介; No-irrecoverable-harm-first ordering (Lock-in -> Reversibility
[P0 first] -> Flow); counter-move relevance; reverse-coverage invariants; fail-closed.

Run:  python3 engine/test_detector.py
"""
import unittest

from detector import (
    Observation, detect, priority_reading, render,
    CLOSING_ARCHETYPES, REOPENING_ARCHETYPES, COUNTER_MOVE, STAGE, LOCKIN_DEGRADES, FLOW_RESOURCES,
)


class Presets(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(CLOSING_ARCHETYPES), 6)
        self.assertEqual(len(REOPENING_ARCHETYPES), 7)
        self.assertEqual(len(FLOW_RESOURCES), 6)

    def test_reverse_coverage_invariants(self):
        # the module-load asserts, re-locked as tests (deleting an entry must fail loud)
        self.assertEqual(set(COUNTER_MOVE), set(CLOSING_ARCHETYPES))
        self.assertEqual(set(STAGE), set(CLOSING_ARCHETYPES))
        self.assertEqual(set(LOCKIN_DEGRADES), {a for a, s in STAGE.items() if s == "lock-in"})
        self.assertTrue(all(v in REOPENING_ARCHETYPES for v in COUNTER_MOVE.values()))

    def test_stage_classification(self):
        self.assertEqual(STAGE["remove_margin_exit"], "lock-in")
        self.assertEqual(STAGE["fix_single_axis"], "lock-in")
        self.assertEqual(STAGE["concentrate_authority_no_recall"], "lock-in")
        self.assertEqual(STAGE["essentialize_person"], "reversibility-loss")
        self.assertEqual(STAGE["finalize_decision"], "reversibility-loss")
        self.assertEqual(STAGE["erase_trace_r2_r3"], "irreversible")  # HARP P0


class ThreeLayers(unittest.TestCase):
    def test_partition_into_three_layers(self):
        d = detect(Observation(
            label="x",
            closing_present=("remove_margin_exit", "finalize_decision", "erase_trace_r2_r3"),
            resources_stuck=("relation",)))
        self.assertEqual([c.archetype for c in d.lockin_candidates], ["remove_margin_exit"])
        self.assertEqual({c.archetype for c in d.reversibility_candidates},
                         {"finalize_decision", "erase_trace_r2_r3"})
        self.assertEqual([f.resource for f in d.flow_candidates], ["relation"])

    def test_lockin_degrades_boundary_margin_mediation(self):
        d = detect(Observation(label="x", closing_present=(
            "remove_margin_exit", "fix_single_axis", "concentrate_authority_no_recall")))
        deg = {c.archetype: c.degrades for c in d.lockin_candidates}
        self.assertEqual(deg, {"remove_margin_exit": "余白", "fix_single_axis": "境界",
                               "concentrate_authority_no_recall": "媒介"})

    def test_p0_severity_and_reversibility_order(self):
        d = detect(Observation(
            label="x",
            closing_present=("finalize_decision", "erase_trace_r2_r3"),
            reopening_present=("provisional_plus_return_condition",)))
        by = {c.archetype: c for c in d.reversibility_candidates}
        self.assertEqual(by["erase_trace_r2_r3"].severity, "irreversible-p0")
        self.assertEqual(by["finalize_decision"].severity, "reversibility-loss")
        self.assertTrue(by["finalize_decision"].counter_present)
        self.assertFalse(by["erase_trace_r2_r3"].counter_present)
        # within reversibility, P0 sorts first
        self.assertEqual(d.reversibility_candidates[0].archetype, "erase_trace_r2_r3")

    def test_monitoring_order_lockin_then_rev_then_flow(self):
        pr = priority_reading(detect(Observation(
            label="x",
            closing_present=("remove_margin_exit", "finalize_decision", "erase_trace_r2_r3"),
            resources_stuck=("time",))))
        self.assertTrue(pr[0].startswith("[1 不可逆化の予兆"))   # lock-in first
        self.assertTrue(pr[1].startswith("[2 戻れるか · ⚠P0"))   # P0 alarm next
        self.assertTrue(pr[-1].startswith("[3 流れるか"))        # flow last

    def test_all_six_closing_at_once(self):
        d = detect(Observation(label="x", closing_present=tuple(CLOSING_ARCHETYPES)))
        self.assertEqual(len(d.lockin_candidates), 3)          # 3 lock-in stage
        self.assertEqual(len(d.reversibility_candidates), 3)   # 2 rev-loss + 1 p0
        self.assertEqual(sum(c.severity == "irreversible-p0" for c in d.reversibility_candidates), 1)


class CounterMoveRelevance(unittest.TestCase):
    def test_irrelevant_counter_move_not_recognized(self):
        # finalize_decision's counter is provisional_plus_return_condition; an
        # unrelated reopening must NOT count as the counter-move.
        d = detect(Observation(
            label="x", closing_present=("finalize_decision",),
            reopening_present=("archive_instead_of_erase",)))  # wrong pair
        self.assertFalse(d.reversibility_candidates[0].counter_present)

    def test_relevant_counter_move_recognized(self):
        d = detect(Observation(
            label="x", closing_present=("finalize_decision",),
            reopening_present=("provisional_plus_return_condition",)))
        self.assertTrue(d.reversibility_candidates[0].counter_present)


class Discipline(unittest.TestCase):
    def test_empty_observation(self):
        d = detect(Observation(label="empty"))
        self.assertEqual((d.lockin_candidates, d.reversibility_candidates, d.flow_candidates), ((), (), ()))
        self.assertIn("候補なし", priority_reading(d)[0])

    def test_candidate_language_hedged(self):
        d = detect(Observation(label="x", closing_present=("remove_margin_exit", "finalize_decision"),
                               resources_stuck=("money",)))
        self.assertIn("かもしれない", d.lockin_candidates[0].note)
        self.assertIn("かもしれない", d.reversibility_candidates[0].note)
        self.assertIn("かもしれない", d.flow_candidates[0].note)
        self.assertIn("not a world model", render(d))

    def test_render_has_three_sections(self):
        text = render(detect(Observation(label="x", closing_present=tuple(CLOSING_ARCHETYPES),
                                          resources_stuck=("trust",))))
        for token in ("[1] Lock-in Candidates", "[2] Reversibility Candidates",
                      "[3] Flow Candidates", "No irrecoverable harm が最初の監視項目"):
            self.assertIn(token, text)


class FailClosed(unittest.TestCase):
    def test_unknown_closing_raises(self):
        with self.assertRaises(ValueError):
            detect(Observation(label="x", closing_present=("ghost",)))

    def test_unknown_reopening_raises(self):
        with self.assertRaises(ValueError):
            detect(Observation(label="x", reopening_present=("ghost",)))

    def test_unknown_resource_raises(self):
        with self.assertRaises(ValueError):
            detect(Observation(label="x", resources_stuck=("oxygen",)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
