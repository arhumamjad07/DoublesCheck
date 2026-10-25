"""Loopback GUI with local planning and explicit bounded Nightshift AI mode."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
import json
from pathlib import Path
import re
import secrets
import webbrowser
from urllib.parse import urlsplit, parse_qs

from catalogue import ROOT
from team import execute, resume_review
from ai_coach import CoachPaused
from nightshift_client import CoachError
from project_status import dashboard, progress

TOKEN = secrets.token_urlsafe(24)
PORT = 8765

def home():
    data = json.loads((ROOT / "data/catalogue.json").read_text(encoding="utf-8"))
    names = [name for name, mon in data["species"].items() if mon["sets"] and mon["eligible_species"]]
    options = "".join(f'<option value="{escape(n, quote=True)}"></option>' for n in sorted(names))
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DoublesCheck</title><style>
    :root{color-scheme:dark}*{box-sizing:border-box}body{background:#101b20;color:#edf5ed;font:16px/1.6 system-ui;margin:0}main{max-width:900px;margin:50px auto;padding:24px}.brand{color:#bce4b2;letter-spacing:.14em;font-weight:750}h1{font-size:clamp(40px,7vw,70px);line-height:1.05;letter-spacing:-.04em;margin:20px 0}p{color:#b2c6c6;max-width:720px}form{background:#17272c;border:1px solid #34474c;border-radius:22px;padding:28px;margin-top:30px}label{display:block;margin:18px 0 7px;font-weight:650}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}input,select,button{font:inherit;width:100%;padding:13px;border-radius:9px;border:1px solid #536869;background:#101b20;color:#edf5ed}button{background:#bce4b2;color:#13251c;border:0;font-weight:750;margin-top:28px;cursor:pointer}.muted{font-size:13px;color:#9fb5b6}small{color:#bce4b2}#message{margin-top:16px;color:#f0c58e;white-space:pre-wrap}.check{display:flex;gap:12px;font-size:14px;align-items:center}.check input{width:auto}a{color:#bce4b2}footer{margin-top:30px;font-size:12px;color:#9fb5b6}@media(max-width:600px){main{margin:16px auto}.grid{grid-template-columns:1fr}form{padding:20px}}</style>
    <main><nav style="display:flex;gap:24px;margin-bottom:24px"><a href="/">Build a team</a><a href="/status">Project status and next steps</a></nav><div class="brand">DOUBLES CHECK</div><h1>Keep your favourites.<br>Understand your team.</h1><p>A starting team for Pokemon doubles, with legal sets, roles, weaknesses and possible opening pairs you can inspect.</p><small>HISTORICAL FORMAT · Scarlet/Violet VGC Regulation H · November 2024 data</small>
    <form id="builder"><h2>Who are you building around?</h2><p class="muted">Choose one to six Pokemon. Leave slots empty and we will fill them. If you lock all six, we keep all six and review the team. Only species with a validated build in this snapshot appear in suggestions.</p><div class="grid">''' + "".join(f'<input aria-label="Favourite {i}" placeholder="{"Charizard, for example" if i==1 else "Optional favourite"}" name="favourite" list="pokemon" maxlength="60">' for i in range(1,7)) + '''</div><datalist id="pokemon">''' + options + '''</datalist>
    <p class="muted">Your first favourite is remembered for next time. Additional locked Pokemon apply to this run.</p><label for="avoid">Any teammate you want to avoid?</label><input id="avoid" list="pokemon" placeholder="Optional: a remembered preference" maxlength="60"><label class="check"><input type="checkbox" id="clear">Clear my previous avoided teammate</label>
    <label for="mode">Data mode</label><select id="mode"><option value="zetaris">Connected data — use local Zetaris</option><option value="sample">Offline sample — no services or credentials needed</option></select><p class="muted">Both modes use the same sourced historical snapshot. Local planning makes no AI model calls. Offline sample always stays model-free.</p><label for="reasoning">Planning mode</label><select id="reasoning"><option value="local">Local planning - no model calls</option><option value="ai">Nightshift AI - approved NVIDIA Nemotron route, up to 8 requests</option></select><label for="objective">Coaching objective</label><select id="objective"><option value="simple">Beginner-friendly balanced play</option><option value="sun">Explore a sun mode</option><option value="rain">Explore a rain mode</option><option value="trick-room">Explore a slow Trick Room mode</option><option value="reliable">Repair unsupported item/weather plans</option></select><p class="muted">AI mode sends your selected Pokemon and preferences to the NVIDIA model through your local Nightshift runtime. It requires connected Zetaris data. Provider limits still apply; it does not use your ChatGPT/Codex allowance. A failed AI run is withheld, with no silent local substitute.</p><button type="submit">Build and check my team</button><div id="message" role="status"></div><ol id="progress" style="font-size:14px;color:#b2c6c6" aria-live="polite"></ol></form><footer>Independent fan project. No affiliation with Pokemon, Nintendo, Creatures or GAME FREAK.<br>Local planning and legality checks are a starting point, not a promise of competitive success.</footer></main>
    <script>
const form=document.querySelector('form'),button=document.querySelector('button'),message=document.querySelector('#message'),progressList=document.querySelector('#progress');
const dataMode=document.querySelector('#mode'),reasoningMode=document.querySelector('#reasoning');
const objectiveMode=document.querySelector('#objective');
function updateModes(){const offline=dataMode.value==='sample';reasoningMode.querySelector('[value=ai]').disabled=offline;if(offline)reasoningMode.value='local';objectiveMode.disabled=reasoningMode.value!=='ai';if(objectiveMode.disabled)objectiveMode.value='simple';}
dataMode.addEventListener('change',updateModes);reasoningMode.addEventListener('change',updateModes);updateModes();
async function runRequest(path,body,runId){
  button.disabled=true;message.replaceChildren();message.textContent='Loading data and checking your choices...';progressList.replaceChildren();let polling=false;
  async function updateProgress(){if(polling)return;polling=true;try{const response=await fetch('/progress?run='+runId);if(!response.ok)return;const state=await response.json();const items=state.events.map(event=>{const li=document.createElement('li');li.textContent=event.label;return li;});progressList.replaceChildren(...items);}catch(error){}finally{polling=false;}}
  const timer=setInterval(updateProgress,700);
  try{
    const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-DoublesCheck-Token':''' + json.dumps(TOKEN) + '''},body:JSON.stringify(body)});
    const data=await response.json();await updateProgress();
    if(!response.ok){
      message.textContent=data.error;button.disabled=false;
      if(data.resume_available){
        const note=document.createElement('p');note.textContent='Checked work is retained for 30 minutes while this app stays open. Continuing uses the remaining request budget; nothing retries automatically.';message.append(note);
        const resume=document.createElement('button');resume.type='button';resume.textContent='Continue this review ('+data.remaining_model_calls+' requests left)';resume.addEventListener('click',()=>runRequest('/resume',{run_id:data.run_id},data.run_id));message.append(resume);
      }
      return;
    }
    location.href=data.report;
  }catch(error){message.textContent=error.message;button.disabled=false;}finally{clearInterval(timer);}
}
form.addEventListener('submit',event=>{
  event.preventDefault();const runId=crypto.randomUUID().replaceAll('-','');
  runRequest('/build',{run_id:runId,favourites:[...document.querySelectorAll('[name=favourite]')].map(el=>el.value.trim()).filter(Boolean),avoided:document.querySelector('#avoid').value.trim()||null,clear:document.querySelector('#clear').checked,sample:dataMode.value==='sample',ai:reasoningMode.value==='ai',objective:document.querySelector('#objective').value},runId);
});
</script></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def respond(self, status, content, content_type="text/html; charset=utf-8"):
        payload = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(payload)
    def allowed_host(self):
        return self.headers.get("Host") in (f"localhost:{PORT}", f"127.0.0.1:{PORT}")
    def do_GET(self):
        if not self.allowed_host(): return self.respond(403, "Local access only.")
        if self.path == "/": return self.respond(200, home())
        if self.path == "/status": return self.respond(200, dashboard(ROOT))
        if urlsplit(self.path).path == "/progress":
            try:
                run_id = parse_qs(urlsplit(self.path).query).get("run", [None])[0]
                return self.respond(200, json.dumps(progress(run_id, ROOT)), "application/json")
            except ValueError:
                return self.respond(400, json.dumps({"error": "Invalid run identifier."}), "application/json")
        match = re.fullmatch(r"/runs/([a-f0-9]{32})/(report\.html|report\.json|team\.txt|trace\.jsonl)", self.path)
        if match:
            file = ROOT / "runs" / match[1] / match[2]
            if file.is_file():
                content_type = "text/html; charset=utf-8" if file.suffix == ".html" else "text/plain; charset=utf-8"
                return self.respond(200, file.read_text(encoding="utf-8"), content_type)
        self.respond(404, "Not found.")
    def do_POST(self):
        if not self.allowed_host() or self.headers.get("X-DoublesCheck-Token") != TOKEN:
            return self.respond(403, json.dumps({"error": "Reload the local page before submitting."}), "application/json")
        if self.path not in {"/build", "/resume"}: return self.respond(404, "Not found.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096: raise ValueError("Request is too large or empty.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict): raise ValueError("Expected a team request.")
            if self.path == "/resume":
                if set(body) != {"run_id"}: raise ValueError("Continuation accepts only the original review identifier.")
                result, folder = resume_review(body["run_id"])
                return self.respond(200, json.dumps({"report": f"/runs/{result['trace_id']}/report.html"}), "application/json")
            favourites = body.get("favourites", [])
            if not isinstance(favourites, list) or len(favourites) > 6 or not all(isinstance(n, str) and len(n)<=60 for n in favourites):
                raise ValueError("Choose up to six Pokemon.")
            avoided = body.get("avoided")
            if avoided is not None and (not isinstance(avoided, str) or len(avoided)>60): raise ValueError("Invalid avoided teammate.")
            if type(body.get("sample")) is not bool or type(body.get("clear")) is not bool: raise ValueError("Invalid data mode.")
            if avoided and body["clear"]: raise ValueError("Choose an avoided teammate or clear the previous one, not both.")
            ai = body.get("ai", False)
            objective = body.get("objective", "simple")
            if type(ai) is not bool or not isinstance(objective, str): raise ValueError("Invalid AI planning mode.")
            result, folder = execute(favourites, avoided, body["sample"], "default", clear_avoidance=body["clear"], run_id=body.get("run_id"), ai=ai, objective=objective, allow_resume=True)
            self.respond(200, json.dumps({"report": f"/runs/{result['trace_id']}/report.html"}), "application/json")
        except CoachPaused as error:
            self.respond(503, json.dumps({"error": str(error), "resume_available": True, "run_id": error.run_id,
                                         "remaining_model_calls": 8-error.session.client.calls}), "application/json")
        except CoachError as error:
            self.respond(503 if error.retryable else 400, json.dumps({"error": str(error), "error_kind": error.code, "resume_available": False}), "application/json")
        except (ValueError, RuntimeError) as error:
            self.respond(400, json.dumps({"error": str(error)}), "application/json")
        except Exception:
            self.respond(500, json.dumps({"error": "The local build could not complete. Check dependencies and restart the app."}), "application/json")

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"DoublesCheck is ready: http://127.0.0.1:{PORT} - local planning and explicit Nightshift AI.", flush=True)
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
