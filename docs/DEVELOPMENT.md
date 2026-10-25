# Development and verification

## Entry points

Use `app.py` for the GUI and `team.py` for the current pipeline. The module map
is in [architecture](ARCHITECTURE.md). Retained `demo.py`/`coaching.py` experiments
are historical integration work and are not the default product.

## Local checks

Install the pinned npm dependencies and the Python requirements first. Run:

```powershell
python -m unittest discover -q
node verify-hmem.cjs
```

These are the regression and H-MEM conformance checks. Do not substitute
`test_meterless_connection.py`: that is a separately gated, one-shot live-service
script, not part of the model-free test command.

| Area | Verification |
| --- | --- |
| Legacy coaching | Deterministic fact checks, refusal/revision bounds and mocked false model approval |
| H-MEM integration | Actual child processes, fresh-process recall, provenance, corrections, clearing, profile isolation and locks |
| Teams/data | Real snapshot, one/three/six locks, avoidance, banned species, independent move/item/EV validation, explicit sample mode and cost gate |
| GUI status/progress | Trace isolation, partial writes, terminal states, invalid/reused IDs and honest roadmap wording |
| Battle guidance | Independent stat arithmetic, all 25 natures, selected running-simulator fixtures, terrain/priority, seed/weather/ally-hit conflicts, contradictory locks and HTML escaping |

Demo 1 recorded 73 tests; Demo 2 recorded 112. Current development passes 154,
plus 13/13 official H-MEM checks. The new suites cover named repair contracts,
recovery, input integrity, feasible locked-item search, transport protocol and
authenticated HTTP continuation. They use simulated model responses; H-MEM,
source data and legality checks are real. See the root
`VERIFICATION.md` for the milestone's precise scope. Existing installation scripts
and GUI HTTP checks were also exercised locally; actual browser clicking/visual
review was not available.

## Independent references and comparison limits

The stat test compares 357 generated examples plus 25 nature cases with
Showdown's arithmetic. `reference-mechanics.cjs` creates local simulator battles
to independently check selected Speed/field behaviours. It never connects to
Pokémon Showdown's public servers.

`quality-comparison.json` records five fixed earlier/revised builds. The revised
version also has richer set options. Its conflict labels use the app's own checks;
they are regression evidence, not a blinded user study, exhaustive benchmark,
competitive rating or proof of a higher win rate.

## Changing search or coaching

Keep favourite/avoidance constraints independent of heuristic scoring. Retain the
full-team validator and refusal path. Describe new scoring terms, dependencies
and assumptions in the architecture/data guides. Add tests for a real failure
case, especially where legal choices can still conflict in play.

Avoid inventing survival, damage, matchup or win-rate claims. A new conditional
mechanic should be checked against a primary implementation and labelled with
its supported scope. A report can explain uncertainty rather than fabricate a
specific benchmark.

The current type-balance term uses original types, while ally-hit warnings cover
some additional immunities. Neither should be described as complete damage
calculation or automatic Tera strategy.

## Rebuilding data or H-MEM

`python refresh-data.py` rebuilds the pinned public data and prepares Zetaris
CSVs. Review changes to sources, option counts, manifests and resulting teams.
Re-register only DoublesCheck's dedicated local files for connected verification.

The H-MEM source manifest pins the upstream commit and source hashes. The app's
facade persists retrieval counters; upstream source is kept separate from that
adaptation. `node build-hmem.mjs` rebuilds the committed compiled runtime on a
Node release supporting `stripTypeScriptTypes`. Preserve the source manifest,
Apache license, attribution and conformance checks when making an intentional
upstream update. Do not edit vendored code merely to make a failing test green.

## Public commits

Use `.env.example` placeholders, never real keys. Keep runtime memory, generated
user runs, logs, backups, virtual environments and `node_modules` out of Git.
The prepared data contains encoded JSON, so inspect decoded records as well as
plain text when auditing a publication. The deliberately public example is
generated from a separate temporary profile, not exported user history.

Git attributes preserve exact bytes for hashed public snapshots and vendored
sources. Changing line-ending handling there requires regenerating/reviewing
the corresponding hashes.

Check `git diff --cached --stat` and the actual staged content before pushing.
Treat local preference/audit logs as private even when they contain no API keys.
Do not enable a cloud-model route or a paid API as part of routine testing.

## Explicit AI extension

`nightshift_client.py` owns the bounded transport; `agent_tools.py` owns the tool
contracts and evidence ledger; `ai_coach.py` owns the Planner/tool/Critic state
machine. See AI_REASONING.md. Tests inject simulated responses, never provider
credentials. Offline and simulated execution must not be labelled live evidence.
The existing source snapshot and legality checks remain authoritative.

The current architecture is in [reasoning acceptance](REASONING_ACCEPTANCE.md).
`reasoning_contracts.py` checks named repairs and objectives; `CoachSession`
retains suspended decisions without replaying successful work. The GUI's manual
Continue path and the explicitly authorised CLI continuation share that code.
`python evaluate_reasoning.py` runs the declared offline cases. Only `--live`
permits real connected/model requests; `--max-model-requests` bounds the suite.

Stream tests cover fragmented content, ignored private reasoning, preliminary
routing aliases, final model identity, missing completion, provider error frames
and truncation. A gateway success or health check alone is insufficient evidence
of a completed coach run.
