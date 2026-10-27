"""Bounded local planning and evaluation over sourced sets, with no model calls."""
import copy
from itertools import combinations
import math
import re
from catalogue import run_showdown
from battle_guidance import (PROTECT, WEATHER, WEATHER_SPEED, TERRAINS, SEEDS, ROOM_SLOW,
                             interaction_checks, member_guidance, speed_value, speed_overview, pair_plan)

def identifier(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())

def resolve_names(values, data):
    index = {identifier(name): name for name in data["species"]}
    result = []
    for value in values:
        if not isinstance(value, str) or identifier(value) not in index:
            raise ValueError(f"Unknown Pokemon: {str(value)[:70]}. Check spelling or form name.")
        result.append(index[identifier(value)])
    return result

def roles(member, data):
    moves = set(member["moves"])
    tags = []
    if moves & {"Tailwind", "Trick Room", "Icy Wind", "Electroweb"}: tags.append("speed control")
    if "Fake Out" in moves: tags.append("Fake Out support")
    if moves & {"Follow Me", "Rage Powder"}: tags.append("redirection")
    if moves & {"Parting Shot", "U-turn", "Volt Switch", "Flip Turn"}: tags.append("pivot")
    if member["ability"] in {"Drought", "Drizzle", "Sand Stream", "Snow Warning"}: tags.append("weather setter")
    if member["ability"] == "Intimidate": tags.append("Intimidate support")
    if moves & {"Reflect", "Light Screen", "Aurora Veil"}: tags.append("screens")
    if sum(data["moves"][m]["category"] != "Status" for m in moves) >= 3: tags.append("attacker")
    return tags or ["mixed utility"]

def set_key(member):
    return (member["species"], member["ability"], member["item"], member["nature"],
            tuple(sorted(member["evs"].items())), tuple(member["moves"]))


def item_assignment_possible(mons, names, used_items):
    """Exact small matching check before pruning a locked-team search branch."""
    domains = [sorted({s["item"] for s in mons[name]["sets"]} - set(used_items)) for name in names]
    owner = {}
    def assign(index, seen):
        for item in domains[index]:
            if item in seen: continue
            seen.add(item)
            if item not in owner or assign(owner[item], seen):
                owner[item] = index
                return True
        return False
    return all(assign(index, set()) for index in range(len(domains)))


