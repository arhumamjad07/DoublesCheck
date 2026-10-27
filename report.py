"""Portable HTML report. All data is escaped; no remote assets or tracking."""
from html import escape as e
import json

def render(result):
    from evidence_lens import render_lens
    lens_html = render_lens(result.get("evidence_lens")) if result.get("mode") == "sample" or result.get("evidence_lens") else ""
    members = []
    for member in result["members"]:
        s = member["set"]
        moves = "".join(f'<li><strong>{e(m["name"])}</strong><span>{e(m["type"])} · {e(m["category"])}</span><p>{e(m["description"])}</p></li>' for m in member["moves"])
        coaching = member.get("move_guidance", [])
        if coaching:
            moves = "".join(f'<li><strong>{e(m["move"])}</strong><p>{e(m["guidance"])}</p></li>' for m in coaching)
        stats = member.get("actual_stats", {})
        stat_text = " / ".join(f'{k.upper()} {v}' for k, v in stats.items())
        speed = member.get("speed", {})
        speed_conditions = "".join(f'<li>{e(r["condition"])}: <b>{r["speed"]}</b></li>' for r in speed.get("scenarios", []))
        set_cautions = "".join(f'<li>{e(c)}</li>' for c in member.get("set_cautions", []))
        evidence = member.get("historical_evidence")
        evidence_text = "No per-choice rates were retained in this registered snapshot."
        if evidence:
            evidence_text = (f"Separate historical shares: item {evidence['item_share']:.1%}; ability {evidence['ability_share']:.1%}; "
                             f"spread {evidence['spread_share']:.1%} of reported spreads. These choices were not necessarily used together.")
        extra = f'''<p><b>Stats at level {s.get('level', 50)}:</b> {e(stat_text)}</p><p>{e(member.get('spread_explanation', ''))}</p>
          <details><summary>Speed, conditions and set trade-offs</summary><p>Ordinary effective Speed: <b>{speed.get('ordinary_speed', '?')}</b>.</p><ul>{speed_conditions}</ul><p class="muted">{e(speed.get('scope', ''))}</p><ul>{set_cautions}</ul><p class="muted">{e(evidence_text)}</p></details>'''
        evs = " / ".join(f'{v} {k.upper()}' for k, v in s["evs"].items() if v)
        weaknesses = ", ".join(f"{t} ×{v:g}" for t, v in member["type_weaknesses"].items())
        members.append(f'''<article><header><div><small>{"YOUR LOCKED PICK" if member["locked"] else "SUGGESTED PARTNER"}</small><h2>{e(member["name"])}</h2></div><b class="type">{e(" / ".join(member["types"]))}</b></header>
          <p class="roles">{e(" · ".join(member["roles"]))}</p><p>{e(member["selection_reason"])}</p><dl><dt>Ability</dt><dd>{e(s["ability"])}</dd><dt>Item</dt><dd>{e(s["item"])}</dd><dt>Nature / Tera</dt><dd>{e(s["nature"])} / {e(s["teraType"])}</dd><dt>EVs</dt><dd>{e(evs)}</dd><dt>IVs</dt><dd>31 in all six stats (default)</dd></dl>
          <details><summary>Moves and how this member works</summary><ul class="moves">{moves}</ul><p><b>{e(s["ability"])}</b>: {e(member["ability_description"])}</p><p><b>{e(s["item"])}</b>: {e(member["item_description"])}</p></details>
          {extra}<p class="muted">Original-type weaknesses: {e(weaknesses or "none")}.</p><p class="muted">Historical weighted ladder usage: {member["usage_percent"]:g}%.</p></article>''')
    risks = "".join(f'<tr><td>{e(r["type"])}</td><td>{e(", ".join(r["weak"]))}</td><td>{e(", ".join(r["resist_or_immune"]) or "None in original types")}</td></tr>' for r in result["weaknesses"])
    def bullet_rows(values):
        return "".join(f"<li>{e(value)}</li>" for value in values)
    leads = "".join(f'''<article><h3>{e(" + ".join(r["pokemon"]))}</h3><p>{e(" ".join(r["reasons"]))}</p><b>A possible opening</b><ul>{bullet_rows(r.get("opening_actions", []))}</ul><details><summary>Conditions and cautions ({len(r.get("cautions", []))})</summary><ul>{bullet_rows(r.get("cautions", []))}</ul></details></article>''' for r in result["possible_leads"])
    plans = "".join(f'''<article><h3>{e(" + ".join(r["lead"]))}</h3><p><b>Back:</b> {e(" + ".join(r["back"]))}</p><ul>{bullet_rows(r.get("reasons", []))}</ul><p class="muted">{e(r.get("note", ""))}</p><details><summary>Check before choosing this four ({len(r.get("cautions", []))})</summary><ul>{bullet_rows(r.get("cautions", []))}</ul></details></article>''' for r in result["four_of_six_examples"])
    interactions = "".join(f'<li><b>{e(" + ".join(row["pokemon"]))}</b> <span class="muted">{e(row["severity"])}</span><p>{e(row["explanation"])}</p></li>' for row in result.get("interactions", [])) or "<li>No supported conflict was found. This is not an exhaustive safety check.</li>"
    overview = result.get("speed_overview", {})
    speed_rows = "".join(f'<tr><td>{e(row["pokemon"])}</td><td>{row["speed"]}</td></tr>' for row in overview.get("ordinary_order", []))
    evaluation = result.get("team_evaluation", {})
    components = "".join(f'<tr><td>{e(name.replace("_", " "))}</td><td>{value:+.3f}</td></tr>' for name, value in evaluation.get("components", {}).items())
    warnings = "".join(f'<li>{e(w)}</li>' for w in result["warnings"])
    sources = "".join(f'<li><a href="{e(s["url"], quote=True)}">{e(s["title"])}</a></li>' for s in result["sources"])
    coach = result.get("ai_coach")
    coach_html = ""
    if coach:
        evidence = "".join(f'<li><b>{e(row["id"])}</b> {e(row["text"])}</li>' for row in coach["selected_evidence"])
        acknowledgements = "".join(f'<li><b>{e(row["id"])}</b> {e(row["text"])}</li>' for row in coach["acknowledged_cautions"])
        changes = "".join(f'<li>Version {row["version"]}: {e(row["operation"])} changed {e(", ".join(row["changed_members"]))}. Removed partners: {e(", ".join(row["removed_partners"]) or "none")}.</li>' for row in coach["changes"])
        assessment = coach.get("objective_assessment")
        audit_html = ""
        if assessment:
            audit_html += f'<div class="notice"><b>{"Requested objective supported" if assessment["met"] else "Alternative offered: requested objective not met"}</b><p>{e(assessment["explanation"])}</p></div>'
        if coach.get("roles_used"):
            audit_html += f'<p><b>Roles actually used:</b> {e(" → ".join(coach["roles_used"]))}. Candidate origin: {e(coach.get("proposal_origin", "not recorded"))}.</p>'
        contracts = coach.get("revision_contracts", [])
        if contracts:
            rows = "".join(f'<tr><td>{e(r["id"])} · {e(r.get("code") or r["kind"])}</td><td>{e(r["problem"])}</td><td>{e(r["status"])}<br>v{r["requested_version"]} → v{r["current_version"]}</td></tr>' for r in contracts)
            audit_html += f'<h3>What the critic asked to change</h3><p class="muted">A different team alone is insufficient: a change-required condition must actually disappear, or the targeted member must change. Disclosure is labelled separately.</p><div class="scroll"><table><thead><tr><th>Checked issue</th><th>Original problem</th><th>Verified result</th></tr></thead><tbody>{rows}</tbody></table></div>'
        details = []
        for change in coach["changes"]:
            for member in change.get("member_changes", []):
                before, after = member.get("before") or {}, member.get("after") or {}
                fields = [f'{key}: {before.get(key, "absent")} → {after.get(key, "absent")}' for key in ("item", "ability", "nature", "moves") if before.get(key) != after.get(key)]
                details.append(f'<li><b>{e(member["species"])}</b>: {e("; ".join(fields) or "spread or other checked set fields changed")}</li>')
        if details: audit_html += '<h3>Actual before-and-after sets</h3><ul>' + "".join(details) + '</ul>'
        coach_html = f'''<section><h2>Nightshift AI review</h2><p><b>Execution:</b> {e(coach.get("execution", "live"))}. Simulated runs are tests, not live-model evidence.</p><p><b>Objective:</b> {e(coach["objective"])}. <b>Strategy:</b> {e(coach["strategy"])}.</p><p>Actual model: <code>{e(", ".join(coach["actual_models"]))}</code></p><div class="status"><span class="pill">{coach["model_calls"]} model requests</span><span class="pill">{coach["tool_calls"]} executed tools</span><span class="pill">{coach["revision_rounds"]} critic revision rounds</span><span class="pill">Final team version {coach["team_version"]}</span></div><p>{"The AI workflow changed the local baseline." if coach["changed_from_local_baseline"] else "The AI reviewed and retained the local baseline; no team change is claimed."}</p><h3>Evidence selected by the AI roles</h3><ul>{evidence}</ul><details><summary>Actual team changes</summary><ul>{changes or "<li>No team mutation occurred.</li>"}</ul></details><details><summary>Remaining cautions explicitly acknowledged by the critic</summary><ul>{acknowledgements or "<li>No supported caution remains.</li>"}</ul></details><p class="muted">{e(coach["scope"])}</p><p><a href="trace.jsonl">Inspect model identities, tool calls and critique/revision events</a></p></section>'''
        coach_html = coach_html.replace('<h3>Evidence selected by the AI roles</h3>', audit_html + '<h3>Evidence selected by the AI roles</h3>')
        coach_html = coach_html.replace("local baseline", "input candidate")
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DoublesCheck · Team report</title>
    <style>:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#101b20;color:#edf5ed;font:16px/1.55 system-ui,sans-serif}}main{{max-width:1160px;margin:auto;padding:42px 26px 80px}}a{{color:#bce4b2}}.brand{{letter-spacing:.12em;color:#bce4b2;font-weight:750}}h1{{font-size:clamp(35px,6vw,64px);line-height:1.1;letter-spacing:-.04em;margin:18px 0}}h2,h3,p{{margin-top:0}}.intro{{max-width:780px;color:#b9c8c7}}.status{{display:flex;gap:12px;flex-wrap:wrap;margin:25px 0}}.pill,.type{{background:#263f3b;border:1px solid #3f5e54;padding:7px 13px;border-radius:30px;font-size:13px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}article{{border:1px solid #34474c;background:#17272c;border-radius:16px;padding:24px;min-width:0}}article header{{display:flex;justify-content:space-between;gap:12px;align-items:center}}small{{font-size:10px;letter-spacing:.12em;color:#bce4b2}}article h2{{margin:4px 0 0;font-size:27px}}.roles{{color:#bce4b2;margin:16px 0}}dl{{display:grid;grid-template-columns:110px 1fr;font-size:14px;gap:7px}}dt{{color:#9fb5b6}}dd{{margin:0}}summary{{cursor:pointer;color:#d0eac9;margin:20px 0 8px}}.moves{{padding-left:20px}}.moves span{{display:block;font-size:12px;color:#a8c3c2}}.moves p{{font-size:13px;margin:5px 0 12px}}.muted{{color:#9fb5b6;font-size:13px}}section{{margin-top:42px}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #34474c}}.scroll{{overflow-x:auto}}pre{{white-space:pre-wrap;background:#0c1519;border:1px solid #34474c;border-radius:14px;padding:22px;font-size:13px}}.notice{{border-left:3px solid #d3b77b;padding:4px 20px;color:#d8d1bc}}.plans li{{margin:12px 0}}footer{{margin-top:45px;color:#8ca5a7;font-size:12px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}article{{padding:18px}}main{{padding:25px 16px}}article header{{align-items:flex-start;flex-direction:column}}}}</style>
    <main><div class="brand">DOUBLES CHECK</div><h1>Your favourites.<br>A team you can inspect.</h1><p class="intro">Six Pokemon, legal sets and a clear starting plan. This report uses historical VGC Regulation H and November 2024 ladder data. It does not claim to find the best team.</p>
    <div class="status"><span class="pill">Historical format checked</span><span class="pill">{e(result["data_source"])}</span><span class="pill">H-MEM preferences applied</span><span class="pill">{int(result.get("model_calls", 0))} model calls</span></div>
    {lens_html}{coach_html}<div class="grid">{"".join(members)}</div><section><h2>Weaknesses to plan around</h2><p class="muted">Original types only, before Tera, abilities or field effects. A resistant teammate does not automatically shield its ally.</p><div class="scroll"><table><thead><tr><th>Attack type</th><th>Weak members</th><th>Resistant or immune members</th></tr></thead><tbody>{risks}</tbody></table></div></section>
    <section><h2>Interactions and trade-offs</h2><p class="muted">These are play conditions, not legality failures. Resolve each one before relying on a combination.</p><ul class="interaction-list">{interactions}</ul></section><section><h2>Who moves first?</h2><p>{e(overview.get("explanation", ""))}</p><div class="scroll"><table><thead><tr><th>Your Pokemon</th><th>Ordinary effective Speed</th></tr></thead><tbody>{speed_rows}</tbody></table></div><p>{e(overview.get("trick_room_plan", ""))}</p><p class="muted">These are your selected sets at neutral stat stages. Open each member's speed section for conditional figures. No opposing speed or guaranteed outspeed is assumed.</p></section><section><h2>Possible opening pairs</h2><p class="muted">Examples to explore after reviewing the opponent's team, not simulated winning lines.</p><div class="grid">{leads}</div></section><section><h2>Bring four of your six</h2><div class="grid">{plans}</div></section>
    <section><details><summary>How the local builder scored this team</summary><p>{e(evaluation.get("scope", ""))}</p><div class="scroll"><table><tbody>{components}</tbody></table></div><p class="muted">Scores help rank candidates within this search. They are not percentages and cannot prove one team wins more battles.</p></details></section><section><h2>Copy into Pokemon Showdown</h2><p class="muted">Select and copy this text, or <a href="team.txt" download="doublescheck-team.txt">download the team file</a>.</p><pre>{e(result["showdown_export"])}</pre></section><section class="notice"><h2>Know the limits</h2><ul>{warnings}</ul><p>{e(result["set_method"])}</p></section><section><h2>Data and evidence</h2><ul>{sources}</ul><p class="muted">The source dataset reports {int(result["statistics"]["number of battles"]):,} ladder battles. Usage frequency is not a win rate. No official tournament results are included.</p><p><a href="report.json">Structured report</a> · <a href="trace.jsonl">Decision trace</a> · <a href="http://127.0.0.1:8765/">Build another team</a></p></section><footer>Independent fan project. Not affiliated with Pokemon, Nintendo, Creatures or GAME FREAK. No official artwork used.<br>Trace {e(result["trace_id"])}</footer></main></html>'''
