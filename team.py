"""DoublesCheck: local planning or explicit Nightshift/Nemotron AI coaching."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

from catalogue import ROOT, load_catalogue
from hmem_memory import recall_preferences
from team_builder import build_team, explain_team, resolve_names

class Trace:
    def __init__(self, directory, run_id=None):
        import re
        self.id = run_id or uuid.uuid4().hex
        if not isinstance(self.id, str) or not re.fullmatch(r"[a-f0-9]{32}", self.id):
            raise ValueError("Invalid run identifier.")
        self.directory = directory / self.id
        try:
            self.directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ValueError("This run already exists. Submit a new request.") from None
        self.events = []
        self.model_calls = 0
    def event(self, agent, action, **details):
        event = {"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": self.id,
                 "agent": agent, "action": action, **details}
        self.events.append(event)
        with (self.directory / "trace.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

def execute(favourites=None, avoided=None, sample=False, profile="default", output=None,
            env_file=None, clear_avoidance=False, run_id=None, ai=False, objective="simple", ai_client=None):
    if type(ai) is not bool: raise ValueError("Choose a valid planning mode.")
    if ai and sample: raise ValueError("Offline sample makes no model calls. Choose connected Zetaris data for Nightshift AI, or use local planning.")
    from agent_tools import OBJECTIVES
    if objective not in OBJECTIVES: raise ValueError("Choose a supported coaching objective.")
    trace = Trace(Path(output or ROOT / "runs"), run_id)
    client = ai_client
    own_client = False
    try:
        trace.event("DataRetriever", "catalogue_requested", mode="sample" if sample else "zetaris")
        data, origin = load_catalogue(sample, env_file)
        trace.event("DataRetriever", "catalogue_loaded", source=origin,
                    format=data["format_id"], rows=len(data["species"]))
        # Validate explicit preferences before persisting them; no speculative memory writes.
        names = resolve_names(favourites or [], data)
        avoid = resolve_names([avoided], data)[0] if avoided else None
        if names:
            for name in names:
                if not data["species"][name]["eligible_species"]:
                    raise ValueError(f"{name} is not eligible in historical Regulation H.")
            if not 1 <= len(names) <= 6: raise ValueError("Choose one to six favourites.")
        updates = {}
        if names: updates["favourite"] = names[0]
        if avoid: updates["avoided_partner"] = avoid
        if clear_avoidance: updates["avoided_partner"] = None
        memory = recall_preferences(ROOT / ".doublescheck-memory", profile, updates)
        names = names or [memory.get("favourite", "Charizard")]
        avoided_names = [memory["avoided_partner"]] if memory.get("avoided_partner") else []
        trace.event("H-MEM", "preferences_recalled", profile=profile,
                    memory_ids=[m["id"] for m in memory["memories"]], locked=names, avoided=avoided_names)
        team, validation, locked = build_team(data, names, avoided_names, trace)
        coaching = None
        if ai:
            from ai_coach import run_coach
            from nightshift_client import NightshiftClient
            if client is None:
                client = NightshiftClient(trace, allow_live=True, env_file=env_file)
                own_client = True
            team, validation, coaching = run_coach(data, team, locked, avoided_names, memory,
                                                  trace, client, objective=objective, origin=origin)
        explanation = explain_team(team, data, locked)
        trace.event("BattleCoach", "battle_guidance_checked", leads=len(explanation["possible_leads"]),
                    interaction_codes=sorted({row["code"] for row in explanation["interactions"]}),
                    speed_scope="Neutral stages; listed conditions only", model_calls=trace.model_calls)
        result = {"name": "DoublesCheck", "trace_id": trace.id,
            "mode": "sample" if sample else "zetaris", "data_source": origin,
            "format": data["format_name"], "format_id": data["format_id"],
            "model_calls": trace.model_calls, "ai_coach": coaching, "engine": "Meterless H-MEM", "locked": locked,
            "legality": {"status": "passed_showdown_validator", "scope": "Historical Regulation H team and set rules; not official certification or current-event eligibility.", "errors": validation["errors"]},
            "team": team, "showdown_export": validation["export"], **explanation,
            "sources": json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))["sources"],
            "statistics": data["statistics"], "set_method": data["set_method"],
            "memory_used": {"profile": profile, "ids": [m["id"] for m in memory["memories"]], "avoided_partner": memory.get("avoided_partner")}}
        trace.event("ReportWriter", "report_writing")
        (trace.directory / "report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (trace.directory / "team.txt").write_text(validation["export"], encoding="utf-8")
        from report import render
        (trace.directory / "report.html").write_text(render(result), encoding="utf-8")
        trace.event("Orchestrator", "report_approved", legality_errors=0, model_calls=trace.model_calls,
                    team=[s["species"] for s in team])
        return result, trace.directory
    except Exception:
        trace.event("Orchestrator", "run_failed", model_calls=trace.model_calls)
        raise
    finally:
        if own_client and client is not None:
            client.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--favourites", "--lock", nargs="+", help="One to six species; quote form names with spaces")
    parser.add_argument("--avoid-partner")
    parser.add_argument("--allow-all-partners", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Bundled real-data snapshot, no services/keys required")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--ai", action="store_true", help="Explicitly call the approved Nemotron model through local Nightshift; connected data required")
    parser.add_argument("--objective", choices=["simple", "sun", "rain", "trick-room"], default="simple")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    if args.avoid_partner and args.allow_all_partners: parser.error("Choose avoidance or clearing it, not both.")
    result, folder = execute(args.favourites, args.avoid_partner, args.sample, args.profile,
                             args.output, args.env_file, args.allow_all_partners, ai=args.ai, objective=args.objective)
    print("DoublesCheck | Historical VGC Regulation H | Model calls:", result["model_calls"])
    print("Data:", result["data_source"])
    print("Team:", ", ".join(m["species"] for m in result["team"]))
    print("Legality: passed local Showdown validator for the selected historical format.")
    print("Open report:", folder / "report.html")
    print("Showdown import:", folder / "team.txt")

if __name__ == "__main__":
    try: main()
    except (ValueError, RuntimeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
