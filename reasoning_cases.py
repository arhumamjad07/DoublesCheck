"""Declared synthetic acceptance inputs. Expectations are never model responses."""
import copy
from dataclasses import dataclass

from catalogue import run_showdown
from team_builder import build_team
from battle_guidance import interaction_checks


@dataclass(frozen=True)
class Case:
    name: str
    favourites: tuple
    avoided: str | None = None
    objective: str = "simple"
    expected_refusal: bool = False
    fixture: bool = False
    remembered: bool = False


CASES = {
    c.name: c for c in [
        Case("one-favourite", ("Charizard",), "Incineroar"),
        Case("three-favourites", ("Charizard", "Venusaur", "Blastoise"), "Incineroar"),
        Case("six-favourites", ("Charizard", "Electabuzz", "Rillaboom", "Torkoal", "Gallade", "Maushold")),
        Case("remembered-avoidance", (), remembered=True),
        Case("memory-changes-team", (), "Torkoal", remembered=True),
        Case("seed-repair", ("Charizard", "Sneasler"), "Incineroar", "reliable", fixture=True),
        Case("rain-request", ("Charizard",), "Incineroar", "rain"),
        Case("locked-tradeoffs", ("Charizard", "Pelipper", "Torkoal", "Rillaboom", "Indeedee-F", "Sneasler")),
        Case("restricted-species", ("Miraidon",), expected_refusal=True),
        Case("unsupported-species", ("Bulbasaur",), expected_refusal=True),
        Case("duplicate-species", ("Charizard", "Charizard"), expected_refusal=True),
        Case("conflicting-preferences", ("Charizard",), "Charizard", expected_refusal=True),
        Case("unknown-species", ("Charizardzzz",), expected_refusal=True),
    ]
}


def seed_fixture(data):
    """Deliberately introduce a real condition, not a fabricated model critique."""
    team, _, _ = build_team(data, ["Charizard"], ["Incineroar"])
    team[-1] = next(copy.deepcopy(s) for s in data["species"]["Sneasler"]["sets"]
                    if s["item"] == "Psychic Seed" and s["ability"] == "Unburden")
    if not run_showdown({"operation": "validate", "team": team})["valid"]:
        raise ValueError("Declared repair fixture is no longer a legal full team")
    if not any(c["code"] == "missing_seed_terrain" and "Sneasler" in c["pokemon"] for c in interaction_checks(team, data)):
        raise ValueError("Declared repair fixture no longer contains its target condition")
    return team


def check_result(case, result, live):
    """Return factual unmet expectations; test success is distinct from team approval."""
    failures = []
    names = [m["species"] for m in result["team"]]
    if len(names) != 6 or not set(case.favourites) <= set(names): failures.append("locked_species_not_preserved")
    avoided = case.avoided or ("Incineroar" if case.remembered else None)
    if avoided in names: failures.append("avoidance_not_preserved")
    if result["legality"]["status"] != "passed_showdown_validator": failures.append("legality_not_verified")
    if case.remembered and (result["locked"] != ["Charizard"] or result["memory_used"]["avoided_partner"] != avoided):
        failures.append("remembered_preferences_not_applied")
    if not live:
        if result["model_calls"] != 0 or result.get("ai_coach") is not None: failures.append("offline_model_call")
        if case.fixture and not any(c["code"] == "missing_seed_terrain" for c in result["interactions"]):
            failures.append("seed_condition_not_detected")
        return failures
    coach = result.get("ai_coach") or {}
    if coach.get("execution") != "live": failures.append("not_live_model_evidence")
    if case.objective != "simple" and not coach.get("objective_assessment", {}).get("met"):
        failures.append("requested_objective_not_delivered")
    if case.fixture:
        if not coach.get("changed_from_local_baseline"): failures.append("no_actual_mutation")
        if not any(c["resolution"] == "change" and c["status"] == "resolved" for c in coach.get("revision_contracts", [])):
            failures.append("no_critic_required_verified_repair")
        if any(c["code"] == "missing_seed_terrain" and "Sneasler" in c["pokemon"] for c in result["interactions"]):
            failures.append("target_condition_persists")
    return failures
