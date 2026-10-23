# DoublesCheck — Demo 1

Build and understand a Pokémon VGC doubles team around your favourites.

DoublesCheck is for beginners who know which Pokémon they like but need help
choosing partners, legal sets and a starting play plan. Lock **one to six Pokémon**;
the app fills the remaining slots or reviews the six you supplied. It preserves
your locked species and explains the choices and trade-offs.

**Demo 1 is a working local planning prototype.** It uses real historical data,
Meterless H-MEM and Pokémon Showdown validation. The current product makes
**zero cloud AI model calls**. Nightshift/Nemotron integration is unfinished in
the main product; separately retained legacy experiments are disabled by default.

## Try it without accounts or API keys

Requirements: Python 3.10+, Node.js 22+ and npm. Windows was used for verification.
The bundled sample is real historical data; it is not a random mock catalogue.

```powershell
git clone https://github.com/arhumamjad07/DoublesCheck.git
cd DoublesCheck
npm ci --ignore-scripts --omit=optional --no-audit --no-fund
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:8765>, select **Offline sample**, enter `Charizard` and
choose **Build and check my team**. The form initially selects connected Zetaris
mode, so switch it for this account-free demonstration.

If you already have the Python dependencies installed, `python app.py` works too.
`Start-DoublesCheck.bat` uses the `python` on your PATH. On macOS/Linux, use
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

## Connected Zetaris mode

Use the event-supplied Zetaris Docker Compose installation; its platform and
container images are not redistributed in this repository. Configure only your
local settings:

```powershell
Copy-Item .env.example .env
# Edit .env locally with your own Zetaris token. Never commit it.
python register-data.py --compose-dir C:/zetaris-platform
python team.py --favourites Charizard --profile connected-demo
```

Start the supplied stack first. Registration copies public snapshot files to
DoublesCheck's dedicated driver folder and creates/retains its three tables.
Connected mode queries a real Pokedex/usage SQL join. It stops on service failure;
there is no silent sample fallback. See [operations](docs/OPERATIONS.md).

## Verification

```powershell
python -m unittest -q test_coaching test_hmem test_team_builder test_project_status test_battle_guidance
node verify-hmem.cjs
```

Recorded Demo 1 result: **73 application tests passed** and **13/13 official H-MEM
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
hackathon eligibility; the remaining AI integration and submission work are
described in the roadmap.
