"""Real H-MEM persistence and workflow tests; no network or model usage."""
import json
import tempfile
import unittest
from pathlib import Path

from coaching import Trace, run_workflow
from hmem_memory import recall_preferences
from test_coaching import CATALOGUE, FakeClient, PASS, proposal


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def recall(self, profile="alice", updates=None):
        # Every call launches a fresh Node process using the actual engine.
        return recall_preferences(self.root / "memory", profile, updates)

    def state(self):
        return json.loads((self.root / "memory/alice/state.json").read_text())

    def seed(self):
        return self.recall(updates={"favourite": "Charizard", "avoided_partner": "Blastoise"})

    def test_fresh_process_recalls_saved_preferences_and_provenance(self):
        written = self.seed()
        recalled = self.recall()
        self.assertEqual(recalled["favourite"], "Charizard")
        self.assertEqual(recalled["avoided_partner"], "Blastoise")
        self.assertEqual([m["id"] for m in written["memories"]],
                         [m["id"] for m in recalled["memories"]])
        self.assertTrue(all(m["source"] == "user_explicit" for m in recalled["memories"]))
        self.assertTrue(all(m["score"] >= .35 for m in recalled["memories"]))
        self.assertIn("[MEMORY CONTEXT]", recalled["context"])
        self.assertTrue(all(r["accessCount"] >= 2 for r in self.state()["records"]))

    def test_profiles_are_isolated(self):
        self.seed()
        other = self.recall("bob")
        self.assertEqual(other["memories"], [])
        self.assertNotIn("favourite", other)
        self.assertNotIn("avoided_partner", other)

    def test_correction_retains_history_but_reinjects_only_current_value(self):
        self.seed()
        corrected = self.recall(updates={"favourite": "Venusaur"})
        self.assertEqual(corrected["favourite"], "Venusaur")
        self.assertEqual(corrected["avoided_partner"], "Blastoise")
        self.assertNotIn("My favourite Pokemon is Charizard", corrected["context"])
        records = self.state()["records"]
        old = next(r for r in records if r["content"] == "My favourite Pokemon is Charizard")
        new = next(r for r in records if r["content"] == "My favourite Pokemon is Venusaur")
        self.assertEqual(old["supersededBy"], new["id"])
        self.assertEqual(new["provenance"]["origin"], "user_correction")

    def test_repeating_explicit_preference_does_not_duplicate(self):
        self.seed()
        self.seed()
        self.assertEqual(len(self.state()["records"]), 2)

    def test_explicit_clear_removes_constraint_and_audits_reason(self):
        self.seed()
        self.recall(updates={"avoided_partner": None})
        recalled = self.recall()
        self.assertNotIn("avoided_partner", recalled)
        self.assertEqual(recalled["favourite"], "Charizard")
        self.assertNotIn("Avoid partner", recalled["context"])
        ledger = (self.root / "memory/alice/ledger.jsonl").read_text()
        self.assertIn("User explicitly cleared partner avoidance", ledger)

    def test_busy_profile_fails_without_removing_another_process_lock(self):
        self.seed()
        lock = self.root / "memory/alice/bridge.lock"
        lock.write_text("another process")
        with self.assertRaises(RuntimeError):
            self.recall()
        self.assertTrue(lock.exists())

    def test_profile_cannot_escape_memory_directory(self):
        with self.assertRaises(ValueError):
            self.recall("../outside")

    def test_recalled_constraint_reaches_both_roles_and_blocks_false_approval(self):
        self.seed()
        memory = self.recall()  # No repeated preferences in this fresh process.
        client = FakeClient([proposal("Blastoise"), PASS, proposal("Venusaur"), PASS])
        result = run_workflow(client, CATALOGUE, memory["favourite"],
                              Trace(self.root / "logs"), memory=memory)
        self.assertEqual(result["proposal"]["teammate"], "Venusaur")
        self.assertEqual(result["revision_count"], 1)
        self.assertEqual(result["memory_used"]["avoided_partner"], "Blastoise")
        for role, payload in client.payloads:
            self.assertEqual(payload["eligible_partners"], ["Venusaur"])
            self.assertIn("Avoid partner Blastoise", payload["memory_context"])
        self.assertTrue(client.payloads[1][1]["deterministic_errors"])

    def test_constraint_cannot_be_overridden_after_revision_limit(self):
        memory = self.seed()
        client = FakeClient([proposal("Blastoise"), PASS, proposal("Blastoise"), PASS])
        with self.assertRaises(RuntimeError):
            run_workflow(client, CATALOGUE, "Charizard", Trace(self.root / "logs"), memory=memory)
        self.assertEqual(client.calls, 4)


if __name__ == "__main__":
    unittest.main()
