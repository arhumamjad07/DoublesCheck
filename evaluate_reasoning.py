"""Reproducible acceptance suite. Offline by default; live is explicit and bounded."""
import argparse
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
import time
import uuid

from catalogue import ROOT, load_catalogue
from hmem_memory import recall_preferences
from nightshift_client import NightshiftClient, CoachError
from ai_coach import CoachPaused
from team import execute, resume_review, Trace
from reasoning_cases import CASES, check_result, seed_fixture
from team_builder import build_team


def implementation_hash():
    digest = hashlib.sha256()
    paths = [p for suffix in ("*.py", "*.mjs", "*.cjs", "*.ts") for p in ROOT.glob(suffix)]
    paths += [ROOT/"data/sources.json", ROOT/"historical-formats-source.json", ROOT/"vendor/hmem/UPSTREAM.json"]
    for path in sorted(paths):
        if path.name.startswith("test_"): continue
        digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


class SuiteBudget:
    def __init__(self, maximum): self.maximum, self.calls = maximum, 0

    def factory(self, trace, **kwargs):
        budget = self
        class BudgetedClient(NightshiftClient):
            def call(self, *args, **options):
                if budget.calls >= budget.maximum:
                    raise CoachError("Acceptance-suite request budget reached. No extra model request was sent.", code="suite_budget")
                before = self.calls
                try: return super().call(*args, **options)
                finally: budget.calls += self.calls-before
        return BudgetedClient(trace, **kwargs)


