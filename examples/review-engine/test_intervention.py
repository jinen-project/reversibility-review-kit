"""
Regression lock for the IBE Governance Intervention / Reopening Engine v0.

Locks: intervene returns reopening moves for each unmitigated risk (mapped to
境界/余白/媒介); the detect -> intervene -> re-audit loop mitigates concentration;
P0 erase -> archive intervention; to_placement builds the recovery placement;
no interventions when nothing is unmitigated.

Run:  python3 engine/test_intervention.py
"""
import unittest

from detector import Observation
from placement import Placement
from governance import accumulate, govern
from intervention import intervene, to_placement, render, INTERVENTION


def _concentrated():
    return accumulate(Observation(label="site"), (
        Placement(label="p1", add_closing=("fix_single_axis",)),
        Placement(label="p2", add_closing=("concentrate_authority_no_recall",)),
        Placement(label="p3", add_closing=("remove_margin_exit",))))


class Intervene(unittest.TestCase):
    def test_returns_interventions_per_unmitigated_risk(self):
        ivs = intervene(govern(_concentrated()))
        names = {iv.risk for iv in ivs}
        self.assertIn("single-interpretation", names)
        self.assertIn("single-axis", names)
        self.assertIn("no-exit", names)
        # each restores boundary/margin/mediation and proposes reopening moves
        for iv in ivs:
            self.assertTrue(iv.reopening)
            self.assertTrue(any(x in iv.restores for x in ("境界", "余白", "媒介")))

    def test_no_intervention_when_clean(self):
        self.assertEqual(intervene(govern(Observation(label="empty"))), ())

    def test_p0_erase_gets_archive_intervention(self):
        v = govern(accumulate(Observation(label="x"), (
            Placement(label="p", add_closing=("erase_trace_r2_r3",)),)))
        ivs = intervene(v)
        p0 = [iv for iv in ivs if iv.risk == "irreversible-p0"]
        self.assertEqual(len(p0), 1)
        self.assertIn("archive_instead_of_erase", p0[0].reopening)


class DetectRecoverLoop(unittest.TestCase):
    def test_intervention_mitigates_concentration(self):
        config = _concentrated()
        before = govern(config)
        self.assertEqual(before.recommended, "縮退")
        ivs = intervene(before)
        recovered = accumulate(config, (to_placement(ivs, "recovery"),))
        after = govern(recovered)
        self.assertEqual(after.recommended, "採用")
        self.assertEqual(sum(1 for r in after.risks if r.present and not r.mitigated), 0)

    def test_to_placement_adds_reopening_moves(self):
        ivs = intervene(govern(_concentrated()))
        p = to_placement(ivs)
        self.assertIn("keep_both_views_mediation", p.add_reopening)
        self.assertIn("unhurried_felt_understood", p.add_reopening)
        self.assertEqual(p.add_closing, ())  # intervention only ADDS reopenings


class Mapping(unittest.TestCase):
    def test_intervention_covers_concentration_risks(self):
        self.assertEqual(set(INTERVENTION),
                         {"single-interpretation", "single-axis", "no-exit", "single-resource"})

    def test_render_frames_recovery(self):
        text = render(intervene(govern(_concentrated())))
        self.assertIn("危険を減らすために何を足すか", text)
        self.assertIn("最終は HA", text)
        self.assertIn("reopening:", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
