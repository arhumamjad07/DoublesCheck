"""DoublesCheck: build/review six Pokemon in historical VGC Regulation H, with no AI-credit usage."""
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
    def event(self, agent, action, **details):
        event = {"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": self.id,
                 "agent": agent, "action": action, **details}
        self.events.append(event)
        with (self.directory / "trace.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

def execute(favourites=None, avoided=None, sample=False, profile="default", output=None,
            env_file=None, clear_avoidance=False, run_id=None):
    trace = Trace(Path(output or ROOT / "runs"), run_id)
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
        explanation = explain_team(team, data, locked)
        trace.event("BattleCoach", "battle_guidance_checked", leads=len(explanation["possible_leads"]),
                    interaction_codes=sorted({row["code"] for row in explanation["interactions"]}),
                    speed_scope="Neutral stages; listed conditions only", model_calls=0)
        result = {"name": "DoublesCheck", "trace_id": trace.id,
            "mode": "sample" if sample else "zetaris", "data_source": origin,
            "format": data["format_name"], "format_id": data["format_id"],
            "model_calls": 0, "engine": "Meterless H-MEM", "locked": locked,
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
        trace.event("Orchestrator", "report_approved", legality_errors=0, model_calls=0,
                    team=[s["species"] for s in team])
        return result, trace.directory
    except Exception:
        trace.event("Orchestrator", "run_failed", model_calls=0)
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--favourites", "--lock", nargs="+", help="One to six species; quote form names with spaces")
    parser.add_argument("--avoid-partner")
    parser.add_argument("--allow-all-partners", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Bundled real-data snapshot, no services/keys required")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    if args.avoid_partner and args.allow_all_partners: parser.error("Choose avoidance or clearing it, not both.")
    result, folder = execute(args.favourites, args.avoid_partner, args.sample, args.profile,
                             args.output, args.env_file, args.allow_all_partners)
    print("DoublesCheck | Historical VGC Regulation H | No model calls")
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