class TeamScorer:
    """Named heuristic terms and cached checks; scores are not win probabilities."""
    def __init__(self, data):
        self.data = data
        self.features = {}
        self.pairs = {}

    def feature(self, member):
        key = set_key(member)
        if key in self.features: return self.features[key]
        data = self.data
        mon = data["species"][member["species"]]
        move_rows = [data["moves"][m] for m in member["moves"]]
        attacks = [m for m in move_rows if m["category"] != "Status"]
        counts = {}
        for move in attacks: counts[move["type"]] = counts.get(move["type"], 0) + 1
        evidence = member.get("evidence")
        if evidence:
            quality = (.6 * math.log(max(.001, evidence["item_share"]))
                       + .3 * math.log(max(.001, evidence["spread_share"]))
                       + .4 * math.log(max(.001, evidence["ability_share"]))
                       + .2 * sum(math.log(max(.001, v)) for v in evidence["move_shares"].values()) / 4)
        else:
            # Older registered snapshots remain usable, with source order as a tie-break.
            original = next((i for i, s in enumerate(mon["sets"]) if set_key(s) == key), 12)
            quality = -.18 * original
        quality -= sum(max(0, count - 2) * 1.3 for count in counts.values())
        if set(member["moves"]) & PROTECT: quality += .6
        if len(attacks) == 0: quality -= 4
        if member["item"] == "Assault Vest" and len(attacks) < 4: quality -= 12
        if member["item"].startswith("Choice ") and len(attacks) < 4: quality -= 8
        if member["item"] == "Choice Band" and not any(m["category"] == "Physical" for m in attacks): quality -= 8
        if member["item"] == "Choice Specs" and not any(m["category"] == "Special" for m in attacks): quality -= 8
        feature = {"quality": quality, "roles": set(roles(member, data)),
                   "speed": speed_value(member, data), "attacks": len(attacks),
                   "usage": math.log1p(mon["usage"] * 100) * 1.1}
        self.features[key] = feature
        return feature

    def pair(self, first, second):
        key = tuple(sorted((set_key(first), set_key(second))))
        if key in self.pairs: return self.pairs[key]
        bonus = 0
        for setter, user in ((first, second), (second, first)):
            weather = WEATHER.get(setter["ability"])
            if weather and (WEATHER_SPEED.get(user["ability"]) == weather or weather == "sun" and user["ability"] == "Solar Power"):
                bonus += 5
            terrain = TERRAINS.get(setter["ability"])
            if terrain and SEEDS.get(user["item"]) == terrain and user["ability"] == "Unburden": bonus += 4
            if "Trick Room" in setter["moves"] and self.feature(user)["speed"] <= ROOM_SLOW: bonus += 1.5
        a, b = self.data["species"][first["species"]], self.data["species"][second["species"]]
        def weight(source, target):
            total = sum(source["teammate_weights"].values()) / 5
            return min(1, source["teammate_weights"].get(target["name"], 0) / max(1, total))
        cooccurrence = (weight(a, b) + weight(b, a)) * .75
        # Pair-local checks intentionally omit missing full-team support: the team term handles that.
        local_codes = {"competing_weather", "competing_terrain", "psychic_priority", "terrain_sleep",
                       "sun_water", "rain_fire", "sun_accuracy", "ally_spread", "grassy_earthquake", "ability_suppression"}
        penalty = sum(c["penalty"] for c in interaction_checks([first, second], self.data) if c["code"] in local_codes)
        result = (bonus - penalty, cooccurrence)
        self.pairs[key] = result
        return result

    def components(self, team):
        features = [self.feature(m) for m in team]
        mons = [self.data["species"][m["species"]] for m in team]
        tags = {tag for row in features for tag in row["roles"]}
        support = sum({"speed control": 4, "Fake Out support": 1.5, "redirection": 2.5,
                       "pivot": 1.25, "screens": 1.5, "Intimidate support": 2}.get(tag, 0) for tag in tags)
        risk = 0
        for attack in self.data["types"]:
            weak = sum(m["incoming"][attack] > 1 for m in mons)
            resist = sum(m["incoming"][attack] < 1 for m in mons)
            risk += .45 * weak ** 2 + (1.2 * weak if weak > 1 and not resist else 0)
        weather = {WEATHER[m["ability"]] for m in team if m["ability"] in WEATHER}
        terrains = {TERRAINS[m["ability"]] for m in team if m["ability"] in TERRAINS}
        field, cooccurrence = 0, 0
        for a, b in combinations(team, 2):
            interaction, historical = self.pair(a, b)
            field += interaction; cooccurrence += historical
        for member in team:
            wanted = WEATHER_SPEED.get(member["ability"]) or ("sun" if member["ability"] == "Solar Power" else None)
            if wanted and wanted not in weather: field -= 3
            if member["item"] in SEEDS and SEEDS[member["item"]] not in terrains: field -= 3
            if "Electro Shot" in member["moves"] and "rain" not in weather and member["item"] != "Power Herb": field -= 1
            if "Electro Shot" in member["moves"] and "rain" in weather and member["item"] == "Power Herb": field -= .8
            if set(member["moves"]) & {"Solar Beam", "Solar Blade"} and "sun" not in weather: field -= 2
        room_users = sum("Trick Room" in member["moves"] for member in team)
        if room_users > 1: support -= (room_users - 1) * 1.5
        if room_users and not any(row["speed"] <= ROOM_SLOW for row in features): support -= 2
        return {"historical_usage": sum(row["usage"] for row in features),
                "set_evidence_and_usability": sum(row["quality"] for row in features),
                "support_roles": support, "original_type_balance": -risk,
                "field_and_partner_interactions": field, "historical_cooccurrence": cooccurrence}

    def score(self, team):
        return round(sum(self.components(team).values()), 5)


def score_team(team, data):
    return TeamScorer(data).score(team)

