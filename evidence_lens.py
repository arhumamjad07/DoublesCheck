"""Allowlisted public evidence. Transport objects, SQL, URLs and headers stay private."""
from datetime import datetime, timezone
from html import escape
import json
import math
import time
import uuid

FORMAT, MONTH, CUTOFF, BATTLES = "gen9vgc2024regh", "2024-11", 1500, 965304
TABLES = {"pokedex", "vgc_usage", "reference", "pokemon_facts", "usage_snapshots",
          "teammate_relationships", "sourced_sets", "source_metadata"}
PURPOSES = {"catalogue_join", "historical_reference", "partner_ranking", "normalised_integrity"}


def receipt(purpose, tables, returned_rows, started_at, duration_ms, *, candidates=None):
    if purpose not in PURPOSES or not tables or not set(tables) <= TABLES:
        raise ValueError("Unknown public query purpose or table.")
    if type(returned_rows) is not int or not 0 <= returned_rows <= 1000000:
        raise ValueError("Invalid public row count.")
    if candidates is not None and (type(candidates) is not int or not 0 <= candidates <= 1000000):
        raise ValueError("Invalid public candidate count.")
    try:
        stamp = datetime.fromisoformat(started_at)
        if stamp.tzinfo is None: raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Invalid public query timestamp.") from None
    if type(duration_ms) not in (int, float) or not math.isfinite(duration_ms) or not 0 <= duration_ms <= 3600000:
        raise ValueError("Invalid query duration.")
    return {"query_id": "dcq-" + uuid.uuid4().hex, "purpose": purpose,
            "tables": [("DOUBLES_CHECK." if t in {"pokedex","vgc_usage","reference"} else "DOUBLES_CHECK_LENS.") + t for t in sorted(set(tables))],
            "format_id": FORMAT, "snapshot": MONTH, "cutoff": CUTOFF,
            "returned_rows": returned_rows, "candidates_considered": candidates,
            "started_at": stamp.astimezone(timezone.utc).isoformat(), "duration_ms": round(duration_ms, 2)}


def measured_query(api, sql, purpose, tables, receipts, *, limit=2000, candidates=None):
    stamp, start = datetime.now(timezone.utc).isoformat(), time.monotonic()
    rows = api.query(sql, limit=limit)
    receipts.append(receipt(purpose, tables, len(rows), stamp, (time.monotonic()-start)*1000, candidates=candidates))
    return rows


def render_lens(lens):
    if not lens:
        return ('<section class="evidence-lens" aria-label="Zetaris Evidence Lens"><h2>Zetaris Evidence Lens</h2>'
                '<p><b>Offline sample — no live Zetaris query.</b></p>'
                '<p>Historical Regulation H · November 2024 · 1500 cutoff. No connection or live receipt is claimed.</p></section>')
    def text(value): return escape(str(value), quote=True)
    receipts = lens["receipts"]
    tables = sorted({t for r in receipts for t in r["tables"]})
    total = sum(r["duration_ms"] for r in receipts)
    ranks, selected = lens.get("partners", []), set(lens.get("selected_partners", []))
    visible = [r for i,r in enumerate(ranks) if i < 6 or r["species"] in selected]
    rows = "".join('<tr><td>' + text(r["species"]) + (' · selected' if r["species"] in selected else '') +
                   '</td><td>' + format(r.get("association", 0), ',.2f') + '</td><td>' +
                   text(round(r.get("usage", 0)*100, 3)) + '%</td><td>' + text(r.get("set_options", 0)) + '</td></tr>' for r in visible)
    decision = ('<p><b>Decision in Zetaris:</b> favourite-specific partner shortlist, ranked by historical '
                'teammate association, then usage. Python still checks team fit, source sets and legality.</p>'
                if lens.get("sql_ranking") else
                '<p>These queries load the joined catalogue. Partner ranking in this slice still runs in Python.</p>')
    ranking = ('<div class="scroll"><table><thead><tr><th>SQL partner evidence (top six + selected)</th><th>Association weight</th>'
               '<th>Weighted usage</th><th>Source set choices</th></tr></thead><tbody>' + rows + '</tbody></table></div>' if rows else '')
    return f'''<section class="evidence-lens" aria-label="Zetaris Evidence Lens" style="border:1px solid #6f9981;border-radius:16px;padding:24px;background:#172c2b;margin:24px 0">
      <div class="brand">ZETARIS EVIDENCE LENS</div><h2>Connected evidence you can inspect</h2>
      <p><b>Live Zetaris queries completed for this run.</b> This is a timestamped receipt, not a continuous health monitor.</p>
      <p><b>Query for:</b> {text(', '.join(lens.get('favourites', [])) or 'catalogue validation')}</p>
      <p>Historical Scarlet/Violet Regulation H · November 2024 · 1500 cutoff · <b>{BATTLES:,} aggregate ladder battles</b></p>
      <p><b>Sources / tables:</b> {text(', '.join(tables))}</p>
      <p><b>Catalogue:</b> {text(lens['catalogue_rows'])} species/forms; {text(lens['usage_rows'])} usage rows; {text(lens['set_options'])} prepared set choices.</p>
      <p><b>Partner query:</b> {text(lens.get('candidate_count', 'not run'))} candidates considered; {text(len(ranks) if lens.get('sql_ranking') else 'not run')} rows returned.</p>
      <p><b>Query time:</b> {total:,.0f} ms total · {text(receipts[0]['started_at'])}</p>
      {decision}{ranking}<p class="muted">Association is historical co-occurrence, not compatibility, a win rate or current-2026 advice. Generated sets combine separate marginal choices, not observed complete teams.</p>
      <details><summary>Sanitised query receipts ({len(receipts)})</summary><pre>{text(json.dumps(receipts, indent=2))}</pre></details></section>'''
