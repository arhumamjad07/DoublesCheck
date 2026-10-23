"""Mechanics regressions and fixed examples that previously gave poor advice."""
import copy
import json
import unittest
from catalogue import load_catalogue, run_showdown
from battle_guidance import (actual_stats, speed_value, speed_profile, pair_plan,
                             interaction_checks, member_guidance)
from team_builder import TeamScorer, build_team, explain_team


class GuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = load_catalogue(sample=True)

    def mon(self, species, **changes):
        member = copy.deepcopy(self.data["species"][species]["sets"][0])
        member.update(changes)
        return member

    def codes(self, team):
        return {c["code"] for c in interaction_checks(team, self.data)}

    def test_known_level_50_charizard_stats(self):
        m = self.mon("Charizard", nature="Timid", evs=dict(hp=4, atk=0, def_=0, spa=252, spd=0, spe=252))
        m["evs"]["def"] = m["evs"].pop("def_")
        self.assertEqual(actual_stats(m, self.data), dict(hp=154, atk=93, **{"def": 98}, spa=161, spd=105, spe=167))

    def test_computed_stats_match_independent_showdown_arithmetic(self):
        samples = [m["sets"][0] for m in self.data["species"].values() if m["sets"]]
        # Also cover every nature and non-default IVs, not merely our favourite set.
        for nature in ("Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax",
                       "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash",
                       "Calm", "Gentle", "Sassy", "Careful", "Quirky"):
            samples.append(self.mon("Charizard", nature=nature, ivs=dict.fromkeys(("hp", "atk", "def", "spa", "spd", "spe"), 0)))
        expected = run_showdown({"operation": "stats", "team": samples})
        self.assertEqual([actual_stats(m, self.data) for m in samples], expected)

    def test_scarf_tailwind_round_once_not_twice(self):
        m = self.mon("Charizard", item="Choice Scarf", nature="Timid")
        self.assertEqual(actual_stats(m, self.data)["spe"], 167)
        self.assertEqual(speed_value(m, self.data), 250)
        self.assertEqual(speed_value(m, self.data, tailwind=True), 501)

    def test_conditions_match_running_showdown_battles(self):
        reference = run_showdown({"operation": "mechanics-fixtures"})
        self.assertEqual(reference["scarf"], {"normal": 250, "wind": 501, "room_stat": 501})
        venusaur = self.mon("Venusaur", nature="Modest", evs=dict(hp=0, atk=0, **{"def": 0}, spa=252, spd=4, spe=252))
        self.assertEqual(reference["chlorophyll"]["clear"], speed_value(venusaur, self.data))
        self.assertEqual(reference["chlorophyll"]["sun"], speed_value(venusaur, self.data, weather="sun"))
        self.assertEqual(reference["seed"], {"speed": 378, "item": "", "active": True})
        self.assertEqual(reference["sash"], {"speed": 189, "active": False})
        self.assertTrue(reference["iron_ball_grounded"])

    def test_unburden_not_assumed_from_holding_focus_sash(self):
        m = self.mon("Sneasler", ability="Unburden", item="Focus Sash", nature="Jolly")
        self.assertEqual(speed_value(m, self.data), 189)
        self.assertEqual(speed_value(m, self.data, unburden=True), 378)
        self.assertIn("conditional_unburden", self.codes([m]))
        self.assertIn("not active on entry", speed_profile(m, [m], self.data)["scenarios"][0]["condition"])

    def test_sun_speed_requires_active_sun(self):
        m = self.mon("Venusaur", ability="Chlorophyll")
        self.assertEqual(speed_value(m, self.data, weather="sun"), speed_value(m, self.data) * 2)
        self.assertEqual(speed_value(m, self.data, weather="rain"), speed_value(m, self.data))
        self.assertIn("missing_weather", self.codes([m]))
        self.assertNotIn("missing_weather", self.codes([m, self.mon("Torkoal")]))

    def test_psychic_terrain_penalizes_fake_out_opening(self):
        sneasler = self.mon("Sneasler", moves=["Fake Out", "Close Combat", "Dire Claw", "Protect"])
        psychic = self.mon("Indeedee-F")
        neutral = self.mon("Indeedee-F", ability="Own Tempo")
        blocked = pair_plan(sneasler, psychic, self.data)
        clear = pair_plan(sneasler, neutral, self.data)
        self.assertIn("psychic_priority", blocked["interaction_codes"])
        self.assertLess(blocked["score"], clear["score"])
        self.assertFalse(any("Fake Out can disrupt" in s for s in blocked["opening_actions"]))
        self.assertTrue(any("grounded" in s for s in blocked["cautions"]))

    def test_psychic_terrain_checks_prankster_enemy_status_but_not_screens(self):
        psychic = self.mon("Indeedee-F")
        prankster = self.mon("Grimmsnarl", ability="Prankster", moves=["Reflect", "Light Screen", "Thunder Wave", "Spirit Break"])
        self.assertIn("psychic_priority", self.codes([psychic, prankster]))
        prankster["moves"] = ["Reflect", "Light Screen", "Protect", "Spirit Break"]
        self.assertNotIn("psychic_priority", self.codes([psychic, prankster]))

    def test_seed_needs_matching_terrain_even_without_unburden(self):
        m = self.mon("Sneasler", item="Psychic Seed", ability="Poison Touch")
        self.assertIn("missing_seed_terrain", self.codes([m]))
        self.assertNotIn("missing_seed_terrain", self.codes([m, self.mon("Indeedee-F")]))
        self.assertIn("missing_seed_terrain", self.codes([m, self.mon("Rillaboom")]))

    def test_seed_unburden_pair_has_specific_activation_guidance(self):
        m = self.mon("Sneasler", item="Psychic Seed", ability="Unburden")
        pair = pair_plan(m, self.mon("Indeedee-F"), self.data)
        self.assertTrue(any("consumes" in text and "Unburden" in text for text in pair["reasons"]))

    def test_earthquake_hits_grounded_ally_but_not_flying_partner(self):
        chomp = self.mon("Garchomp", moves=["Earthquake", "Dragon Claw", "Rock Slide", "Protect"])
        self.assertIn("ally_spread", self.codes([chomp, self.mon("Incineroar")]))
        self.assertNotIn("ally_spread", self.codes([chomp, self.mon("Charizard")]))
        self.assertIn("ally_spread", self.codes([chomp, self.mon("Charizard", item="Iron Ball")]))

    def test_ally_immunity_respects_ability_and_balloon(self):
        chomp = self.mon("Garchomp", moves=["Earthquake", "Dragon Claw", "Rock Slide", "Protect"])
        self.assertNotIn("ally_spread", self.codes([chomp, self.mon("Gengar", ability="Levitate")]))
        self.assertNotIn("ally_spread", self.codes([chomp, self.mon("Incineroar", item="Air Balloon")]))

    def test_conflicting_weather_is_a_warning_not_species_replacement(self):
        pair = [self.mon("Torkoal"), self.mon("Pelipper")]
        self.assertIn("competing_weather", self.codes(pair))
        self.assertIn("sun_accuracy", self.codes(pair))

    def test_rain_removes_electro_shot_charge_and_redundant_herb_is_explained(self):
        arch = self.mon("Archaludon", item="Assault Vest")
        self.assertIn("electro_shot_charge", self.codes([arch]))
        self.assertNotIn("electro_shot_charge", self.codes([arch, self.mon("Pelipper")]))
        herb = self.mon("Archaludon", item="Power Herb")
        self.assertIn("one charge", next(c["explanation"] for c in interaction_checks([herb], self.data) if c["code"] == "electro_shot_charge"))
        self.assertIn("herb_in_rain", self.codes([herb, self.mon("Pelipper")]))

    def test_slow_room_partner_gets_timing_guidance(self):
        result = pair_plan(self.mon("Indeedee-F"), self.mon("Torkoal"), self.data)
        self.assertTrue(any("-7 priority" in text for text in result["opening_actions"]))
        torkoal = self.mon("Torkoal")
        self.assertEqual(speed_value(torkoal, self.data), 36)
        self.assertTrue(any("31 Speed IVs" in text for text in member_guidance(torkoal, [torkoal, self.mon("Indeedee-F")], self.data)["set_cautions"]))

    def test_double_room_warns_that_second_use_undoes_first(self):
        a = self.mon("Indeedee-F")
        b = self.mon("Porygon2", moves=["Trick Room", "Recover", "Ice Beam", "Tera Blast"])
        result = pair_plan(a, b, self.data)
        self.assertIn("double_room", result["interaction_codes"])
        self.assertTrue(any("undo" in text for text in result["cautions"]))

    def test_source_item_popularity_breaks_otherwise_equal_choices(self):
        a = self.mon("Charizard", item="Choice Specs")
        b = copy.deepcopy(a)
        b["item"] = "Charcoal"
        a["evidence"]["item_share"] = .76
        b["evidence"]["item_share"] = .034
        scorer = TeamScorer(self.data)
        self.assertGreater(scorer.score([a]), scorer.score([b]))

    def test_rain_context_prefers_vest_over_redundant_herb(self):
        builds = self.data["species"]["Archaludon"]["sets"]
        vest = next(m for m in builds if m["item"] == "Assault Vest")
        herb = next(m for m in builds if m["item"] == "Power Herb")
        scorer = TeamScorer(self.data)
        rain = self.mon("Pelipper")
        self.assertGreater(scorer.score([vest, rain]), scorer.score([herb, rain]))

    def test_catalogue_offers_single_target_ground_alternative(self):
        self.assertTrue(any("Stomping Tantrum" in m["moves"] and "Earthquake" not in m["moves"] for m in self.data["species"]["Garchomp"]["sets"]))

    def test_poorly_matched_seed_loses_to_identical_working_item(self):
        wrong = self.mon("Sneasler", item="Psychic Seed", ability="Poison Touch")
        right = copy.deepcopy(wrong); right["item"] = "Focus Sash"
        scorer = TeamScorer(self.data)
        self.assertGreater(scorer.score([right]), scorer.score([wrong]))

    def test_report_contains_numbers_conditions_and_source_limits(self):
        team, _, locked = build_team(self.data, ["Charizard"])
        result = explain_team(team, self.data, locked)
        for member in result["members"]:
            self.assertEqual(len(member["actual_stats"]), 6)
            self.assertIn("no survival or knockout benchmark", member["spread_explanation"])
        self.assertEqual(len(result["possible_leads"]), 3)
        self.assertTrue(any(m["species"] == "Torkoal" for m in team))
        self.assertIn("win probability", result["team_evaluation"]["scope"])
        self.assertTrue(any(c["code"] == "solar_power_hp" for c in result["interactions"]))
        self.assertTrue(all(lead["opening_actions"] for lead in result["possible_leads"]))
        self.assertEqual(result["members"][0]["set"]["item"], "Choice Specs")

    def test_six_conflicting_locks_stay_locked_and_are_explained(self):
        names = ["Charizard", "Torkoal", "Pelipper", "Sneasler", "Indeedee-F", "Rillaboom"]
        team, check, locked = build_team(self.data, names)
        self.assertTrue(check["valid"])
        self.assertEqual([m["species"] for m in team], names)
        result = explain_team(team, self.data, locked)
        codes = {c["code"] for c in result["interactions"]}
        self.assertTrue({"competing_weather", "competing_terrain", "psychic_priority"} <= codes)

    def test_new_coaching_fields_are_html_escaped(self):
        from report import render
        team, validation, locked = build_team(self.data, ["Charizard", "Torkoal", "Pelipper", "Sneasler", "Indeedee-F", "Rillaboom"])
        result = explain_team(team, self.data, locked)
        hostile = '<script>alert("unsafe")</script>'
        result["members"][0]["move_guidance"][0]["guidance"] = hostile
        result["possible_leads"][0]["opening_actions"] = [hostile]
        result.update(data_source="sample", sources=[], statistics=self.data["statistics"],
                      set_method=self.data["set_method"], trace_id="a" * 32, showdown_export=validation["export"])
        html = render(result)
        self.assertNotIn(hostile, html)
        self.assertIn("&lt;script&gt;", html)
        for heading in ["Who moves first?", "Interactions and trade-offs", "Bring four of your six"]:
            self.assertIn(heading, html)


if __name__ == "__main__": unittest.main()