def build_team(data, favourites, avoided=None, trace=None):
    if not 1 <= len(favourites) <= 6:
        raise ValueError("Lock between one and six Pokemon.")
    favourites = resolve_names(favourites, data)
    avoided = set(resolve_names(avoided or [], data))
    mons = data["species"]
    bases = [mons[n]["base_species"] for n in favourites]
    if len(set(bases)) != len(bases):
        raise ValueError("Species Clause: two forms of the same species cannot share this team.")
    if set(favourites) & avoided:
        raise ValueError("A locked favourite is also avoided. Clear that avoidance or change the locks.")
    for name in favourites:
        if not mons[name]["eligible_species"]:
            raise ValueError(f"{name} is not eligible in the selected historical Regulation H format.")
        if not mons[name]["sets"]:
            raise ValueError(f"{name} has no validated build in this historical snapshot. No moveset was invented.")
    if trace: trace.event("Planner", "locked_favourites_checked", favourites=favourites, avoided=sorted(avoided))
    scorer = TeamScorer(data)
    beam = [[]]
    for locked_index, name in enumerate(favourites):
        next_beam = []
        for team in beam:
            used_items = {s["item"] for s in team}
            for build in mons[name]["sets"]:
                if build["item"] not in used_items and item_assignment_possible(mons, favourites[locked_index+1:], used_items | {build["item"]}):
                    next_beam.append(team + [copy.deepcopy(build)])
        if not next_beam:
            raise ValueError("Locked Pokemon cannot satisfy Item Clause with available sets; no lock was replaced.")
        beam = sorted(next_beam, key=scorer.score, reverse=True)[:10]
    if "zetaris_partner_pool" in data:
        # Connected search cannot silently widen beyond the live SQL shortlist.
        candidates = set(data["zetaris_partner_pool"])
    else:
        ranked = sorted((m for m in mons.values() if m["sets"] and m["eligible_species"] and m["name"] not in avoided),
                        key=lambda m: (-m["usage"], m["name"]))
        candidates = {m["name"] for m in ranked[:45]}
        for name in favourites:
            candidates.update(sorted(mons[name]["teammate_weights"], key=mons[name]["teammate_weights"].get, reverse=True)[:10])
    candidates = sorted(n for n in candidates if n in mons and mons[n]["eligible_species"] and mons[n]["sets"] and n not in avoided)
    while len(beam[0]) < 6:
        expansions = []
        for team in beam:
            used_bases = {mons[s["species"]]["base_species"] for s in team}
            used_items = {s["item"] for s in team}
            for name in candidates:
                if mons[name]["base_species"] in used_bases: continue
                available = [s for s in mons[name]["sets"] if s["item"] not in used_items]
                # Rank options in this team's context, so item popularity cannot win
                # over a working seed/weather combination or a usable support move.
                available.sort(key=lambda build: scorer.score(team + [build]), reverse=True)
                for build in available[:3]:
                    proposal = team + [build]
                    expansions.append((scorer.score(proposal), proposal))
        if not expansions: raise RuntimeError("Search exhausted without a valid six-member team.")
        expansions.sort(key=lambda row: (-row[0], tuple(s["species"] + s["item"] for s in row[1])))
        seen, beam = set(), []
        for score, team in expansions:
            key = tuple(sorted(set_key(s) for s in team))
            if key in seen: continue
            seen.add(key); beam.append(team)
            if len(beam) >= 10: break
        if trace: trace.event("Builder", "candidate_slot_filled", slots=len(beam[0]), evaluated=len(expansions), retained=len(beam))
    # Full independent validator is allowed to block and force a different search candidate.
    for attempt, team in enumerate(beam, 1):
        check = run_showdown({"operation": "validate", "team": team})
        if trace: trace.event("LegalityEvaluator", "team_checked", attempt=attempt, errors=check["errors"])
        if check["valid"]:
            if trace:
                trace.event("TeamEvaluator", "team_quality_checked", components=scorer.components(check["team"]),
                            interaction_codes=sorted({c["code"] for c in interaction_checks(check["team"], data)}), model_calls=0)
            return check["team"], check, favourites
    raise RuntimeError("All final candidates failed the full Showdown validator; output withheld.")