def render_summary(summary):
    rows = []
    for row in summary["cases"]:
        links = f'<a href="../{row["run_id"]}/trace.jsonl">Trace</a>'
        if row.get("team_approved"): links += f' · <a href="../{row["run_id"]}/report.html">Team report</a>'
        rows.append(f'<tr><th>{escape(row["case"])}</th><td>{escape(row["test_status"])}</td><td>{escape(row["application_outcome"])}</td><td>{row["model_requests"]}</td><td>{escape(", ".join(row.get("unmet_expectations", [])) or "—")}</td><td>{links}</td></tr>')
    metrics = summary["metrics"]
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DoublesCheck reasoning acceptance</title>
<style>body{{max-width:1200px;margin:40px auto;padding:0 20px;background:#101b20;color:#edf5ed;font:16px/1.6 system-ui}}a{{color:#bce4b2}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:12px;border-bottom:1px solid #456}}.scroll{{overflow:auto}}code{{word-break:break-all}}p{{max-width:900px}}</style>
<h1>Reasoning acceptance: {escape(summary["mode"])}</h1><p>{metrics["passed"]} passed, {metrics["failed"]} failed, {metrics["skipped"]} skipped. Model requests: {metrics["model_requests"]} / {summary["request_budget"]}.</p>
<p><b>Live approved team reports: {metrics["live_team_approvals"]}.</b> Expected input refusals and offline checks are separate evidence; they are not successful live AI reviews. A completed team can still fail its acceptance expectation, such as an unmet user objective.</p>
<p>The seed-repair case is a declared synthetic fixture containing a real legal-but-unsupported item condition. No model response, verdict or repair is scripted in live mode. Failed attempts stay in this report. Provider failures are not relabelled as successes.</p>
<div class="scroll"><table><thead><tr><th>Case</th><th>Acceptance</th><th>Application outcome</th><th>Model requests</th><th>Unmet expectations</th><th>Evidence</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p>Code fingerprint: <code>{summary["implementation_sha256"]}</code>. Format: historical VGC Regulation H; no competitive win-rate claim.</p><p><a href="report.json">Structured evaluation</a></p></html>'''


def run_suite(names, *, live=False, env_file=None, max_requests=24, resume_once=False):
    if not names or len(names) != len(set(names)) or any(name not in CASES for name in names): raise ValueError("Choose unique declared case names")
    if type(max_requests) is not int or not 1 <= max_requests <= 40: raise ValueError("Suite budget must be 1–40 model requests")
    suite_trace = Trace(ROOT/"runs")
    budget = SuiteBudget(max_requests)
    summary = {"kind": "reasoning_acceptance_suite", "mode": "live" if live else "offline",
               "created_at": datetime.now(timezone.utc).isoformat(), "implementation_sha256": implementation_hash(),
               "request_budget": max_requests if live else 0, "explicit_one_continuation_per_case": resume_once,
               "cases": []}
    def save():
        rows = summary["cases"]
        summary["metrics"] = {"passed": sum(r["test_status"] == "passed" for r in rows),
            "failed": sum(r["test_status"] == "failed" for r in rows), "skipped": sum(r["test_status"] == "skipped" for r in rows),
            "model_requests": budget.calls,
            "live_team_approvals": sum(live and r.get("team_approved", False) for r in rows)}
        (suite_trace.directory/"report.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
        (suite_trace.directory/"report.html").write_text(render_summary(summary),encoding="utf-8")
    for name in names:
        case = CASES[name]
        run_id = uuid.uuid4().hex
        profile = "eval-" + suite_trace.id[:8] + "-" + name
        clients = []
        def factory(trace, **options):
            client = budget.factory(trace, **options); clients.append(client); return client
        row = {"case": name, "run_id": run_id, "declared_fixture": case.fixture,
               "test_status": "failed", "application_outcome": "not_started", "team_approved": False,
               "model_requests": 0, "unmet_expectations": [], "explicit_continuations": 0}
        summary["cases"].append(row)
        before, started = budget.calls, time.monotonic()
        print(json.dumps({"case":name,"phase":"starting","live":live}),flush=True)
        try:
            if not live and case.objective not in {"simple", "reliable"}:
                row.update(test_status="skipped", application_outcome="requires_live_objective_evaluation")
                continue
            candidate = None
            if case.fixture:
                data, _ = load_catalogue(not live, env_file)
                candidate = seed_fixture(data)
            if case.remembered:
                recall_preferences(ROOT/".doublescheck-memory",profile,{"favourite":"Charizard","avoided_partner":case.avoided or "Incineroar"})
            try:
                result, folder = execute(list(case.favourites) or None, None if case.remembered else case.avoided, sample=not live,
                    profile=profile, run_id=run_id, ai=live, objective=case.objective if live else "simple",
                    env_file=env_file, review_candidate=candidate, ai_factory=factory if live else None, allow_resume=live)
            except CoachPaused as error:
                row["interruption_code"] = error.code
                if not resume_once: raise
                row["explicit_continuations"] = 1
                print(json.dumps({"case":name,"phase":"explicit_continuation","remaining_case_requests":8-error.session.client.calls}),flush=True)
                time.sleep(2)
                result, folder = resume_review(error.run_id)
            row["team_approved"] = True
            row["application_outcome"] = "live_approved" if live else "local_validated"
            row["unmet_expectations"] = check_result(case,result,live)
            if name == "memory-changes-team":
                reference_data,_ = load_catalogue(not live,env_file)
                reference,_,_ = build_team(reference_data,["Charizard"])
                row["unconstrained_reference"] = [m["species"] for m in reference]
                row["memory_changed_output"] = case.avoided in row["unconstrained_reference"] and case.avoided not in [m["species"] for m in result["team"]]
                if not row["memory_changed_output"]: row["unmet_expectations"].append("memory_effect_not_demonstrated")
            if case.expected_refusal: row["unmet_expectations"].append("invalid_request_was_accepted")
            row["test_status"] = "failed" if row["unmet_expectations"] else "passed"
            if result.get("ai_coach"):
                c=result["ai_coach"]
                row.update(actual_models=c["actual_models"], changed=c["changed_from_local_baseline"], revision_rounds=c["revision_rounds"],
                           contracts=[{"code":r["code"],"resolution":r["resolution"],"status":r["status"]} for r in c["revision_contracts"]],
                           goal_met=c["objective_assessment"]["met"])
        except ValueError:
            row["application_outcome"] = "input_refused"
            row["test_status"] = "passed" if case.expected_refusal and budget.calls == before else "failed"
            if row["test_status"] == "failed": row["unmet_expectations"] = ["unexpected_input_refusal"]
        except CoachError as error:
            row.update(application_outcome="model_withheld", error_code=error.code, unmet_expectations=["model_review_not_completed"])
        except Exception as error:
            row.update(application_outcome="service_or_application_failure", error_kind=type(error).__name__, unmet_expectations=["workflow_not_completed"])
        finally:
            row["model_requests"] = budget.calls-before
            row["seconds"] = round(time.monotonic()-started,3)
            save()
            print(json.dumps({"case":name,"test_status":row["test_status"],"application_outcome":row["application_outcome"],"model_requests":row["model_requests"]}),flush=True)
    suite_trace.event("Evaluation","evaluation_suite_completed",**summary["metrics"])
    print("Evaluation report: " + str(suite_trace.directory/"report.html"),flush=True)
    return summary, suite_trace.directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true",help="Explicitly use connected Zetaris and the approved Nightshift NVIDIA route")
    parser.add_argument("--cases",nargs="+",choices=sorted(CASES),default=list(CASES))
    parser.add_argument("--env-file",type=Path)
    parser.add_argument("--max-model-requests",type=int,default=24)
    parser.add_argument("--resume-once",action="store_true",help="Explicitly authorize one continuation after an interruption in each case; the original case/suite budgets remain enforced")
    args=parser.parse_args()
    summary,_=run_suite(args.cases,live=args.live,env_file=args.env_file,max_requests=args.max_model_requests,resume_once=args.resume_once)
    raise SystemExit(1 if summary["metrics"]["failed"] else 0)


if __name__=="__main__":main()
