"""Explicit continuation retains reasoning state without repeating successful work."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from ai_coach import run_coach, CoachPaused, CoachSession
from catalogue import load_catalogue
from team_builder import build_team
from nightshift_client import CoachError
from test_ai_coach import Trace, ScriptedClient, approval
from test_reasoning_contracts import inspect


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = load_catalogue(True)
        cls.baseline, _, cls.locked = build_team(cls.data, ["Charizard"], ["Incineroar"])

    def make_client(self):
        return ScriptedClient([inspect, CoachError("Temporary upstream interruption", code="gateway_stream_error", retryable=True), approval])

    def start(self, client, trace):
        return run_coach(self.data, self.baseline, self.locked, ["Incineroar"],
                         {"favourite": "Charizard", "avoided_partner": "Incineroar"}, trace, client,
                         review_first=True, origin="simulated recovery evaluation")

    def test_transport_pause_sends_no_automatic_retry_and_keeps_completed_tools(self):
        trace, client = Trace(), self.make_client()
        with self.assertRaises(CoachPaused) as caught: self.start(client, trace)
        self.assertEqual(client.calls, 2)
        self.assertEqual(sum(e["action"] == "tool_executed" for e in trace.events), 1)
        _, check, result = caught.exception.session.advance()
        self.assertTrue(check["valid"])
        self.assertEqual(client.calls, 3)
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(sum(e["action"] == "tool_executed" for e in trace.events), 1)
        self.assertTrue(any(e["action"] == "review_resumed" for e in trace.events))

    def test_pause_does_not_reset_the_lifetime_request_budget(self):
        trace = Trace()
        client = ScriptedClient([inspect] + [{"verdict": "nonsense"}] * 6 + [CoachError("upstream", retryable=True)])
        with self.assertRaises(CoachError) as caught: self.start(client, trace)
        self.assertNotIsInstance(caught.exception, CoachPaused)
        self.assertEqual(client.calls, 8)
        self.assertFalse(any(e["action"] == "ai_approved" for e in trace.events))

    def test_human_wait_is_excluded_without_resetting_active_time(self):
        now = [5.0]; client, trace = self.make_client(), Trace()
        client.clock = lambda: now[0]; client.started = 0.0
        with self.assertRaises(CoachPaused) as caught: self.start(client, trace)
        now[0] = 10005.0
        caught.exception.session.advance()
        self.assertEqual(client.started, 10000.0)
        self.assertEqual(client.calls, 3)

    def test_concurrent_continuation_cannot_duplicate_requests(self):
        client, trace = self.make_client(), Trace()
        with self.assertRaises(CoachPaused) as caught: self.start(client, trace)
        session = caught.exception.session
        session.lock.acquire()
        try:
            with self.assertRaises(CoachError): session.advance()
            self.assertEqual(client.calls, 2)
        finally: session.lock.release()
        session.advance()
        with self.assertRaises(CoachError): session.advance()
        self.assertEqual(client.calls, 3)

    def test_application_continuation_does_not_requery_or_rebuild(self):
        import team
        from hmem_memory import recall_preferences
        client = self.make_client()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recall = lambda folder,profile,updates,**kw: recall_preferences(root/"memory", profile, updates, **kw)
            with patch("team.load_catalogue", return_value=(self.data,"simulated Zetaris recovery fixture")) as data_mock, \
                 patch("team.recall_preferences", side_effect=recall), patch("team.build_team", wraps=build_team) as builder:
                with self.assertRaises(CoachPaused) as caught:
                    team.execute(["Charizard"], avoided="Incineroar", output=root/"runs", profile="recover",
                                 ai=True, ai_client=client, allow_resume=True)
                run_id = caught.exception.run_id
                self.assertFalse(list((root/"runs").glob("*/report.html")))
                result, folder = team.resume_review(run_id)
                self.assertEqual(result["model_calls"], 3)
                self.assertTrue((folder/"report.html").exists())
                self.assertEqual(data_mock.call_count, 1)
                self.assertEqual(builder.call_count, 1)
                events = [json.loads(line) for line in (folder/"trace.jsonl").read_text().splitlines()]
                self.assertEqual(sum(e["action"] == "candidate_slot_filled" for e in events), 5)
                self.assertEqual(sum(e["action"] == "tool_executed" for e in events), 1)
                self.assertNotIn(run_id, team._PENDING_RUNS)
                with self.assertRaises(ValueError): team.resume_review(run_id)
                self.assertEqual(client.calls, 3)

    def test_changed_preferences_stop_continuation_before_another_model_call(self):
        import team
        from hmem_memory import recall_preferences
        client = self.make_client()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recall = lambda folder,profile,updates,**kw: recall_preferences(root/"memory", profile, updates, **kw)
            with patch("team.load_catalogue", return_value=(self.data,"simulated Zetaris fixture")), patch("team.recall_preferences", side_effect=recall):
                with self.assertRaises(CoachPaused) as caught:
                    team.execute(["Charizard"], avoided="Incineroar", output=root/"runs", profile="changed",
                                 ai=True, ai_client=client, allow_resume=True)
                recall_preferences(root/"memory", "changed", {"avoided_partner":"Torkoal"})
                with self.assertRaises(ValueError): team.resume_review(caught.exception.run_id)
                self.assertEqual(client.calls, 2)
                self.assertFalse(list((root/"runs").glob("*/report.html")))

    def test_expired_continuation_stops_without_model_call(self):
        import team
        from hmem_memory import recall_preferences
        client = self.make_client()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch("team.load_catalogue",return_value=(self.data,"fixture")), \
                 patch("team.recall_preferences",side_effect=lambda folder,profile,updates,**kw:recall_preferences(root/"memory",profile,updates,**kw)):
                with self.assertRaises(CoachPaused) as caught:
                    team.execute(["Charizard"],output=root/"runs",profile="expired",ai=True,ai_client=client,allow_resume=True)
                run_id=caught.exception.run_id
                team._PENDING_RUNS[run_id]["saved_at"] = time.monotonic()-team.PAUSE_SECONDS-1
                with self.assertRaises(ValueError):team.resume_review(run_id)
                self.assertEqual(client.calls,2)


if __name__ == "__main__": unittest.main()
