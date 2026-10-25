"""Small, whitelisted tools and a versioned evidence ledger for AI coaching."""
import copy
import hashlib
import json
from battle_guidance import interaction_checks, member_guidance, WEATHER, TERRAINS
from catalogue import run_showdown
from team_builder import build_team, resolve_names, roles, set_key, TeamScorer
from nightshift_client import CoachError

OBJECTIVES = {"simple": "Beginner-friendly balanced play", "sun": "Explore a sun mode",
              "rain": "Explore a rain mode", "trick-room": "Explore a slow Trick Room mode",
              "reliable": "Repair unsupported item/weather activation plans; disclose remaining conditional effects honestly"}
TOOLS = {
    "inspect_team": "No arguments. Check the current team's legality, constraints, stats, supported interactions and evidence.",
    "search_partners": "{for_species: name, role: any|weather|speed|redirection|pivot, weather: any|sun|rain}. Return up to six supported source choices.",
    "get_sets": "{species: name, purpose: recommended|protection|no_ally_hit|different_item|repair_condition, issue_id?: current caution ID}. repair_condition requires issue_id. Return up to three diverse source options with checked effects.",
    "build_candidate": "{partners: [up to five names]}. Preserve all original locks/avoidance, keep these additional partners and fill remaining slots locally.",
    "change_set": "{species: current name, set_id: ID returned by get_sets}. Change that member's sourced set, then check the full team.",
}
READ_ONLY = {"inspect_team", "search_partners", "get_sets"}


def member_identity(member):
    return {key: member.get(key) for key in ("species", "ability", "item", "moves", "nature", "evs", "ivs", "teraType", "level")}


def fingerprint(team):
    return hashlib.sha256(json.dumps([member_identity(m) for m in team], sort_keys=True).encode()).hexdigest()[:16]


class ToolRefused(ValueError):
    pass


