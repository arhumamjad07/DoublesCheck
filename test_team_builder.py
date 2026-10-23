"""Regression checks for real-data teams, legality, cost controls and reporting."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from catalogue import ROOT, load_catalogue, run_showdown
from hmem_memory import recall_preferences
from team_builder import build_team, explain_team
from report import render
from credit_policy import require_model_opt_in

class TeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = load_catalogue(sample=True)
        cls.team, cls.validation, cls.locked = build_team(cls.data, ["Charizard"])

    def test_real_data_and_historical_format_are_present(self):
        self.assertEqual(len(self.data["species"]), 1417)
        self.assertEqual(self.data["format_id"], "gen9vgc2024regh")
        self.assertEqual(self.data["statistics"]["number of battles"], 965304)
        self.assertEqual(len(self.data["types"]), 18)

    def test_one_favourite_builds_six_valid_species(self):
        self.assertEqual(len(self.team), 6)
        self.assertEqual(self.team[0]["species"], "Charizard")
        self.assertTrue(self.validation["valid"])
        self.assertEqual(len({m["item"] for m in self.team}), 6)
        self.assertEqual(len({self.data["species"][m["species"]]["base_species"] for m in self.team}), 6)

    def test_three_favourites_are_preserved(self):
        team, check, locked = build_team(self.data, ["Charizard", "Venusaur", "Blastoise"])
        self.assertEqual([s["species"] for s in team[:3]], locked)
        self.assertTrue(check["valid"])

    def test_six_locked_members_are_reviewed_without_replacements(self):
        names = [s["species"] for s in self.team]
        team, check, _ = build_team(self.data, names)
        self.assertEqual([s["species"] for s in team], names)
        self.assertTrue(check["valid"])

    def test_avoided_partner_cannot_be_selected(self):
        avoided = self.team[1]["species"]
        team, _, _ = build_team(self.data, ["Charizard"], [avoided])
        self.assertNotIn(avoided, [s["species"] for s in team])

    def test_banned_restricted_and_mega_favourites_rejected(self):
        for species in ["Flutter Mane", "Miraidon", "Charizard-Mega-X"]:
            with self.subTest(species=species), self.assertRaises(ValueError):
                build_team(self.data, [species])

    def test_unknown_duplicate_and_excess_favourites_rejected(self):
        for names in [["MadeUpMon"], ["Charizard", "Charizard"], ["Charizard"] * 7, []]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                build_team(self.data, names)

    def test_locked_and_avoided_conflict_rejected(self):
        with self.assertRaises(ValueError):
            build_team(self.data, ["Charizard"], ["Charizard"])

    def test_independent_validator_rejects_illegal_move(self):
        team = copy.deepcopy(self.team)
        team[0]["moves"][0] = "Spore"
        self.assertFalse(run_showdown({"operation": "validate", "team": team})["valid"])

    def test_independent_validator_rejects_duplicate_item(self):
        team = copy.deepcopy(self.team)
        team[1]["item"] = team[0]["item"]
        self.assertFalse(run_showdown({"operation": "validate", "team": team})["valid"])

    def test_independent_validator_rejects_illegal_evs(self):
        team = copy.deepcopy(self.team)
        team[0]["evs"]["spa"] = 999
        self.assertFalse(run_showdown({"operation": "validate", "team": team})["valid"])

    def test_full_type_chart_respects_dual_types_and_immunity(self):
        self.assertEqual(self.data["species"]["Charizard"]["incoming"]["Rock"], 4)
        self.assertEqual(self.data["species"]["Charizard"]["incoming"]["Ground"], 0)
        self.assertEqual(self.data["species"]["Garchomp"]["incoming"]["Electric"], 0)

    def test_model_gate_defaults_to_off(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(RuntimeError):
            require_model_opt_in()

    def test_legacy_model_client_is_blocked_before_transport(self):
        from coaching import ModelClient
        post = Mock(side_effect=AssertionError("Paid transport must not run"))
        client = ModelClient(None, {}, post, Mock())
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(RuntimeError):
            client.call("Builder", "anything", {})
        post.assert_not_called()
        self.assertEqual(client.calls, 0)

    def test_sample_mode_does_not_construct_a_network_client(self):
        with patch("catalogue.Zetaris", side_effect=AssertionError("No network allowed")):
            data, label = load_catalogue(sample=True)
        self.assertEqual(data["format_id"], self.data["format_id"])
        self.assertIn("sample", label)

    def test_zetaris_failure_never_silently_becomes_sample_data(self):
        with patch("catalogue.Zetaris", side_effect=RuntimeError("offline")), self.assertRaises(RuntimeError):
            load_catalogue(sample=False)

    def test_expanded_hmem_preferences_persist_real_species(self):
        with tempfile.TemporaryDirectory() as directory:
            recall_preferences(directory, "real-species", {"favourite": "Garchomp", "avoided_partner": "Incineroar"})
            memory = recall_preferences(directory, "real-species")
            self.assertEqual(memory["favourite"], "Garchomp")
            self.assertEqual(memory["avoided_partner"], "Incineroar")

    def test_reporting_explains_each_member_and_produces_four_of_six(self):
        result = explain_team(self.team, self.data, self.locked)
        self.assertEqual(len(result["members"]), 6)
        self.assertEqual(len(result["possible_leads"]), 3)
        for plan in result["four_of_six_examples"]:
            self.assertEqual(len(set(plan["lead"] + plan["back"])), 4)
        self.assertTrue(any("historical" in warning.lower() for warning in result["warnings"]))

if __name__ == "__main__":
    unittest.main()
