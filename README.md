# DoublesCheck

Build and understand a Pokémon VGC doubles team around your favourites.

DoublesCheck is for beginners who know which Pokémon they like but need help
choosing partners, legal sets and a starting play plan. Lock **one to six Pokémon**;
the app fills the remaining slots or reviews the six you supplied. It preserves
your locked species and explains the choices and trade-offs.

**Demo 4** adds the visible Zetaris Evidence Lens and a live SQL-ranked partner
pool. The user can inspect which historical sources support the shortlist,
change their favourite and see different query evidence and recommendations.
See the [Demo 4 guide](docs/DEMO_4.md) and [passing submission gate](docs/EVIDENCE_VERIFICATION.md).

Demo 3 established real Critic-required AI repair, checked weather-goal
adaptation, explicit recovery after interruptions and broader acceptance cases.
The model investigates and chooses changes; independent code enforces source
sets, preferences, evidence, repair completion and historical legality.

Demo 2 introduced bounded Nightshift/NVIDIA AI mode. Demo 1 established the local
data/memory/validation foundation. The `demo-1`, `demo-2` and `demo-3` tags are preserved;
this milestone is `demo-4`. Local planning remains the default and Offline sample
always makes zero model calls.

Demo 4's **Zetaris Evidence Lens** provides live query receipts and
queryable historical tables, with a favourite-specific SQL shortlist constraining
automatic partner selection. The frozen `demo-3` tag remains available.
Read the [Evidence Lens guide](docs/ZETARIS_EVIDENCE_LENS.md) for exact registration,
recording steps, source grains, boundaries and the separate Grok review task.

See the [Demo 3 guide](docs/DEMO_3.md), [reasoning architecture](docs/REASONING_ACCEPTANCE.md),
[real live repair](examples/reasoning-repair/README.md),
[verification](VERIFICATION.md) and [release security audit](docs/SECURITY_AUDIT.md).

## Try it without accounts or API keys

Requirements: Python 3.10+, Node.js 22+ and npm. Windows was used for verification.
The bundled sample is real historical data; it is not a random mock catalogue.

```powershell
git clone https://github.com/arhumamjad07/DoublesCheck.git
cd DoublesCheck
npm.cmd ci --ignore-scripts --omit=optional --no-audit --no-fund
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:8765>, select **Offline sample**, enter `Charizard` and
choose **Build and check my team**. The form initially selects connected Zetaris
mode, so switch it for this account-free demonstration.

If you already have the Python dependencies installed, `python app.py` works too.
`Start-DoublesCheck.bat` uses the `python` on your PATH. On macOS/Linux, use `npm` instead of `npm.cmd`, and use
`python3 -m venv .venv` and `.venv/bin/python` in place of the Windows venv path;
those platforms have not been independently verified for this milestone.

The sample command-line build needs only Python's standard library and the npm
dependency; it does not need `.env`, Docker, Zetaris or Nightshift:

```powershell
python team.py --sample --favourites Charizard --profile demo-one
python team.py --sample --favourites Charizard Venusaur Blastoise --profile demo-three
```

The command prints the generated report's path. A reproducible, deliberately
public example is included in [examples/demo-1](examples/demo-1/README.md).
Download the repository and open its `report.html` locally; GitHub displays HTML
source rather than running this application.

## What Demo 1 does

- Preserves one to six locked species; fills missing team slots with a bounded
  search. Invalid or unsupported locks produce an error.
- Selects among **11,376 individually validated build options** for **357 supported
  species/forms**, from a catalogue containing **1,417 species/form records**.
- Uses historical item, ability, move and spread rates together with support
  roles, original-type balance, co-occurrence and explicit interaction checks.
- Checks full-team legality, including moves, abilities, EV limits, Species Clause
  and Item Clause, with the local Showdown validator.
- Explains roles, EVs, natures, actual level-50 stats, ordinary/conditional Speed,
  possible opening actions, example groups of four and their cautions.
- Flags competing weather/terrain, blocked priority moves, unsupported seeds,
  conditional Unburden, ally-hitting attacks and other supported interactions.
- Remembers the first favourite and one avoided partner with real Meterless H-MEM.
- Produces HTML, JSON, a Showdown team export and a decision trace. The GUI shows
  progress from real trace events and a project dashboard at `/status`.
- Supports a real local Zetaris join and an explicitly selected offline sample.

## Format and evidence

This milestone supports **historical Scarlet/Violet VGC Regulation H**, with
**November 2024** Smogon ladder statistics at the 1500 cutoff. It is not a check
against the current 2026 competitive rules.

The source archive reports 965,304 ladder battles. Its separate marginal choices
are combined into candidate sets; a generated combination is **not necessarily an
observed complete set**. Usage is not a win rate or official tournament result.
See [data and rules](docs/DATA_AND_RULES.md), [source hashes](data/sources.json)
and [third-party notices](THIRD-PARTY-NOTICES.md).

IVs currently default to 31. EV explanations do not claim verified survival or
knockout benchmarks. Team scores are heuristics, not probabilities. Damage
simulation, opponent-specific battle solving and optimized IVs remain unfinished.

## Explicit Nightshift AI mode

Once local Zetaris and Nightshift are ready, configure your runtime token locally
and explicitly choose Nightshift AI in the GUI, or run:

```powershell
python team.py --ai --favourites Charizard --objective simple --profile ai-coach
```

The requested model is pinned to `nvidia/nemotron-3.5-lightning-30b-a3b`; all model
requests go through the local Nightshift endpoint. The NVIDIA key stays in
Nightshift, not this repository. No OpenAI API key is needed. AI mode is bounded
to eight requests and two critic revision rounds, with no automatic transport
retry or provider fallback. It requires connected data and cannot be combined
with `--sample`. Read the [AI reasoning guide](docs/AI_REASONING.md) before running.

A [real live balanced review](examples/demo-2/README.md) passed in three model
requests and retained the baseline. Current development also demonstrates a
[Critic-required live repair](examples/reasoning-repair/README.md) and
[explicit recovery](examples/reasoning-recovery/README.md), plus
[live rain adaptation](examples/reasoning-rain/README.md). Upstream errors still
occur; failed or unfinished AI runs withhold the result. See the
verification log for passing and failed attempts, rather than assuming a health
check or the model-free test suite establishes live reliability.

## Evaluate the reasoning workflow

```powershell
# Local checks and declared cases, no services or model calls
python evaluate_reasoning.py

