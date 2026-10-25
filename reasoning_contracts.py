"""Check that a revision fixes its named issue, rather than merely changing a team."""
import copy

from agent_tools import ToolRefused, member_identity


def finding_key(fact):
    return (fact.get("code"), tuple(sorted(fact.get("pokemon", []))))


GLOBAL_CONDITIONS = {"competing_weather", "competing_terrain", "double_room", "ability_suppression"}
UNSUPPORTED_PLANS = {"missing_seed_terrain", "missing_weather", "solar_charge", "vest_status"}


def matches_issue(fact, record):
    if fact["kind"] != record["kind"]: return False
    if record.get("code"):
        return fact.get("code") == record["code"] and (record["code"] in GLOBAL_CONDITIONS or finding_key(fact) == (record["code"],tuple(record["pokemon"])))
    return bool(set(fact.get("pokemon", [])) & set(record["pokemon"]))


class RevisionContracts:
    def __init__(self, trace=None):
        self.records = []
        self.trace, self.statuses = trace, {}

    def request(self, issues, tools):
        additions = []
        for issue in issues:
            fact = tools.cited([issue["evidence_id"]])[0]
            if issue["resolution"] == "change" and fact["kind"] not in {"caution", "member", "objective"}:
                raise ToolRefused("A change request must identify a specific condition, member or objective fact")
            if fact["kind"] == "caution" and not fact.get("code"):
                raise ToolRefused("A condition change requires a checked finding code")
            targets = set(fact.get("pokemon", []))
            row = {"id": "R" + str(len(self.records) + len(additions) + 1),
                   "requested_version": tools.version, "evidence_id": fact["id"],
                   "resolution": issue["resolution"], "kind": fact["kind"],
                   "code": fact.get("code"), "pokemon": sorted(targets),
                   "problem": fact["text"],
                   "before_members": [member_identity(m) for m in tools.team if m["species"] in targets]}
            if row["kind"] == "member" and not row["before_members"]:
                raise ToolRefused("Member criticism must identify a current member")
            additions.append(row)
        # Commit only after every issue has passed validation.
        self.records.extend(copy.deepcopy(additions))
        if self.trace:
            for row in additions:
                self.trace.event("Critic", "revision_contract_created", contract_id=row["id"], version=row["requested_version"],
                                 evidence_id=row["evidence_id"], finding_code=row["code"], resolution=row["resolution"], pokemon=row["pokemon"])
        return self.view(tools)

    def view(self, tools):
        current = tools.inspect()
        facts = current["evidence"]
        members = {m["species"]: member_identity(m) for m in tools.team}
        rows = []
        for record in self.records:
            row = copy.deepcopy(record)
            related = [f for f in facts if set(f.get("pokemon", [])) & set(row["pokemon"])]
            if row["resolution"] == "disclose":
                row["status"] = "disclose"
            elif row["kind"] in {"caution", "objective"}:
                persists = any(matches_issue(f,row) for f in facts)
                row["status"] = "open" if persists or tools.version <= row["requested_version"] else "resolved"
            else:
                changed = any(members.get(m["species"]) != m for m in row["before_members"])
                row["status"] = "resolved" if changed and tools.version > row["requested_version"] else "open"
            row["current_version"] = tools.version
            row["current_evidence_ids"] = [f["id"] for f in related]
            if self.trace and self.statuses.get(row["id"]) != row["status"]:
                self.trace.event("PolicyGuard", "revision_contract_status", contract_id=row["id"], version=tools.version,
                                 finding_code=row["code"], status=row["status"], current_evidence_ids=row["current_evidence_ids"])
                self.statuses[row["id"]] = row["status"]
            rows.append(row)
        return rows

    def ensure_resolved(self, tools):
        rows = self.view(tools)
        if any(row["status"] == "open" for row in rows):
            raise ToolRefused("The requested problem still exists. An unrelated edit or a different unsupported condition does not satisfy the revision contract")
        return rows


def objective_assessment(objective, strategy, team, data=None):
    """Describe whether a requested mode was actually delivered, without inventing a promise."""
    capabilities = {
        "sun": [m["species"] for m in team if m["ability"] == "Drought"],
        "rain": [m["species"] for m in team if m["ability"] == "Drizzle"],
        "trick-room": [m["species"] for m in team if "Trick Room" in m["moves"]],
    }
    if objective == "reliable":
        from battle_guidance import interaction_checks
        remaining = [c["code"] for c in interaction_checks(team, data) if c["code"] in UNSUPPORTED_PLANS] if data else ["not_checked"]
        met = not remaining
        support = []
    else:
        met = objective == "simple" or (strategy == objective and bool(capabilities.get(objective)))
        remaining = []
        support = capabilities.get(objective, [])
    return {"requested": objective, "selected_strategy": strategy, "met": met,
            "support": support, "remaining_unsupported_conditions": remaining,
            "explanation": ("The selected plan supports the requested objective within the documented scope."
                            if met else "The requested mode was not delivered. This is an explicitly labelled alternative, not a successful fulfilment of that objective.")}
