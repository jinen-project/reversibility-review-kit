"""
Regression lock for IBE Domain Profile / Profile Translation (Runtime Spec §7 #1).

Locks: DomainProfile validation (fail-closed on unknown target); translate renames
domain terms -> abstract grammar ids; identity fallback (already-abstract passes
through); abstract profile is identity; a domain-term placement, once translated,
runs through the Engine to the same verdict as its abstract equivalent.

Run:  python3 engine/test_profiles.py
"""
import unittest

from detector import Observation
from placement import Placement
from decision_context import DecisionContext
from runtime import run_cycle
from profiles import DomainProfile, ABSTRACT_PROFILE, translate, CHILDCARE_PROFILE_DEMO


class ProfileSchema(unittest.TestCase):
    def test_unknown_closing_target_raises(self):
        with self.assertRaises(ValueError):
            DomainProfile("p", "d", closing_map={"x": "not_an_archetype"})

    def test_unknown_resource_target_raises(self):
        with self.assertRaises(ValueError):
            DomainProfile("p", "d", resource_map={"x": "oxygen"})

    def test_abstract_profile_is_identity(self):
        self.assertEqual(ABSTRACT_PROFILE.closing_map, {})
        # identity: an already-abstract id passes through unchanged
        p = translate(ABSTRACT_PROFILE, Placement(label="x", add_closing=("erase_trace_r2_r3",)))
        self.assertEqual(p.add_closing, ("erase_trace_r2_r3",))


class Translate(unittest.TestCase):
    def test_domain_terms_become_abstract_ids(self):
        dp = Placement(label="観察記録を破棄",
                       add_closing=("観察記録を破棄",), unblock_resources=("信頼",))
        ap = translate(CHILDCARE_PROFILE_DEMO, dp)
        self.assertEqual(ap.add_closing, ("erase_trace_r2_r3",))
        self.assertEqual(ap.unblock_resources, ("trust",))
        self.assertIn("[保育]", ap.label)

    def test_identity_fallback_for_unmapped_term(self):
        # a term not in the map passes through unchanged (already-abstract)
        ap = translate(CHILDCARE_PROFILE_DEMO, Placement(label="x", add_closing=("fix_single_axis",)))
        self.assertEqual(ap.add_closing, ("fix_single_axis",))

    def test_translated_placement_matches_abstract_verdict(self):
        # the domain-term placement, translated, yields the same verdict as the abstract one
        ctx = DecisionContext(protect=("reversibility",), increase=("flow",), avoid=("lock-in",))
        base = Observation(label="保育園", resources_stuck=("trust",))
        domain = run_cycle(ctx, base, translate(CHILDCARE_PROFILE_DEMO,
                           Placement(label="観察記録を破棄", add_closing=("観察記録を破棄",))))
        abstract = run_cycle(ctx, base, Placement(label="erase", add_closing=("erase_trace_r2_r3",)))
        self.assertEqual(domain.placement_audit, abstract.placement_audit)   # both STOP
        self.assertTrue(domain.placement_audit.startswith("STOP"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
