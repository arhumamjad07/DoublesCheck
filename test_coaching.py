"""Offline regression tests. No services, keys or AI usage required."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from coaching import Trace, evidence_for, run_workflow, validate_proposal

CATALOGUE = [dict(name=name, type_primary=a, type_secondary=b, demo_role="mock")
             for name, a, b in [("Charizard", "Fire", "Flying"),
                                ("Venusaur", "Grass", "Poison"),
                                ("Blastoise", "Water", "None")]]


def proposal(teammate="Blastoise", favourite="Charizard"):
    facts = evidence_for(CATALOGUE)
    return dict(locked_favourite=favourite, teammate=teammate,
                legality_status="not_verified", explanation="Type-only example.",
                trade_off="Shared Electric weakness remains.",
                beginner_guidance=["Review targeting and the missing team slots."],
                type_checks=[dict(pokemon=name, attack_type=attack, multiplier=value)
                             for name in (favourite, teammate)
                             for attack, value in facts[name].items()])


PASS = dict(verdict="pass", issues=[], summary="Supported within limited scope.")
REVISE = dict(verdict="revise", issues=["Unsupported advice."], summary="Revise explanation.")


class FakeClient:
    def __init__(self, results):
        self.results, self.calls, self.payloads = iter(results), 0, []

    def call(self, agent, instructions, payload):
        self.calls += 1
        self.payloads.append((agent, payload))
        return next(self.results)


class CoachingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.trace = Trace(self.temp.name, ["test-secret"])
        self.facts = evidence_for(CATALOGUE)

    def test_dual_type_multiplication(self):
        self.assertEqual(self.facts["Charizard"], {"Water": 2, "Electric": 2, "Rock": 4})
        self.assertEqual(self.facts["Venusaur"], {"Water": .5, "Electric": .5, "Rock": 1})
        self.assertEqual(self.facts["Blastoise"], {"Water": .5, "Electric": 2, "Rock": 1})

    def test_no_unknown_type_silent_neutral(self):
        bad = copy.deepcopy(CATALOGUE)
        bad[0]["type_secondary"] = "Unknown"
        with self.assertRaises(RuntimeError):
            evidence_for(bad)

    def test_false_resistance_is_rejected(self):
        draft = proposal()
        claim = next(c for c in draft["type_checks"] if c["pokemon"] == "Blastoise" and c["attack_type"] == "Electric")
        claim["multiplier"] = .5
        self.assertTrue(any("Incorrect Electric" in error for error in validate_proposal(draft, "Charizard", self.facts)))

    def test_missing_claims_rejected(self):
        draft = proposal()
        draft["type_checks"].pop()
        self.assertTrue(validate_proposal(draft, "Charizard", self.facts))

    def test_duplicate_claims_rejected(self):
        draft = proposal()
        draft["type_checks"].append(draft["type_checks"][0])
        self.assertIn("Duplicate type check.", validate_proposal(draft, "Charizard", self.facts))

    def test_locked_favourite_cannot_change(self):
        draft = proposal()
        draft["locked_favourite"] = "Venusaur"
        self.assertTrue(validate_proposal(draft, "Charizard", self.facts))

    def test_unverified_legality_cannot_become_legal(self):
        draft = proposal()
        draft["legality_status"] = "legal"
        self.assertTrue(validate_proposal(draft, "Charizard", self.facts))

    def test_outside_catalogue_and_malformed_fields_rejected(self):
        for value in ("Pikachu", "Charizard", [], None):
            draft = proposal()
            draft["teammate"] = value
            self.assertTrue(validate_proposal(draft, "Charizard", self.facts))

    def test_separate_calls_on_happy_path(self):
        client = FakeClient([proposal(), PASS])
        result = run_workflow(client, CATALOGUE, "Charizard", self.trace)
        self.assertEqual(client.calls, 2)
        self.assertEqual([p[0] for p in client.payloads], ["Builder", "Evaluator"])
        self.assertEqual(result["revision_count"], 0)

    def test_freeform_interception_advice_replaced_before_review(self):
        draft = proposal()
        draft["beginner_guidance"] = ["Blastoise intercepts Electric attacks aimed at Charizard."]
        client = FakeClient([draft, PASS])
        result = run_workflow(client, CATALOGUE, "Charizard", self.trace)
        guide = result["proposal"]["beginner_guidance"]
        self.assertIn("Charizard's type multiplier is 2x and Blastoise's is 2x", guide[1])
        self.assertNotIn("Blastoise intercepts", " ".join(guide))
        self.assertEqual(client.payloads[1][1]["proposal"]["beginner_guidance"], guide)

    def test_real_critique_passed_to_revision(self):
        client = FakeClient([proposal(), REVISE, proposal("Venusaur"), PASS])
        result = run_workflow(client, CATALOGUE, "Charizard", self.trace)
        self.assertEqual(result["revision_count"], 1)
        self.assertEqual(client.calls, 4)
        self.assertIn("Unsupported advice.", client.payloads[2][1]["critique"])
        self.assertEqual(result["proposal"]["teammate"], "Venusaur")

    def test_contradictory_model_prose_is_replaced_with_computed_explanation(self):
        draft = proposal("Venusaur")
        draft["trade_off"] = "Charizard is neutral to Electric."
        draft["explanation"] = "Venusaur protects Charizard automatically."
        client = FakeClient([draft, PASS])
        result = run_workflow(client, CATALOGUE, "Charizard", self.trace)
        checked = result["proposal"]
        self.assertIn("Electric: Charizard 2x, Venusaur 0.5x", checked["explanation"])
        self.assertIn("Electric (2x)", checked["trade_off"])
        self.assertNotIn("neutral to Electric", checked["trade_off"])
        self.assertEqual(client.payloads[1][1]["proposal"], checked)

    def test_ai_cannot_override_mechanical_rejection(self):
        bad = proposal()
        bad["legality_status"] = "legal"
        client = FakeClient([bad, PASS, bad, PASS])
        with self.assertRaises(RuntimeError):
            run_workflow(client, CATALOGUE, "Charizard", self.trace)
        self.assertEqual(client.calls, 4)

    def test_failed_review_never_published(self):
        client = FakeClient([proposal(), REVISE, proposal(), REVISE])
        with self.assertRaises(RuntimeError):
            run_workflow(client, CATALOGUE, "Charizard", self.trace)
        self.assertEqual(client.calls, 4)

    def test_different_favourite_is_preserved(self):
        client = FakeClient([proposal("Charizard", "Blastoise"), PASS])
        result = run_workflow(client, CATALOGUE, "Blastoise", self.trace)
        self.assertEqual(result["proposal"]["locked_favourite"], "Blastoise")

    def test_malformed_evaluator_rejected(self):
        client = FakeClient([proposal(), dict(verdict="pass", issues="none")])
        with self.assertRaises(RuntimeError):
            run_workflow(client, CATALOGUE, "Charizard", self.trace)

    def test_trace_redacts_and_records_events(self):
        self.trace.event("Evaluator", "revision_requested", issues=["test-secret"])
        text = Path(self.trace.path).read_text(encoding="utf-8")
        self.assertNotIn("test-secret", text)
        self.assertIn("[REDACTED]", text)
        self.assertIn(self.trace.run_id, text)


if __name__ == "__main__":
    unittest.main()
