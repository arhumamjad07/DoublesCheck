"""Local status/roadmap view and progress derived from real run events."""
from html import escape
import json
import re
from catalogue import ROOT

RUBRIC = [
    ("Impact", 30, "Clear beginner problem", "Show that beginners understand their team better; no user study yet."),
    ("Technical", 20, "Working and tested foundation", "Test the stronger local coach with players and restore reliable AI reasoning."),
    ("Innovation", 15, "Promising angle, unproven differentiation", "Demonstrate a favourite-preserving coach that critiques and improves a team."),
    ("Demo", 15, "Working flow, recording unfinished", "Record a repeatable 1–4 minute demonstration with sources and sponsor use."),
    ("Product & UX", 10, "Basic local GUI and reports", "Make advice actionable and test the interface with beginners."),
    ("Sponsor Tech", 10, "Zetaris and H-MEM working", "Main product still needs the Nightshift AI feature; older Nemotron demo is separate."),
]

def progress(run_id, root=ROOT):
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise ValueError("Invalid run identifier.")
    file = root / "runs" / run_id / "trace.jsonl"
    if not file.is_file(): return {"run_id": run_id, "status": "waiting", "events": []}
    events = []
    with file.open(encoding="utf-8") as handle:
        lines = handle.read(256_000).splitlines()
    labels = {"catalogue_requested": "Loading the selected Pokemon dataset",
        "catalogue_loaded": "Pokemon data loaded", "preferences_recalled": "Remembered preferences applied",
        "locked_favourites_checked": "Your locked choices checked", "team_checked": "Full team legality checked",
        "team_quality_checked": "Checked weather, terrain, items and partner interactions",
        "battle_guidance_checked": "Calculated stats, conditional Speed and opening plans",
        "report_writing": "Writing explanations and your Showdown export",
        "report_approved": "Report ready", "run_failed": "Build stopped; see the form's error message"}
    for line in lines:
        try: event = json.loads(line)
        except ValueError: continue  # An actively written last line may be incomplete.
        if not isinstance(event, dict) or event.get("trace_id") != run_id: continue
        action = event.get("action")
        label = labels.get(action)
        if action == "candidate_slot_filled": label = f"Searched teammates for slot {event.get('slots')} of 6"
        if label: events.append({"action": action, "label": label, "time": event.get("timestamp")})
    status = "running"
    if events and events[-1]["action"] == "report_approved": status = "complete"
    if events and events[-1]["action"] == "run_failed": status = "failed"
    return {"run_id": run_id, "status": status, "events": events}

def dashboard(root=ROOT):
    rows = "".join(f'<tr><th>{escape(name)}<small>{points} points</small></th><td>{escape(state)}</td><td>{escape(next_step)}</td></tr>'
                   for name, points, state, next_step in RUBRIC)
    traces = sorted((root / "runs").glob("*/trace.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    recent = []
    for file in traces:
        if not re.fullmatch(r"[a-f0-9]{32}", file.parent.name): continue
        result = progress(file.parent.name, root)
        label = result["events"][-1]["label"] if result["events"] else "Waiting for events"
        report = file.with_name("report.html")
        link = f'<a href="/runs/{result["run_id"]}/report.html">Open report</a>' if report.is_file() else "No report published"
        recent.append(f'<li><b>{escape(result["status"])}</b> — {escape(label)}<br><code>{result["run_id"][:12]}</code> · {link}</li>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DoublesCheck · Build status</title><style>
    :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#101b20;color:#edf5ed;font:16px/1.6 system-ui}main{max-width:1120px;margin:auto;padding:38px 24px 70px}a{color:#bce4b2}nav{display:flex;gap:24px;margin-bottom:30px}h1{font-size:clamp(34px,5vw,58px);line-height:1.1;letter-spacing:-.035em}.intro{max-width:820px;color:#b2c6c6}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}article,section{background:#17272c;border:1px solid #34474c;padding:24px;border-radius:16px;margin-top:22px}article strong{display:block;color:#bce4b2;font-size:25px}article p{color:#b2c6c6;margin-bottom:0}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #34474c;padding:16px 12px}th small{display:block;font-weight:400;color:#bce4b2}h2{margin-top:0}li{margin:10px 0}.muted,footer{color:#9fb5b6;font-size:13px}.notice{border-left:3px solid #d4b77a}.scroll{overflow-x:auto}.recent li{padding-bottom:12px}footer{margin-top:25px}@media(max-width:750px){.cards{grid-template-columns:1fr}main{padding:24px 16px}article{margin-top:0}th,td{padding:12px 8px}}</style>
    <main><nav><a href="/">Build a team</a><a href="/status" aria-current="page">Project status</a></nav><h1>What works.<br>What comes next.</h1><p class="intro">Our vision is a beginner-friendly VGC coach: preserve your favourites, build or review six Pokemon, explain the trade-offs, and help you choose four after seeing the opponent. We have the working foundation; the full coach is still in development.</p>
    <div class="cards"><article><strong>Working prototype</strong><p>One to six favourites, legal historical sets, readable reports and Showdown exports.</p></article><article><strong>Real data + memory</strong><p>1,417 species/form records; 358 historical usage records; Zetaris joins and Meterless H-MEM preferences.</p></article><article><strong>Model calls off</strong><p>The main app uses local search. It cannot spend cloud model credits. Nightshift AI integration remains unfinished.</p></article></div>
    <section><h2>Aligned with the vision</h2><ul><li><b>Working:</b> preserve locked favourites, fill team slots, validate sets and team clauses, explain original-type weaknesses and remember preferences.</li><li><b>Improved:</b> source-weighted set choices, weather/terrain and ally-hit checks, level-50 stats, conditional Speed, actionable example leads and four-of-six plans. These remain heuristics, not solved battles.</li><li><b>Missing depth:</b> damage calculations, opponent-aware plans, optimized IVs and stronger interaction checks.</li><li><b>Deliberate scope:</b> historical Scarlet/Violet VGC Regulation H, using November 2024 ladder statistics. Not current 2026 rules.</li></ul></section>
    <section><h2>GenAI marking rubric</h2><p class="muted">Weights from the supplied hackathon overview. These are candid readiness notes, not awarded or predicted scores.</p><div class="scroll"><table><thead><tr><th>Criterion</th><th>Current position</th><th>Highest-value improvement</th></tr></thead><tbody>''' + rows + '''</tbody></table></div></section>
    <section class="notice"><h2>Next priorities</h2><ol><li><b>Finish the AI requirement safely:</b> configure a verified free Nightshift route and integrate its reasoning into the real-data product. Earlier successful Nemotron traces do not substitute for this.</li><li><b>Deepen coaching:</b> the local interaction and Speed checks are now implemented and regression-tested; review the resulting advice with VGC players.</li><li><b>Validate usefulness:</b> compare builds and explanations with a baseline, then have beginners try the interface.</li><li><b>Prepare the submission:</b> public repository, sponsor explanation, slide deck, demo video and HackOS fields.</li></ol></section>
    <section><h2>Verification already recorded</h2><p>73 application tests and 13/13 Meterless H-MEM conformance checks passed on 23 October 2026. A clean sample installation and the live local Zetaris workflow also passed.</p><p class="muted">This is the last recorded verification, not a live test runner. Backend form/report checks passed; visual browser automation was unavailable. Full submission eligibility is not certified here.</p></section>
    <section><h2>Recent actual runs</h2><ul class="recent">''' + ("".join(recent) or "<li>No recorded builds yet. Build a team to see its progress here.</li>") + '''</ul></section><footer>Status is based on saved implementation and run traces. No cloud model call is made by this page.</footer></main></html>'''
