"""GUI progress represents actual trace events and never leaks raw details."""
import json
from pathlib import Path
import tempfile
import unittest
from project_status import dashboard, progress, RUBRIC
from team import Trace

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_id = "a" * 32

    def trace(self):
        return Trace(self.root / "runs", self.run_id)

    def test_missing_run_waits_without_fabricated_events(self):
        self.assertEqual(progress(self.run_id, self.root)["events"], [])
        self.assertEqual(progress(self.run_id, self.root)["status"], "waiting")

    def test_progress_reports_real_events_but_omits_sensitive_details(self):
        trace = self.trace()
        trace.event("H-MEM", "preferences_recalled", secret="do-not-display")
        trace.event("Builder", "candidate_slot_filled", slots=4)
        result = progress(self.run_id, self.root)
        self.assertEqual(result["status"], "running")
        self.assertEqual(len(result["events"]), 2)
        self.assertIn("slot 4", result["events"][-1]["label"])
        self.assertNotIn("do-not-display", json.dumps(result))

    def test_incomplete_last_line_is_safe_while_building(self):
        trace = self.trace()
        trace.event("DataRetriever", "catalogue_loaded")
        with (trace.directory / "trace.jsonl").open("a") as handle: handle.write('{"action":')
        self.assertEqual(len(progress(self.run_id, self.root)["events"]), 1)

    def test_success_and_failure_follow_terminal_events(self):
        trace = self.trace()
        trace.event("Orchestrator", "report_approved")
        self.assertEqual(progress(self.run_id, self.root)["status"], "complete")
        trace.event("Orchestrator", "run_failed")
        self.assertEqual(progress(self.run_id, self.root)["status"], "failed")

    def test_invalid_identifiers_and_reusing_runs_rejected(self):
        for value in ["../outside", None, "<script>"]:
            with self.assertRaises(ValueError): progress(value, self.root)
        self.trace()
        with self.assertRaises(ValueError): self.trace()

    def test_dashboard_does_not_claim_ai_or_all_features_complete(self):
        page = dashboard(self.root)
        self.assertIn("Model calls off", page)
        self.assertIn("Nightshift AI integration remains unfinished", page)
        self.assertEqual(sum(row[1] for row in RUBRIC), 100)
        self.assertIn("not awarded or predicted scores", page)

if __name__ == "__main__": unittest.main()
