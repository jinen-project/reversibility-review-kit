"""
Regression lock for the IBE Governance Layer v0.

Locks: accumulate (sequence of placements -> cumulative config); cumulative
concentration that LOCAL audits would miss; mitigation by left counters;
extended decision options (縮退/分散/実験 beyond 採用/保留/棄却); No-irrecoverable-harm
top constraint (archive-less erase -> 棄却); range-of-motion properties.

Run:  python3 engine/test_governance.py
"""
import unittest

from detector import Observation
from placement import Placement
from governance import accumulate, govern, render, DECISION_OPTIONS


def _base():
    return Observation(label="site")


class Accumulate(unittest.TestCase):
    def test_sequence_accumulates(self):
        obs = accumulate(_base(), (
            Placement(label="p1", add_closing=("fix_single_axis",)),
            Placement(label="p2", add_closing=("concentrate_authority_no_recall",))))
        self.assertEqual(set(obs.closing_present), {"fix_single_axis", "concentrate_authority_no_recall"})


class Govern(unittest.TestCase):
    def test_cumulative_concentration_recommends_degrade(self):
        # three closings, no counters -> cumulative concentration (local audits could pass each)
        obs = accumulate(_base(), (
            Placement(label="p1", add_closing=("fix_single_axis",)),
            Placement(label="p2", add_closing=("concentrate_authority_no_recall",)),
            Placement(label="p3", add_closing=("remove_margin_exit",))))
        v = govern(obs)
        self.assertEqual(v.recommended, "縮退")
        unmit = [r for r in v.risks if r.present and not r.mitigated]
        self.assertGreaterEqual(len(unmit), 2)

    def test_counters_left_keeps_room_adopt(self):
        # same closings but each leaves its counter -> mitigated -> adopt
        obs = accumulate(_base(), (
            Placement(label="q1", add_closing=("fix_single_axis",), add_reopening=("keep_both_views_mediation",)),
            Placement(label="q2", add_closing=("concentrate_authority_no_recall",), add_reopening=("keep_parallel_paths",)),
            Placement(label="q3", add_closing=("remove_margin_exit",), add_reopening=("unhurried_felt_understood",))))
        v = govern(obs)
        self.assertEqual(v.recommended, "採用")
        self.assertTrue(all(p.held for p in v.properties))

    def test_single_concentration_recommends_distribute(self):
        v = govern(accumulate(_base(), (Placement(label="p", add_closing=("concentrate_authority_no_recall",)),)))
        self.assertEqual(v.recommended, "分散")

    def test_irrecoverable_erase_recommends_reject(self):
        v = govern(accumulate(_base(), (Placement(label="p", add_closing=("erase_trace_r2_r3",)),)))
        self.assertEqual(v.recommended, "棄却")
        self.assertIn("不可逆", v.no_irrecoverable_harm)

    def test_archive_left_is_not_irrecoverable(self):
        v = govern(accumulate(_base(), (
            Placement(label="p", add_closing=("erase_trace_r2_r3",), add_reopening=("archive_instead_of_erase",)),)))
        self.assertNotEqual(v.recommended, "棄却")  # archive left -> recoverable

    def test_empty_config_adopt(self):
        self.assertEqual(govern(_base()).recommended, "採用")


class Options(unittest.TestCase):
    def test_six_decision_options(self):
        self.assertEqual(DECISION_OPTIONS, ("採用", "保留", "棄却", "縮退", "分散", "実験"))

    def test_render_shows_options_and_top_constraint(self):
        text = render(govern(accumulate(_base(), (Placement(label="p", add_closing=("erase_trace_r2_r3",)),))))
        self.assertIn("縮退", text)
        self.assertIn("No irrecoverable harm（最上位制約）", text)
        self.assertIn("最終は HA", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