class CoachTools:
    def __init__(self, data, team, locked, avoided, trace, origin, objective="simple"):
        self.data, self.team = data, copy.deepcopy(team)
        self.locked, self.avoided = list(locked), list(avoided)
        self.trace, self.origin = trace, origin
        self.objective = objective
        self.version, self.calls, self.successful_calls = 1, 0, 0
        self.ledger, self.issued_sets, self.snapshots = {}, {}, {}
        self.issued_versions = {}
        self.changes = []
        self.completed_reads = []
        self.delivered_versions = set()
        self.scorer = TeamScorer(data)
        self.assert_constraints(self.team)

    def assert_constraints(self, team):
        names = [m["species"] for m in team]
        if len(team) != 6 or any(name not in names for name in self.locked) or set(names) & set(self.avoided):
            raise ToolRefused("A team must keep six members, all original locked species and all remembered avoidance constraints.")
        bases = [self.data["species"][n]["base_species"] for n in names]
        if len(set(bases)) != 6: raise ToolRefused("Species Clause conflict")
        for member in team:
            fields = ("species", "ability", "item", "moves", "nature", "evs", "ivs", "teraType", "level")
            if not any(all(option.get(key) == member.get(key) for key in fields)
                       for option in self.data["species"][member["species"]]["sets"]):
                raise ToolRefused("Only prepared source set options are permitted.")

    def fact(self, kind, text, *, code=None, pokemon=None):
        key = "E" + str(len(self.ledger) + 1)
        record = {"id": key, "version": self.version, "kind": kind, "text": text}
        if code: record["code"] = code
        if pokemon: record["pokemon"] = pokemon
        self.ledger[key] = record
        return record

    def inspect(self):
        if self.version in self.snapshots: return self.snapshots[self.version]
        self.assert_constraints(self.team)
        check = run_showdown({"operation": "validate", "team": self.team})
        if not check["valid"]: raise ToolRefused("Full-team legality failed; proposal cannot be submitted.")
        evidence = [self.fact("constraint", "Original locked species and recalled avoidance are satisfied; all six sourced sets passed historical Regulation H team validation.")]
        members = []
        for m in self.team:
            coaching = member_guidance(m, self.team, self.data)
            evidence.append(self.fact("member", f"{m['species']}: {m['ability']}; {m['item']}; {m['nature']}; moves: {', '.join(m['moves'])}. Roles: {', '.join(roles(m, self.data))}.", pokemon=[m["species"]]))
            evidence.append(self.fact("speed", f"{m['species']} has ordinary effective Speed {coaching['speed']['ordinary_speed']} at neutral stages. Conditional examples: " + json.dumps(coaching["speed"]["scenarios"]) + ". No opposing speed or damage benchmark was calculated.", pokemon=[m["species"]]))
            members.append({"species": m["species"], "item": m["item"], "ability": m["ability"], "moves": m["moves"], "roles": roles(m, self.data)})
        warnings = []
        for check in interaction_checks(self.team, self.data):
            row = self.fact("caution", check["explanation"], code=check["code"], pokemon=check["pokemon"])
            row["severity"] = check["severity"]
            warnings.append(row["id"]); evidence.append(row)
        support = {"sun": any(m["ability"] == "Drought" for m in self.team),
                   "rain": any(m["ability"] == "Drizzle" for m in self.team),
                   "trick-room": any("Trick Room" in m["moves"] for m in self.team)}
        if self.objective in support and not support[self.objective]:
            evidence.append(self.fact("objective", "The requested " + self.objective + " mode is not supported by an automatic matching weather setter or selected Trick Room move. Add checked support or explicitly offer an alternative; do not claim fulfilment.", code="missing_mode_" + self.objective))
        if self.objective == "reliable":
            from reasoning_contracts import UNSUPPORTED_PLANS
            unsupported = sorted({r["code"] for r in evidence if r.get("code") in UNSUPPORTED_PLANS})
            if unsupported:
                evidence.append(self.fact("objective", "The user requests repair of unsupported item/weather plans. These checked conditions remain: " + ", ".join(unsupported) + ". Merely disclosing them does not fulfil the repair objective; investigate source-backed changes or explicitly decline fulfilment.", code="missing_quality_reliable"))
        from battle_guidance import pair_plan
        from itertools import combinations
        pairs = sorted((pair_plan(a, b, self.data) for a, b in combinations(self.team, 2)), key=lambda p: -p["score"])[:3]
        for pair in pairs:
            evidence.append(self.fact("opening", " + ".join(pair["pokemon"]) + ": " + " ".join(pair["reasons"] + pair["opening_actions"]) + " Conditions: " + " ".join(pair["cautions"]), pokemon=pair["pokemon"]))
        result = {"version": self.version, "fingerprint": fingerprint(self.team), "source": self.origin,
                  "format": self.data["format_id"], "members": members, "evidence": evidence,
                  "caution_ids": warnings, "score_components": self.scorer.components(self.team),
                  "limits": "Historical snapshot, marginal set choices, default 31 IVs, no damage/turn simulation or win probability. Original-type balance and listed conditional checks only."}
        self.snapshots[self.version] = result
        return result

    def commit(self, team, actor, operation):
        self.assert_constraints(team)
        check = run_showdown({"operation": "validate", "team": team})
        if not check["valid"]: raise ToolRefused("The proposed change failed independent full-team legality; current team retained.")
        before = fingerprint(self.team)
        after = fingerprint(check["team"])
        if before == after: return {"changed": False, "version": self.version, "reason": "The selected team is unchanged."}
        old = {m["species"]: m for m in self.team}
        changed = [m["species"] for m in check["team"] if m["species"] not in old or member_identity(old[m["species"]]) != member_identity(m)]
        removed = [m["species"] for m in self.team if m["species"] not in {s["species"] for s in check["team"]}]
        self.team = check["team"]; self.version += 1
        row = {"version": self.version, "operation": operation, "changed_members": changed, "removed_partners": removed,
               "before": before, "after": after,
               "member_changes": [{"species": name, "before": member_identity(old[name]) if name in old else None,
                                   "after": member_identity(next(m for m in check["team"] if m["species"] == name))}
                                  for name in changed]}
        self.changes.append(row)
        self.trace.event(actor, "candidate_revised", **row)
        snapshot = self.inspect()
        self.delivered_versions.add(self.version)
        self.trace.event("Validator", "candidate_checked_after_edit", version=self.version,
                         evidence_ids=[fact["id"] for fact in snapshot["evidence"]], legality_errors=0)
        return {"changed": True, "version": self.version, "changed_members": changed, "removed_partners": removed,
                "checked_state": snapshot,
                "next": "This edit returned fresh checked evidence in shared_state. Submit the current version; older evidence cannot support it."}

    def invoke(self, name, arguments, actor="Planner"):
        self.calls += 1
        if self.calls > 12: raise CoachError("Tool-call budget reached; output withheld.")
        if name not in TOOLS or not isinstance(arguments, dict): raise ToolRefused("Unknown tool or invalid arguments")
        if actor == "Critic" and name not in READ_ONLY: raise ToolRefused("Critic may inspect evidence, not mutate the team.")
        # Log only validated, bounded argument values; never echo arbitrary input.
        if len(json.dumps(arguments)) > 1000: raise ToolRefused("Tool arguments too large")
        read = {"actor": actor, "tool": name, "arguments": arguments, "version": self.version}
        if name in READ_ONLY and read in self.completed_reads:
            raise ToolRefused("This read already completed for the current team. Use the shared evidence or choose a different action.")
        result = self._invoke(name, arguments, actor)
        self.successful_calls += 1
        if name in READ_ONLY: self.completed_reads.append(copy.deepcopy(read))
        self.trace.event(actor, "tool_executed", tool=name, arguments=arguments,
                         version=self.version, data_source=self.origin)
        return result

    def _invoke(self, name, args, actor):
        if name == "inspect_team":
            if args: raise ToolRefused("inspect_team takes no arguments")
            return self.inspect()
        if name == "search_partners":
            if set(args) - {"for_species", "role", "weather"}: raise ToolRefused("Unsupported search argument")
            source = resolve_names([args.get("for_species", self.locked[0])], self.data)[0]
            role, weather = args.get("role", "any"), args.get("weather", "any")
            if role not in {"any", "weather", "speed", "redirection", "pivot"} or weather not in {"any", "sun", "rain"}: raise ToolRefused("Unsupported search filter")
            selected = []
            for mon in self.data["species"].values():
                if not mon["eligible_species"] or not mon["sets"] or mon["name"] in self.avoided or mon["name"] == source: continue
                tags = {r for s in mon["sets"] for r in roles(s, self.data)}
                tag = {"weather": "weather setter", "speed": "speed control", "redirection": "redirection", "pivot": "pivot"}.get(role)
                if tag and tag not in tags: continue
                if weather != "any" and not any(WEATHER.get(s["ability"]) == weather for s in mon["sets"]): continue
                weight = self.data["species"][source]["teammate_weights"].get(mon["name"], 0)
                selected.append((weight, mon["usage"], mon["name"], sorted(tags)))
            selected.sort(reverse=True)
            return {"source": self.origin, "for_species": source, "choices": [{"species": n, "historical_usage_percent": round(u * 100, 3), "roles": tags} for w, u, n, tags in selected[:6]], "note": "Historical co-occurrence/usage, not a win rate or proof of the best partner."}
        if name == "get_sets":
            if set(args) - {"species", "purpose", "issue_id"}: raise ToolRefused("Unsupported set argument")
            species = resolve_names([args.get("species")], self.data)[0]
            if species in self.avoided: raise ToolRefused("That species is avoided")
            purpose = args.get("purpose", "recommended")
            if purpose not in {"recommended", "protection", "no_ally_hit", "different_item", "repair_condition"}: raise ToolRefused("Unsupported set purpose")
            target = None
            if purpose == "repair_condition":
                target = self.cited([args.get("issue_id")])[0]
                if target["kind"] != "caution" or species not in target.get("pokemon", []):
                    raise ToolRefused("Repair search requires a current condition affecting that species")
            elif "issue_id" in args:
                raise ToolRefused("An issue_id is only accepted for repair_condition")
            current = next((m for m in self.team if m["species"] == species), None)
            others = [m for m in self.team if m["species"] != species]
            used = {m["item"] for m in others}
            current_findings = interaction_checks(self.team, self.data)
            current_keys = {(c["code"], tuple(sorted(c["pokemon"]))) for c in current_findings}
            options = []
            for index, member in enumerate(self.data["species"][species]["sets"]):
                if member["item"] in used: continue
                if purpose == "protection" and not set(member["moves"]) & {"Protect", "Detect", "Spiky Shield"}: continue
                if purpose == "no_ally_hit" and any(self.data["moves"][m]["target"] == "allAdjacent" for m in member["moves"]): continue
                if purpose == "different_item" and current and member["item"] == current["item"]: continue
                if target:
                    proposed = interaction_checks(others + [member], self.data)
                    if any(c["code"] == target["code"] and set(c["pokemon"]) == set(target["pokemon"]) for c in proposed): continue
                options.append((self.scorer.score(others + [member]), index, member))
            options.sort(key=lambda row: -row[0])
            # Give the model meaningful alternatives instead of six near-identical
            # EV variants of the same item/ability. The model still selects the ID.
            diverse, seen = [], set()
            for option in options:
                key = (option[2]["item"], option[2]["ability"])
                if key not in seen:
                    diverse.append(option); seen.add(key)
                if len(diverse) == 3: break
            if len(diverse) < 3:
                diverse.extend(option for option in options if option not in diverse)
            result = []
            for score, index, member in diverse[:3]:
                set_id = self.data["species"][species]["id"] + ":" + str(index)
                self.issued_sets[set_id] = copy.deepcopy(member)
                self.issued_versions[set_id] = self.version
                findings = interaction_checks(others + [member], self.data)
                new_keys = {(c["code"], tuple(sorted(c["pokemon"]))) for c in findings}
                result.append({"set_id": set_id, "species": species, "ability": member["ability"], "item": member["item"], "moves": member["moves"],
                               "nature": member["nature"], "evs": member["evs"], "version": self.version,
                               "resolves": sorted({code for code, names in current_keys - new_keys}),
                               "introduces": sorted({code for code, names in new_keys - current_keys}),
                               "conditional_cautions": [c["explanation"] for c in findings if species in c["pokemon"]]})
            return {"source": self.origin, "purpose": purpose, "options": result}
        if name == "build_candidate":
            if set(args) != {"partners"} or not isinstance(args["partners"], list) or len(args["partners"]) > 5: raise ToolRefused("Expected up to five partner names")
            partners = resolve_names(args["partners"], self.data)
            locks = self.locked + [name for name in partners if name not in self.locked]
            if len(locks) > 6 or len(set(locks)) != len(locks): raise ToolRefused("Too many or duplicate partners")
            candidate, _, _ = build_team(self.data, locks, self.avoided)
            return self.commit(candidate, actor, name)
        if name == "change_set":
            if set(args) != {"species", "set_id"} or not isinstance(args["set_id"], str): raise ToolRefused("Expected species and a previously returned set_id")
            species = resolve_names([args["species"]], self.data)[0]
            option = self.issued_sets.get(args["set_id"])
            if not option or option["species"] != species: raise ToolRefused("Set ID was not supplied by get_sets for that species")
            if self.issued_versions.get(args["set_id"]) != self.version: raise ToolRefused("Set options came from an older team version; request current options")
            if species not in {m["species"] for m in self.team}: raise ToolRefused("Species is not in the current team")
            return self.commit([copy.deepcopy(option) if m["species"] == species else m for m in self.team], actor, name)

    def cited(self, ids, *, require_cautions=False):
        if not isinstance(ids, list) or len(ids) > 40 or any(not isinstance(i, str) for i in ids): raise ToolRefused("Expected bounded evidence IDs")
        facts = []
        for key in dict.fromkeys(ids):
            row = self.ledger.get(key)
            if not row or row["version"] != self.version: raise ToolRefused("Unknown or stale evidence ID")
            facts.append(row)
        if require_cautions and not set(self.inspect()["caution_ids"]) <= {f["id"] for f in facts}:
            raise ToolRefused("Every remaining caution must be explicitly acknowledged before approval")
        return facts
