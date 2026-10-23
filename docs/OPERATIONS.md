# Setup and operations

## Choose a mode

| Mode | Required | Network/model usage |
| --- | --- | --- |
| Offline sample | Python, Node and installed npm dependency | No service requests or model calls during a build |
| Connected | The above, Python dependencies, local Zetaris/Docker and its token | Local Zetaris SQL requests; no model calls |
| Legacy experiments | Separate settings and an explicit credit gate | Not part of Demo 1 setup; may use provider allowance if deliberately enabled |

Installing dependencies and refreshing public data require internet access.
That is separate from the installed sample app's offline execution.

## Installation

Use the root README's setup commands. Python 3.10+ and Node 22+ are the declared
requirements; Demo 1 was tested on Windows with Node 24. The committed H-MEM
runtime is already compiled. Rebuilding its TypeScript requires a Node release
that supplies `node:module.stripTypeScriptTypes`; Node 24 was used for that task.

A virtual environment is recommended. It keeps `requests` and `python-dotenv`
separate from other projects. All commands in the other guides assume `python`
selects the intended environment; use its explicit executable if necessary.

`npm ci --ignore-scripts --omit=optional --no-audit --no-fund` installs the locked
required dependency graph without lifecycle scripts or optional server packages.
Do not commit `node_modules` or the virtual environment.

## Local GUI and CLI

Run `python app.py`, then visit <http://127.0.0.1:8765>. The server is bound to
loopback. The form supports up to six favourites, one avoidance and explicit
avoidance clearing. GUI requests use the `default` memory profile.

Open `/status` for the vision, recorded test results, roadmap and recent runs.
That page is not a live test runner. Form progress comes from the current run's
trace; stages are not fabricated percentages.

CLI examples:

```powershell
python team.py --sample --favourites Charizard --profile learning
python team.py --sample --favourites Charizard Venusaur Blastoise --profile learning
python team.py --sample --favourites Charizard --avoid-partner Incineroar --profile learning
python team.py --sample --profile learning
python team.py --sample --allow-all-partners --profile learning
```

Names with spaces need quotes, for example `"Indeedee-F"` and `"Mr. Mime"`.
The alias `--lock` also accepts favourite names. Only the first favourite persists
between runs. Profiles must contain 1–64 letters, digits, underscores or hyphens.
Additional locks apply to the current run. `--output PATH` selects the run-output
parent; profile memory still resides in the project's private memory directory.

## Environment settings

Copy `.env.example` to `.env` locally only for connected services.

| Variable | Purpose in Demo 1 |
| --- | --- |
| `ZETARIS_REST_URL` | Local REST base, normally `http://localhost:8888/api/v1.0` |
| `ZETARIS_ORG_ID` | Local organisation identifier, normally `1` |
| `ZETARIS_API_KEY` | Your local Zetaris access token; private |
| `DOUBLES_CHECK_NODE` | Optional path to a working Node executable |
| `METERLESS_BASE_URL` | Retained legacy integration setting; unused by the main app |
| `METERLESS_RUNTIME_TOKEN` | Legacy Nightshift credential; private and unused by the main app |
| `METERLESS_MODEL` | Legacy route identifier; unused by the main app |

No real credential is distributed. Do not add a provider key to a source file,
example report, issue, screenshot or commit. Never publish `.env` contents.

## Zetaris and Docker

Use the supplied Zetaris platform installation and its documented startup steps.
The repository does not include its Docker images or distribution credentials.
For an existing stack under `C:/zetaris-platform`, these commands are run from
that stack's directory:

```powershell
docker compose up -d
docker compose ps
```

The query engine (`driver`) and API must be healthy. From DoublesCheck, run:

```powershell
python register-data.py --compose-dir C:/zetaris-platform
python team.py --favourites Charizard --profile connected-demo
```

Registration copies the prepared public CSV files to
`/home/zetaris/customer-data/shared/doublescheck-v1` in the driver and
creates/retains `DOUBLES_CHECK.pokedex`, `vgc_usage` and `reference`. Re-running
refreshes only those dedicated files. It does not drop existing registrations or
alter unrelated platform data. Back up any deliberate local changes to those
specific snapshot files before re-registering.

Only `localhost`, `127.0.0.1` and `::1` are accepted for the Zetaris host. Redirects
are disabled. The app sends bearer authentication and organisation/request headers
to `/sql-editor/sqls/run`. It does not silently change providers or data modes.

## Storage and privacy

- `runs/<id>/report.html`, `report.json`, `team.txt`, `trace.jsonl`: generated local
  results. Traces may contain preferences, profile names and memory identifiers.
- `.doublescheck-memory/<profile>/`: local preference records and audit history.
- `.env`: local service secrets.
- `logs/`, backups and raw refresh intermediates: local development artifacts.

These locations are excluded from Git. Only intentionally generated public sample
artifacts live under `examples/demo-1`. Local stores are plain files, not encrypted
vaults. Avoid entering personal or sensitive information as preferences.

## Costs

The current GUI/CLI uses local computation. Docker/Zetaris queries, H-MEM retrieval
and Showdown validation do not consume ChatGPT or NVIDIA model tokens. They use
your own hardware and electricity.

Codex/ChatGPT usage while developing the project belongs to the coding assistant's
own plan. A future app request routed through Nightshift would use the configured
provider's allowance/billing, separately from that plan. No provider's free quota
or billing state has been verified for this milestone. The legacy model client is
blocked before transport unless a deliberate opt-in is present. Demo 1 setup does
not require or enable that opt-in.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Python opens the Windows Store or is missing | Install a working Python interpreter and select it in the editor; use the explicit venv executable |
| Node/validator cannot run | Check `node --version`, install the npm dependencies, or set `DOUBLES_CHECK_NODE` |
| Zetaris missing/offline | Start its local stack and driver/API, check `.env`, or explicitly select Offline sample |
| Older schema snapshot | Re-run `register-data.py` with this version's prepared CSVs |
| Unknown/banned/unsupported Pokémon | Check the spelling/form and this historical snapshot's support; no replacement is silently made |
| Locked Pokémon is also avoided | Clear that avoidance or change the locks |
| H-MEM reports a busy profile | Wait for that profile's current operation; do not remove another running process's lock |
| Port 8765 is already in use | Use the existing DoublesCheck instance or stop that instance before restarting |
| Local form token rejected | Reload the form after a server restart |
| Sample still appears to call a model | Use `app.py` or `team.py`, not the separately retained legacy `demo.py` |

Stop the application with Ctrl+C in its terminal. Stopping the separate Zetaris
stack with `docker compose stop` preserves its volumes. Do not use volume deletion
commands as a routine shutdown step. Nightshift need not run for Demo 1.