def explain_team(team, data, locked):
    mons = data["species"]
    weaknesses = []
    for attack in data["types"]:
        weak = [s["species"] for s in team if mons[s["species"]]["incoming"][attack] > 1]
        checks = [s["species"] for s in team if mons[s["species"]]["incoming"][attack] < 1]
        if len(weak) >= 2:
            weaknesses.append({"type": attack, "weak": weak, "resist_or_immune": checks,
                               "severity": "high" if len(weak) >= 3 or not checks else "watch"})
    weaknesses.sort(key=lambda r: (-len(r["weak"]), r["type"]))
    members = []
    for member in team:
        mon = mons[member["species"]]
        if member["species"] in locked:
            reason = "You locked this Pokemon, so the search preserved it."
        else:
            reason = "Adds " + ", ".join(roles(member, data)) + " to the candidate team."
            supplied = WEATHER.get(member["ability"])
            if supplied:
                beneficiaries = [m["species"] for m in team if m is not member and
                                 (WEATHER_SPEED.get(m["ability"]) == supplied or supplied == "sun" and m["ability"] == "Solar Power")]
                if beneficiaries:
                    reason += f" Its {member['ability']} supplies {supplied} for {', '.join(beneficiaries)}; that benefit depends on keeping the weather active."
            terrain = TERRAINS.get(member["ability"])
            if terrain:
                seed_users = [m["species"] for m in team if SEEDS.get(m["item"]) == terrain]
                if seed_users:
                    reason += f" Its {terrain} Terrain can activate the selected seeds on {', '.join(seed_users)}."
            for favourite in locked:
                resisted = [t for t in data["types"] if mons[favourite]["incoming"][t] > 1 and mon["incoming"][t] < 1]
                if resisted:
                    reason += f" Its original types resist or are immune to {', '.join(resisted)}, to which {favourite} is weak."
            if any(mons[f]["teammate_weights"].get(member["species"], 0) > 0 for f in locked):
                reason += " It also appears alongside a locked favourite in this historical ladder snapshot."
            reason += " This is a search heuristic, not proof it is the best partner."
        members.append({"name": member["species"], "locked": member["species"] in locked,
            "selection_reason": reason,
            "roles": roles(member, data), "types": mon["types"], "usage_percent": round(mon["usage"] * 100, 3),
            "base_stats": mon["base_stats"], "type_weaknesses": {t: v for t, v in mon["incoming"].items() if v > 1},
            "ability_description": data["abilities"][member["ability"]],
            "item_description": data["items"][member["item"]],
            "moves": [data["moves"][m] for m in member["moves"]], "set": member})
    scorer = TeamScorer(data)
    baseline = scorer.components(team)
    for member, row in zip(team, members):
        row.update(member_guidance(member, team, data))
        row["historical_evidence"] = member.get("evidence")
        without = scorer.components([m for m in team if m is not member])
        row["heuristic_contribution"] = {key: round(baseline[key] - without[key], 3) for key in baseline}
    leads = [pair_plan(a, b, data) for a, b in combinations(team, 2)]
    leads.sort(key=lambda row: (-row["score"], tuple(row["pokemon"])))
    chosen_leads = leads[:3]
    plans = []
    for lead in chosen_leads:
        active = [s for s in team if s["species"] in lead["pokemon"]]
        remaining = [s for s in team if s["species"] not in lead["pokemon"]]
        best = max(combinations(remaining, 2), key=lambda pair: scorer.score(active + list(pair)))
        group = active + list(best)
        notes = []
        for member in best:
            tags = roles(member, data)
            notes.append(f"{member['species']} supplies {', '.join(tags)} from the back; switching still costs positioning and may expose it to an attack.")
        if any("Trick Room" in m["moves"] for m in group):
            slow = [m["species"] for m in group if speed_value(m, data) <= ROOM_SLOW]
            fast = [m["species"] for m in group if speed_value(m, data) >= 120]
            if slow and fast: notes.append(f"Split modes: {', '.join(slow)} can use the slow mode; {', '.join(fast)} usually prefer turns outside Trick Room. Opponent Speed still decides whether to reverse order.")
        plans.append({"lead": lead["pokemon"], "back": [s["species"] for s in best], "reasons": notes,
                      "cautions": [c["explanation"] for c in interaction_checks(group, data)],
                      "note": "A conditional four-of-six practice plan, not an opponent-specific selection. Change it after inspecting the opponent's six."})
    warnings = ["Historical Regulation H only; this is not a check against current 2026 tournament rules.",
        "Sets combine historical aggregate choices; they are not proven winning sets, and a legal team is not necessarily strong.",
        "Type charts describe original types before Terastallization and ignore abilities, items and field effects.",
        "No damage simulation or battle win probability is computed. Leads and four-of-six selections are conditional practice plans.",
        "IVs default to 31 because aggregate usage does not provide them. They are not optimized.",
        "Speed examples cover listed conditions only, with neutral stat stages and no status or suppression. Unknown opponent sets prevent guaranteed move-order claims."]
    if not any("speed control" in member["roles"] for member in members): warnings.append("This team has no recognized speed-control move in the selected sets.")
    return {"members": members, "weaknesses": weaknesses, "possible_leads": chosen_leads,
            "four_of_six_examples": plans, "warnings": warnings,
            "interactions": interaction_checks(team, data), "speed_overview": speed_overview(team, data),
            "team_evaluation": {"components": {k: round(v, 3) for k, v in baseline.items()},
                                "score": scorer.score(team),
                                "scope": "Transparent bounded-search heuristic; neither a win probability nor a benchmark of competitive strength. The search does not examine every legal team."}}
