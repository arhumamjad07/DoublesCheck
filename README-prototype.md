> Legacy three-Pokemon demonstration. Model requests are now disabled by default. See README.md and run app.py or team.py for the current credit-free real-data version.

# DoublesCheck checked coaching prototype

This is a small connection-and-review demo, not the completed hackathon app.

## Run

Start Zetaris's query engine and API, and leave Nightshift open with its NVIDIA
lane ready. The existing project `.env` supplies both services' credentials.

```powershell
python -m pip install requests python-dotenv
python demo.py
python demo.py --favourite Blastoise
python -m unittest -q test_coaching test_hmem
```

The offline tests do not call external services. A live run makes one read-only
Zetaris SQL request and two to four AI calls. Transport calls do not retry.
Each AI call has an 8192-token ceiling (including model reasoning) and a
150-second read timeout. Nightshift 1.2.1 does not forward the public API's
`chat_template_kwargs`; this demo does not claim to disable reasoning.
The builder and evaluator are separate calls to the same configured model.
There is at most one critique-driven revision followed by another evaluation.
If review still fails, no recommendation is approved and the command exits nonzero.

## Working Meterless Engine feature: H-MEM player preferences

The app uses the official Meterless H-MEM reference engine through a small local
Node bridge. Explicit player preferences become sourced memory records with
provenance and an audit ledger. Later runs use H-MEM's hybrid retrieval and
reinjection formatter to recall those records into both Builder and Evaluator
prompts. Python also excludes an avoided partner from eligible choices, so an
AI approval cannot bypass that constraint.

This example uses a separate demonstration profile. Avoiding Blastoise is an
illustrative test preference, not an assumption about your actual preferences.

```powershell
# Save preferences without calling Zetaris or any model.
python demo.py --profile memory-proof --favourite Charizard --avoid-partner Blastoise --memory-only
# Fresh process: recall without entering those preferences again.
python demo.py --profile memory-proof --memory-only
# Coach using the recalled preferences: only Venusaur remains eligible.
python demo.py --profile memory-proof
# Explicitly clear avoidance when desired; favourite remains saved.
python demo.py --profile memory-proof --allow-all-partners --memory-only
```

`--favourite` changes the stored favourite; omitting it recalls the existing value.
An empty profile defaults to Charizard without claiming that value was remembered.
Profiles use separate local directories. Corrections supersede earlier records;
superseded preferences remain in history but are excluded from the app's prompts.
Only explicit inputs are saved: model suggestions never silently become player
preferences. `--allow-all-partners` explicitly deletes the active avoidance record
and logs the reason. Memory lives in `.doublescheck-memory/` and is ignored by Git.

The bridge uses an installed Node runtime, including Nightshift's bundled Node on
Windows. Set `DOUBLES_CHECK_NODE` to a Node executable if automatic discovery fails.
Compiled engine files are included; no npm install is required to run the app.
The engine adds no AI calls. A locked or unreadable memory profile stops the run
before service calls rather than silently discarding preferences.

### Engine source and verification

Vendored from [Meterless H-MEM](https://github.com/Meterless/Meterless/tree/1742dec56a66e58eef9dda2d2b865823758ca8cd/engines/hmem),
commit `1742dec56a66e58eef9dda2d2b865823758ca8cd`, under Apache-2.0.
`vendor/hmem/UPSTREAM.json` records source hashes and `vendor/hmem/LICENSE`
preserves the license. Upstream TypeScript is unmodified; generated JavaScript
and a small application facade persist retrieval access counters between runs.

Run the official conformance suite against the facade:

```powershell
$env:HMEM_IMPL = (Resolve-Path .\hmem-engine.mjs).Path
node vendor/hmem/compiled/conformance/runner.mjs
```

If Node is not on PATH, use Nightshift's bundled executable:
`& "$env:LOCALAPPDATA\Nightshift\node\node.exe" vendor/hmem/compiled/conformance/runner.mjs`.
`build-hmem.mjs` regenerates compiled files using Node 24's built-in TypeScript
transformer; rebuilding is not required for normal use.

The integration tests launch real engine processes and verify persistence,
profile isolation, corrections, clearing, duplicate prevention, lock handling,
and enforcement of remembered constraints in the coaching workflow.

## What is checked

- Locked favourite and teammate membership in a three-row mock catalogue.
- Incoming Water, Electric and Rock type effectiveness for normal-form Charizard,
  Venusaur and Blastoise. Dual-type multipliers are multiplied in Python.
- Structured numerical claims must match the computed evidence.
- Published explanations, trade-offs and beginner guidance are generated from
  checked multipliers, replacing free-form model prose before evaluation. This
  prevents a contradictory prose claim from bypassing correct numerical checks.
  The AI proposes the teammate; Python supplies its scope-limited factual explanation.
- The evaluator separately reviews the narrative and requests changes when needed.
- Logs in `logs/<trace-id>.jsonl` record actual requests, model IDs, checks,
  critique and approval/withholding. They are not fabricated example traces.

Type source: https://github.com/smogon/pokemon-showdown/blob/master/data/typechart.ts
The relevant subset is embedded and does not update automatically.

## Important limits

Mock Pokemon records are returned by a SQL CTE, not a persistent catalogue.
No regulation is selected and legality remains `not_verified`. These checks do
not validate moves, abilities, items, EVs, IVs, Mega Evolutions, damage or history.
Defensive resistance does not imply a legal move, offensive coverage, automatic
protection of an ally, or overall team quality. A pair is not a complete team.
The separate evaluator still uses the same model and is not guaranteed to catch
every narrative error. Its approval applies only to this explicitly limited demo.

H-MEM here uses the reference engine's deterministic hash embeddings and local
JSON persistence. It is a prototype storage setup, not a production database or
semantic embedding service. A per-profile lock prevents simultaneous app writes;
it does not provide crash recovery or multi-user authentication. The application
uses explicit preference capture and retrieval; it does not automatically run
memory mining, dreaming or sleep consolidation. Those services remain available
in the reference engine and are exercised where covered by upstream conformance.
Historical data imports, full teams, an interface, and proper format-specific
legality are future work.

The old script is preserved as `demo_connection_original.py` when first upgraded.
Keep `.env` private. Neither keys nor raw service error bodies are logged.
