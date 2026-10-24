# Demo 1 verification

Implementation verified on 23 October 2026; publication checks prepared on
24 October 2026. Results below are recorded checks, not a live CI status badge.

## Regression and reference checks

- **73 application tests passed**, including the earlier coaching tests with
  mocked model responses, actual H-MEM integration tests, real-data/team tests,
  progress/status tests and 23 battle-guidance tests.
- **13/13 official Meterless H-MEM conformance checks passed** against the app's
  facade. These are upstream conformance vectors, not an exhaustive security audit.
- Stat arithmetic matched the pinned Showdown implementation for 357 generated
  examples plus all 25 natures.
- Separate running local Showdown battle fixtures confirmed Choice Scarf/Tailwind
  rounding, unchanged Speed stats under Trick Room, Chlorophyll in sun,
  consumed-seed Unburden, inactive Focus Sash Unburden on entry and Iron Ball
  grounding. No external battle server was contacted.
- Cost-control tests confirm the legacy model gate fails before transport when
  opt-in is absent. The main GUI/CLI has no model-call path.
- Snapshot hashes in `data/sources.json` matched the prepared public files.

## Data and connected flow

Schema 2 contains 1,417 species/form records, 358 usage rows and 11,376 generated
legal set options across 357 supported species/forms. Source: November 2024
historical VGC Regulation H; the aggregate reports 965,304 ladder battles.

The real local Zetaris tables were refreshed and a SQL join reconstructed the
complete catalogue. It exactly matched the bundled sample. A connected Charizard
build preserved the lock, filled six slots, passed the full-team validator and
wrote HTML, JSON, team export and decision trace with zero model calls.

The GUI was reloaded with the improved code. Its HTTP form produced a complete
report and progress state. The report contained the new stat, speed, interaction
and opening-plan sections. Actual browser clicking and visual layout inspection
were unavailable, so those are not claimed as passed browser tests.

## Public example and comparisons

`examples/demo-1/` is a new, deliberately public sample run with isolated temporary
memory and no service credentials. It is not exported user history. Its complete
team is legality-checked and its model-call count is zero.

`quality-comparison.json` records five fixed earlier/revised builds. These use the
app's own supported conflict checks and a changed set-option pool; they are
regression smoke comparisons, not an independent competitive-strength benchmark.

## Reproduce the checks

```powershell
npm ci --ignore-scripts --omit=optional --no-audit --no-fund
python -m pip install -r requirements.txt
python -m unittest -q test_coaching test_hmem test_team_builder test_project_status test_battle_guidance
node verify-hmem.cjs
python team.py --sample --favourites Charizard --profile verify-sample
```

Sample mode needs no `.env` or running services. Connected verification additionally
requires the event-supplied local Zetaris stack, your own local settings and
registration of this version's dedicated snapshot files.

## Limits

These checks do not establish an optimal team, win probability, production
security or full hackathon eligibility. There is no current-2026 rule support,
damage/turn simulation, opponent-specific solving, optimized IVs or official
tournament-result corpus. EVs are historical investments, not verified survival
or knockout benchmarks. The slow-mode cutoff is a heuristic.

The main product does not use Nightshift/Nemotron yet. Older successful model
experiments and the subsequent unresolved routing failure remain historical work,
not evidence of reliable current-product AI integration. No model requests were
sent for Demo 1's team-quality, documentation or publication verification.

## Publication checkout checks - 24 October 2026

A clean checkout of the staged source installed 24 required npm packages from the
lockfile with lifecycle scripts disabled and optional dependencies omitted. It
contained no .env and reused no owner memory. All 73 application tests, 13/13
H-MEM conformance checks, source/snapshot hash checks, 18 relative documentation
links, a three-favourite sample build and public-example legality passed.

The exact staged files were scanned against actual service/GitHub credential
values, common secret formats and owner-specific private paths/contact details.
All 1,776 public base64 records were decoded and checked. The staged-file list
excluded service settings, private memory, user runs, logs, backups and installed
dependencies. No credential values were printed or included in this report.

