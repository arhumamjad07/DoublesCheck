"""DoublesCheck: local planning or explicit Nightshift/Nemotron AI coaching."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid
import threading
import time
import copy

from catalogue import ROOT, load_catalogue
from hmem_memory import recall_preferences
from team_builder import build_team, explain_team, resolve_names
from ai_coach import CoachPaused

_PENDING_RUNS = {}
_PENDING_LOCK = threading.Lock()
PAUSE_SECONDS = 1800


def _discard_pending(record):
    record["session"].dispose()
    if record["own_client"]: record["session"].client.close()


def _save_pending(run_id, record):
    with _PENDING_LOCK:
        expired = [key for key, row in _PENDING_RUNS.items() if time.monotonic() - row["saved_at"] > PAUSE_SECONDS]
        for key in expired: _discard_pending(_PENDING_RUNS.pop(key))
        if len(_PENDING_RUNS) >= 4:
            oldest = min(_PENDING_RUNS, key=lambda key: _PENDING_RUNS[key]["saved_at"])
            _discard_pending(_PENDING_RUNS.pop(oldest))
        _PENDING_RUNS[run_id] = record

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

def write_team_report(data, team, validation, locked, memory, trace, *, sample, origin, profile, coaching=None):
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


def resume_review(run_id):
    import re
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-f0-9]{32}", run_id): raise ValueError("Invalid review identifier.")
    with _PENDING_LOCK: record = _PENDING_RUNS.pop(run_id, None)
    if record is None: raise ValueError("This paused review is unavailable or already running. Start a new review if the app restarted.")
    if time.monotonic() - record["saved_at"] > PAUSE_SECONDS:
        _discard_pending(record)
        raise ValueError("The continuation window expired. Start a new review.")
    context = record["context"]
    keep = False
    try:
        current = recall_preferences(ROOT / ".doublescheck-memory", context["profile"], {})
        if any(current.get(key) != context["memory"].get(key) for key in ("favourite", "avoided_partner")):
            raise ValueError("Your preferences changed after this review paused. Start a new review so the latest preferences are respected.")
        team, validation, coaching = record["session"].advance()
        return write_team_report(context["data"], team, validation, context["locked"], context["memory"], context["trace"],
                                 sample=context["sample"], origin=context["origin"], profile=context["profile"], coaching=coaching)
    except CoachPaused as error:
        record["saved_at"] = time.monotonic(); _save_pending(run_id, record); keep = True
        error.run_id = run_id
        context["trace"].event("Orchestrator", "run_paused", model_calls=record["session"].client.calls)
        raise
    except Exception:
        context["trace"].event("Orchestrator", "run_failed", model_calls=record["session"].client.calls)
        raise
    finally:
        if not keep: _discard_pending(record)


def canonical_candidate(data, candidate):
    """Accept only exact prepared sets; discard unrecognised input metadata."""
    from agent_tools import member_identity
    if not isinstance(candidate, list) or len(candidate) != 6: raise ValueError("Provide exactly six prepared source sets for review.")
    result = []
    for member in candidate:
        if not isinstance(member, dict) or not isinstance(member.get("species"), str) or member["species"] not in data["species"]:
            raise ValueError("Provided team contains an unknown species or invalid set.")
        option = next((s for s in data["species"][member["species"]]["sets"] if member_identity(s) == member_identity(member)), None)
        if option is None: raise ValueError("Provided team contains a set outside this prepared source snapshot. No model request was sent.")
        result.append(copy.deepcopy(option))
    if len({data["species"][m["species"]]["base_species"] for m in result}) != 6:
        raise ValueError("Provided team violates Species Clause. Preferences were not updated.")
    return result


def execute(favourites=None, avoided=None, sample=False, profile="default", output=None,
            env_file=None, clear_avoidance=False, run_id=None, ai=False, objective="simple", ai_client=None, allow_resume=False,
            review_candidate=None, ai_factory=None):
    if type(ai) is not bool: raise ValueError("Choose a valid planning mode.")
    if ai and sample: raise ValueError("Offline sample makes no model calls. Choose connected Zetaris data for Nightshift AI, or use local planning.")
    if not ai and objective != "simple": raise ValueError("Custom coaching objectives require Nightshift AI. Local planning uses the balanced baseline.")
    from agent_tools import OBJECTIVES
    if objective not in OBJECTIVES: raise ValueError("Choose a supported coaching objective.")
    trace = Trace(Path(output or ROOT / "runs"), run_id)
    client = ai_client
    own_client = False
    keep_client = False
    try:
        trace.event("DataRetriever", "catalogue_requested", mode="sample" if sample else "zetaris")
        data, origin = load_catalogue(sample, env_file)
        trace.event("DataRetriever", "catalogue_loaded", source=origin,
                    format=data["format_id"], rows=len(data["species"]))
        provided = canonical_candidate(data, review_candidate) if review_candidate is not None else None
        provided_validation = None
        if provided is not None:
            from catalogue import run_showdown
            provided_validation = run_showdown({"operation":"validate","team":provided})
            if not provided_validation["valid"]: raise ValueError("The provided team failed full-team legality checks. Preferences were not updated and no model request was sent.")
        # Validate explicit preferences before persisting them; no speculative memory writes.
        names = resolve_names(favourites or [], data)
        avoid = resolve_names([avoided], data)[0] if avoided else None
        if names:
            for name in names:
                if not data["species"][name]["eligible_species"]:
                    raise ValueError(f"{name} is not eligible in historical Regulation H.")
                if not data["species"][name]["sets"]:
                    raise ValueError(f"No prepared source sets are available for {name} in this snapshot.")
            if not 1 <= len(names) <= 6: raise ValueError("Choose one to six favourites.")
            if len({data["species"][name]["base_species"] for name in names}) != len(names):
                raise ValueError("Locked favourites must satisfy Species Clause; remove duplicate species or forms.")
            from team_builder import item_assignment_possible
            if not item_assignment_possible(data["species"], names, set()):
                raise ValueError("Locked favourites cannot satisfy Item Clause with prepared source sets. Preferences were not updated.")
            if provided is not None and not set(names) <= {m["species"] for m in provided}:
                raise ValueError("The provided team does not contain all locked favourites. Preferences were not updated.")
        if clear_avoidance and avoid: raise ValueError("Choose an avoided teammate or clear avoidance, not both.")
        updates = {}
        if names: updates["favourite"] = names[0]
        if avoid: updates["avoided_partner"] = avoid
        if clear_avoidance: updates["avoided_partner"] = None
        memory = recall_preferences(ROOT / ".doublescheck-memory", profile, updates, locked=names)
        names = names or [memory.get("favourite", "Charizard")]
        avoided_names = [memory["avoided_partner"]] if memory.get("avoided_partner") else []
        trace.event("H-MEM", "preferences_recalled", profile=profile,
                    memory_ids=[m["id"] for m in memory["memories"]], locked=names, avoided=avoided_names)
        if provided is None:
            team, validation, locked = build_team(data, names, avoided_names, trace)
        else:
            from agent_tools import CoachTools
            from catalogue import run_showdown
            tools = CoachTools(data, provided, names, avoided_names, trace, origin, objective)
            validation = provided_validation
            team, locked = validation["team"], names
            trace.event("InputReviewer", "provided_team_checked", source_sets=True, legality_errors=0, locked=locked)
        coaching = None
        if ai:
            from ai_coach import run_coach
            from nightshift_client import NightshiftClient
            if client is None:
                client = (ai_factory or NightshiftClient)(trace, allow_live=True, env_file=env_file)
                own_client = True
            team, validation, coaching = run_coach(data, team, locked, avoided_names, memory,
                                                  trace, client, objective=objective, origin=origin, review_first=True,
                                                  candidate_origin="provided_team" if provided is not None else "local_builder")
        return write_team_report(data, team, validation, locked, memory, trace, sample=sample, origin=origin, profile=profile, coaching=coaching)
    except CoachPaused as error:
        if allow_resume:
            keep_client = True
            _save_pending(trace.id, {"session": error.session, "saved_at": time.monotonic(), "own_client": own_client,
                                   "context": {"data": data, "locked": locked, "memory": memory, "trace": trace, "sample": sample, "origin": origin, "profile": profile}})
            error.run_id = trace.id
            trace.event("Orchestrator", "run_paused", model_calls=trace.model_calls)
            raise
        error.session.dispose()
        trace.event("Orchestrator", "run_failed", model_calls=trace.model_calls)
        from nightshift_client import CoachError
        raise CoachError(str(error), code=error.code, retryable=True) from None
    except Exception:
        trace.event("Orchestrator", "run_failed", model_calls=trace.model_calls)
        raise
    finally:
        if own_client and client is not None and not keep_client:
            client.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--favourites", "--lock", nargs="+", help="One to six species; quote form names with spaces")
    parser.add_argument("--avoid-partner")
    parser.add_argument("--allow-all-partners", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Bundled real-data snapshot, no services/keys required")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--ai", action="store_true", help="Explicitly call the approved Nemotron model through local Nightshift; connected data required")
    parser.add_argument("--objective", choices=["simple", "sun", "rain", "trick-room", "reliable"], default="simple")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--review-team", type=Path, help="Review a JSON list or previous report containing six exact prepared source sets")
    args = parser.parse_args()
    if args.avoid_partner and args.allow_all_partners: parser.error("Choose avoidance or clearing it, not both.")
    candidate = None
    if args.review_team:
        raw = json.loads(args.review_team.read_text(encoding="utf-8"))
        candidate = raw.get("team") if isinstance(raw, dict) else raw
    result, folder = execute(args.favourites, args.avoid_partner, args.sample, args.profile,
                             args.output, args.env_file, args.allow_all_partners, ai=args.ai, objective=args.objective, review_candidate=candidate)
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
