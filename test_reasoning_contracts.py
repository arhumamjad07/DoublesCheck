"""Regression cases for useful critique, targeted repairs, and honest objectives."""
import copy
import unittest

from catalogue import load_catalogue, run_showdown
from team_builder import build_team
from agent_tools import CoachTools, ToolRefused, member_identity
from reasoning_contracts import RevisionContracts, objective_assessment
from ai_coach import run_coach, _active_feedback
from nightshift_client import CoachError
from test_ai_coach import Trace, ScriptedClient, INSPECT, submission, approval


def inspect(role, payload):
    return {"verdict" if role == "Critic" else "action": "tool", "tool": "inspect_team", "arguments": {}}


class ReasoningContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = load_catalogue(True)
        cls.baseline, _, cls.locked = build_team(cls.data, ["Charizard"], ["Incineroar"])
        cls.fixture = copy.deepcopy(cls.baseline)
        cls.fixture[-1] = next(copy.deepcopy(m) for m in cls.data["species"]["Sneasler"]["sets"]
                               if m["item"] == "Psychic Seed" and m["ability"] == "Unburden")
        assert run_showdown({"operation": "validate", "team": cls.fixture})["valid"]

    def setUp(self): self.trace = Trace()

    def engine(self):
        return CoachTools(self.data, self.fixture, ["Charizard", "Sneasler"], ["Incineroar"], self.trace, "explicit sourced test fixture")

    def issue(self, engine):
        return next(r for r in engine.inspect()["evidence"] if r.get("code") == "missing_seed_terrain")

    def request(self, engine):
        contracts = RevisionContracts()
        contracts.request([{"evidence_id": self.issue(engine)["id"], "resolution": "change"}], engine)
        return contracts

    def test_correct_source_change_closes_the_specific_contract(self):
        engine = self.engine(); contracts = self.request(engine)
        options = engine.invoke("get_sets", {"species": "Sneasler", "purpose": "repair_condition", "issue_id": self.issue(engine)["id"]})["options"]
        self.assertTrue(options)
        self.assertLessEqual(len(options), 3)
        for option in options: self.assertIn("missing_seed_terrain", option["resolves"])
        sash = next(o for o in options if o["item"] == "Focus Sash")
        engine.invoke("change_set", {"species": "Sneasler", "set_id": sash["set_id"]})
        rows = contracts.ensure_resolved(engine)
        self.assertEqual(rows[0]["status"], "resolved")
        self.assertEqual(rows[0]["requested_version"], 1)
        self.assertEqual(rows[0]["current_version"], 2)
        self.assertTrue(rows[0]["current_evidence_ids"])

    def test_unrelated_legal_edit_cannot_satisfy_criticism(self):
        engine = self.engine(); contracts = self.request(engine)
        option = engine.invoke("get_sets", {"species": "Charizard", "purpose": "different_item"})["options"][0]
        engine.invoke("change_set", {"species": "Charizard", "set_id": option["set_id"]})
        self.assertEqual(engine.version, 2)
        with self.assertRaises(ToolRefused): contracts.ensure_resolved(engine)

    def test_different_moves_with_same_unsupported_seed_do_not_close_contract(self):
        engine = self.engine(); contracts = self.request(engine)
        original = next(m for m in engine.team if m["species"] == "Sneasler")
        alternative = next(copy.deepcopy(m) for m in self.data["species"]["Sneasler"]["sets"]
                           if m["item"] == "Psychic Seed" and member_identity(m) != member_identity(original))
        engine.commit([alternative if m["species"] == "Sneasler" else m for m in engine.team], "Planner", "test edit")
        with self.assertRaises(ToolRefused): contracts.ensure_resolved(engine)

    def test_generic_legality_fact_cannot_define_a_meaningless_change(self):
        engine = self.engine(); contracts = RevisionContracts()
        with self.assertRaises(ToolRefused):
            contracts.request([{"evidence_id": engine.inspect()["evidence"][0]["id"], "resolution": "change"}], engine)
        self.assertEqual(contracts.records, [])

    def test_invalid_issue_batch_does_not_partially_change_contract_state(self):
        engine = self.engine(); contracts = RevisionContracts()
        with self.assertRaises(ToolRefused): contracts.request([
            {"evidence_id": self.issue(engine)["id"], "resolution": "change"},
            {"evidence_id": "E999", "resolution": "change"}], engine)
        self.assertEqual(contracts.records, [])

    def test_repair_search_refuses_stale_or_unrelated_issue(self):
        engine = self.engine()
        with self.assertRaises(ToolRefused): engine.invoke("get_sets", {"species": "Charizard", "purpose": "repair_condition", "issue_id": self.issue(engine)["id"]})
        with self.assertRaises(ToolRefused): engine.invoke("get_sets", {"species": "Sneasler", "purpose": "repair_condition", "issue_id": "E999"})

    def test_set_option_must_be_issued_for_the_current_team_version(self):
        engine = self.engine()
        options = engine.invoke("get_sets", {"species": "Charizard", "purpose": "different_item"})["options"]
        engine.invoke("change_set", {"species": "Charizard", "set_id": options[0]["set_id"]})
        with self.assertRaises(ToolRefused): engine.invoke("change_set", {"species": "Charizard", "set_id": options[-1]["set_id"]})

    def run_review(self, client, fixture=False, objective="simple"):
        return run_coach(self.data, self.fixture if fixture else self.baseline,
                         ["Charizard", "Sneasler"] if fixture else self.locked,
                         ["Incineroar"], {"favourite": "Charizard", "avoided_partner": "Incineroar"},
                         self.trace, client, origin="explicit simulated evaluation", objective=objective, review_first=True)

    def test_review_first_does_not_invent_a_model_planner_role(self):
        client = ScriptedClient([inspect, approval])
        _, check, result = self.run_review(client)
        self.assertTrue(check["valid"])
        self.assertEqual(client.calls, 2)
        self.assertEqual(result["roles_used"], ["Critic"])
        self.assertEqual(result["proposal_origin"], "local_builder")
        self.assertFalse(result["changed_from_local_baseline"])

    def test_critic_dispatches_planner_and_actual_fix_returns_for_approval(self):
        def critique(role, p):
            issue = next(r for r in p["shared_state"]["evidence"] if r.get("code") == "missing_seed_terrain")
            return {"verdict": "revise", "version": 1, "issues": [{"evidence_id": issue["id"], "resolution": "change"}]}
        def get_sets(role, p): return {"action": "tool", **p["critic_feedback"]["suggested_investigations"][0]}
        def change(role, p):
            choice = next(o for o in p["shared_options"] if o["item"] == "Focus Sash")
            return {"action": "tool", "tool": "change_set", "arguments": {"species": "Sneasler", "set_id": choice["set_id"]}}
        client = ScriptedClient([inspect, critique, get_sets, change, submission, approval])
        _, check, result = self.run_review(client, True)
        self.assertTrue(check["valid"])
        self.assertEqual(client.calls, 6)
        self.assertEqual(result["roles_used"], ["Critic", "Planner"])
        self.assertTrue(result["changed_from_local_baseline"])
        self.assertEqual(result["revision_contracts"][0]["status"], "resolved")
        self.assertTrue(all(r["version"] == 2 for r in result["selected_evidence"]))
        handoff=client.payloads[-2]
        self.assertEqual(handoff["critic_feedback"]["issues"],[])
        self.assertEqual(handoff["critic_feedback"]["status"],"resolved")
        self.assertEqual(handoff["tools"],{})
        self.assertEqual(handoff["shared_options"],[])
        self.assertIsNone(handoff["planner_proposal"])

    def test_critic_options_are_shared_with_planner_without_reissuing_ids(self):
        def search(role,p):
            fact=next(r for r in p["shared_state"]["evidence"] if r.get("code")=="missing_seed_terrain")
            return {"verdict":"tool","tool":"get_sets","arguments":{"species":"Sneasler","purpose":"repair_condition","issue_id":fact["id"]}}
        def critique(role,p):
            fact=next(r for r in p["shared_state"]["evidence"] if r.get("code")=="missing_seed_terrain")
            return {"verdict":"revise","version":1,"issues":[{"evidence_id":fact["id"],"resolution":"change"}]}
        def change(role,p):
            self.assertNotIn("get_sets",p["tools"])
            option=next(o for o in p["shared_options"] if o["item"]=="Focus Sash")
            return {"action":"tool","tool":"change_set","arguments":{"species":"Sneasler","set_id":option["set_id"]}}
        client=ScriptedClient([inspect,search,critique,change,submission,approval])
        _,_,result=self.run_review(client,True)
        self.assertEqual(client.calls,6)
        self.assertEqual(result["revision_contracts"][0]["status"],"resolved")
        self.assertEqual(client.payloads[2]["tools"],{})

    def test_critic_cannot_approve_before_real_inspection(self):
        client = ScriptedClient([approval] * 8)
        with self.assertRaises(CoachError): self.run_review(client)
        self.assertFalse(any(e["action"] == "ai_approved" for e in self.trace.events))

    def test_duplicate_citations_do_not_count_as_two_supported_facts(self):
        def duplicate(role, p):
            row = approval(role, p); row["evidence_ids"] = [row["evidence_ids"][0]] * 2; return row
        client = ScriptedClient([inspect] + [duplicate] * 7)
        with self.assertRaises(CoachError): self.run_review(client)

    def test_unmet_objective_cannot_be_quietly_approved(self):
        client = ScriptedClient([inspect] + [approval] * 7)
        with self.assertRaises(CoachError): self.run_review(client, objective="rain")

    def test_explicit_counterproposal_is_not_labelled_goal_fulfilment(self):
        def alternative(role, p):
            row = approval(role, p)
            unmet = next(r for r in p["shared_state"]["evidence"] if r["kind"] == "objective")
            row["evidence_ids"] = [row["evidence_ids"][0], unmet["id"]]; return row
        _, _, result = self.run_review(ScriptedClient([inspect, alternative]), objective="rain")
        self.assertFalse(result["objective_assessment"]["met"])
        self.assertIn("not delivered", result["objective_assessment"]["explanation"])

    def test_feedback_rebinds_same_code_to_the_correct_species(self):
        facts=[{"id":"E22","kind":"caution","code":"missing_weather","pokemon":["Charizard"],"text":"Charizard needs sun"},
               {"id":"E23","kind":"caution","code":"missing_weather","pokemon":["Venusaur"],"text":"Venusaur needs sun"}]
        rows=[{"status":"open","kind":"caution","code":"missing_weather","pokemon":["Venusaur"],"resolution":"change"},
              {"status":"open","kind":"caution","code":"missing_weather","pokemon":["Charizard"],"resolution":"change"}]
        result=_active_feedback({"round":1,"version":1,"suggested_investigations":[]},rows,{"version":2,"evidence":facts})
        self.assertEqual([r["evidence_id"] for r in result["issues"]],["E23","E22"])

    def test_weather_goal_can_change_the_team_and_return_fresh_checked_state(self):
        def critique(role,p):
            fact=next(r for r in p["shared_state"]["evidence"] if r.get("code")=="missing_mode_rain")
            return {"verdict":"revise","version":1,"issues":[{"evidence_id":fact["id"],"resolution":"change"}]}
        def search(role,p):
            return {"action":"tool",**p["critic_feedback"]["suggested_investigations"][0]}
        def build(role,p):
            choices=next(r["result"]["choices"] for r in p["recent_tool_results"] if r.get("tool")=="search_partners")
            self.assertIn("Pelipper",[r["species"] for r in choices])
            return {"action":"tool","tool":"build_candidate","arguments":{"partners":["Pelipper"]}}
        def rain_submission(role,p):
            self.assertEqual(p["shared_state"]["version"],2)
            self.assertNotIn("inspect_team",p["tools"])
            self.assertFalse(any(f.get("code")=="missing_mode_rain" for f in p["shared_state"]["evidence"]))
            row=submission(role,p); row["strategy"]="rain"; return row
        # Two invalid arguments must not evict successful search evidence from
        # the shared model context. Failed commands still consume the budget.
        bad={"action":"tool","tool":"get_sets","arguments":{"species":"Pelipper","purpose":"rain"}}
        client=ScriptedClient([inspect,critique,search,bad,bad,build,rain_submission,approval])
        team,check,result=self.run_review(client,objective="rain")
        self.assertTrue(check["valid"])
        self.assertIn("Charizard",[m["species"] for m in team])
        self.assertNotIn("Incineroar",[m["species"] for m in team])
        self.assertTrue(any(m["ability"]=="Drizzle" for m in team))
        self.assertTrue(result["objective_assessment"]["met"])
        self.assertEqual(result["revision_contracts"][0]["status"],"resolved")
        self.assertEqual(client.calls,8)


if __name__ == "__main__": unittest.main()