# Explicit real-service repair evaluation; at most eight model requests
python evaluate_reasoning.py --live --cases seed-repair --max-model-requests 8
```

The suite distinguishes live approvals, expected input refusals, offline checks
and unmet objectives. It keeps failures visible. `--resume-once` explicitly opts
into one continuation per case without resetting its request budget. In the GUI,
Continue is manual, preserves completed work, and is available for up to 30
minutes while the app remains open. No provider switch or background retry occurs.

For item/weather activation repair, choose the `reliable` AI objective. A report
must identify an unmet objective as an alternative rather than pretend success.

## Connected Zetaris mode

Use the event-supplied Zetaris Docker Compose installation; its platform and
container images are not redistributed in this repository. Configure only your
local settings:

```powershell
Copy-Item .env.example .env
# Edit .env locally with your own Zetaris token. Never commit it.
python register-data.py --compose-dir C:/zetaris-platform
python zetaris_schema.py
python register-evidence.py --compose-dir C:/zetaris-platform
python team.py --favourites Charizard --profile connected-demo
```

Start the supplied stack first. Registration copies public snapshot files to
DoublesCheck's dedicated driver folder and creates/retains its three tables.
Connected mode retains the real Pokedex/usage SQL join and also queries the
separate normalised Evidence Lens tables for a ranked partner shortlist. It stops on service failure;
there is no silent sample fallback. See [operations](docs/OPERATIONS.md).

## Verification

```powershell
python -m unittest discover -q
node verify-hmem.cjs
```

The Evidence Lens upgrade passed **174 application tests in each of two clean
installations**. Its [submission gate](docs/EVIDENCE_VERIFICATION.md) records actual
SQL/GUI rehearsal timings and the genuine AI repair regression.

Frozen Demo 3 result: **154 application tests passed** and **13/13 official H-MEM
conformance checks passed**. The tests make no cloud model requests. Stat arithmetic
was compared with Showdown, and separate running simulator fixtures checked
selected speed/field mechanics. The connected Zetaris workflow and GUI HTTP form,
report and progress flow also passed. Visual browser review was unavailable.
These results do not establish competitive team strength or production security.
See [verification](VERIFICATION.md) for scope and reproduction details.

## Documentation

| Guide | Contents |
| --- | --- |
| [Demo 1](docs/DEMO_1.md) | Milestone scope, walkthrough, expected behaviour and limitations |
| [Demo 2](docs/DEMO_2.md) | Preserved first live AI milestone |
| [Demo 3](docs/DEMO_3.md) | Verified repair, weather adaptation, recovery and varied cases |
| [Demo 4](docs/DEMO_4.md) | Visible Zetaris evidence, normalised tables and favourite-specific SQL ranking |
| [Demo 4 security audit](docs/SECURITY_AUDIT_DEMO_4.md) | Fresh history and exact release checks |
| [Security audit](docs/SECURITY_AUDIT.md) | Demo 1/2 history and Demo 3 publication checks |
| [AI reasoning](docs/AI_REASONING.md) | Model/tool/Critic loop, safety bounds and rubric mapping |
| [Current reasoning acceptance](docs/REASONING_ACCEPTANCE.md) | Dynamic roles, named repair contracts, continuation, case matrix and rubric evidence |
| [Architecture](docs/ARCHITECTURE.md) | Data flow, search, evaluator, H-MEM and module map |
| [Data and rules](docs/DATA_AND_RULES.md) | Sources, set generation, evidence and refresh procedure |
| [Operations](docs/OPERATIONS.md) | Setup, environment settings, storage, billing boundaries and troubleshooting |
| [Development](docs/DEVELOPMENT.md) | Tests, local changes, vendored code and contribution checks |
| [Roadmap](docs/ROADMAP.md) | Original vision, remaining features and hackathon alignment |
| [Changelog](CHANGELOG.md) | Milestone history |
| [Security](SECURITY.md) | Local-use boundaries and credential handling |

`demo.py`, `demo_connection_original.py`, `coaching.py`, `README-prototype.md` and
`HMEM-verification.md` retain earlier experiments. They are not the Demo 1 entry
point or evidence that the current application uses an LLM.

## Credits, licensing and affiliation

Built for the Open Agent Hackathon, with AI coding assistance. Showdown and the
Meterless reference implementation are pre-existing components, attributed with
their licenses and pinned sources. This repository does not claim a new battle
simulator or a newly invented memory engine.

The original project currently has no general redistribution license selected
(`UNLICENSED` in `package.json`). Public source visibility does not change the
separate licenses/rights of third-party software, data or franchise material.

Independent fan project. Not affiliated with Pokémon, Nintendo, Creatures or
GAME FREAK. No official artwork is included. This milestone does not certify
hackathon eligibility; remaining live reliability, player-validation and submission work are
described in the roadmap.