## Demo 2 - verification, 24 October 2026

- 112 application tests passed, including 39 AI/tool/transport tests.
- 13/13 H-MEM conformance checks passed with the extension in place.
- A simulated critic required a real sourced set change for an unsupported
  Psychic Seed; the changed team passed independent legality and used new-version
  evidence. An unchanged resubmission after change-required criticism was refused.
- Tests cover locked/avoided species, full-source set identity including IV/Tera,
  issued IDs, stale citations, all-caution acknowledgement, forbidden tools,
  role authority, budgets, wrong model, authorization/rate-limit/server errors,
  redaction, malformed/truncated content, and no silent local fallback.
- End-to-end simulated AI report/trace persistence passed. Simulated output is
  explicitly labelled and is not live-model evidence.
- Isolated HTTP GUI checks passed: default sample remains model-free; combining
  Offline sample and AI is refused before service/model requests. JavaScript
  syntax checks passed. No visual browser review is claimed.

### Live connected result

Evaluation `961f5d9281f6439d8d626fedd9520f72` completed with real Zetaris data,
H-MEM preferences and the actual returned
`nvidia/nemotron-3.5-lightning-30b-a3b` identity through local Nightshift.
Charizard remained locked and Incineroar remained avoided. The model requested
inspection, submitted a balanced proposal and the Critic approved it with current
evidence and both cautions. Final independent team validation passed and the
HTML/JSON/export/trace were written. Three model requests, one executed tool,
zero revision rounds; approximately 70 seconds including local work.

The live model retained the local baseline. No live mutation or critic-required
repair is claimed. The separate simulated fixture proves that a real sourced set
change can be required and validated. A deliberately public copy of the live
evaluation, with synthetic memory identifiers removed, is in `examples/demo-2`.

A repeat balanced review `52f0c6423e374ebfbc41e240dbd54000` also completed:
three requests, one tool, zero revisions, the same retained six and approximately
79 seconds. Both runs used the approved concrete model. This small acceptance
check is not a statistical reliability estimate.

### Failures encountered and practical limits

- The Zetaris driver initially was stopped. It was restarted and became healthy;
  data-query failures made no model requests and produced no approved report.
- Initial model commands repeated an inspection or returned a generic `plan`.
  Completed-read guards, explicit one-command instructions and compact checked
  context were added. One bounded malformed-JSON repair is counted separately.
- Non-streaming requests repeatedly received HTTP 502 at around 45 seconds.
  The client now consumes bounded SSE and verifies the concrete model in the
  terminal metadata, rather than accepting preliminary `meterless/auto` frames.
- Streaming does not eliminate upstream failures. A subsequent rain-objective
  evaluation `9a2ab7f8e8114d01ba3cc9b6950c6d4a` stopped on a gateway stream error
  after two attempted model requests. No report, retry or provider fallback was
  produced. Complex-objective live adaptation remains unverified.
- Provider availability/limits and response latency remain prototype limitations.
  This verification is not a success-rate benchmark, competitive-quality study,
  provider SLA or assurance that every objective will complete within the budget.

The feature is available only through explicit AI mode; Demo 1's legacy
model-credit opt-in has not been enabled. No OpenAI/paid fallback was configured.

### Publication checks

The exact 105 staged public files were exported into a separate clean source
directory without `.env` or owner memory. Using the existing pinned dependency
installation, all 112 application tests and 13/13 H-MEM checks passed there.
Snapshot hashes, public live-example legality/export, sanitized memory metadata,
31 relative documentation links and package version consistency passed.

The staged blobs were scanned against actual local service/GitHub credential
values, common secret formats and private contact/path strings. All 1,776 public
base64 records were decoded and scanned. No secrets, private memory, user-run
folders, logs, backups or installed dependencies were included. Data and vendored
source bytes are unchanged from Demo 1. This is a targeted publication audit,
not an exhaustive security assessment.
