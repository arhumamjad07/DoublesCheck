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

## Demo 3 — reasoning acceptance, 25 October 2026

This extends the preserved Demo 2 milestone. It addresses live reliability,
Critic-required real correction, and varied user situations. These verified changes
form the Demo 3 milestone; earlier release tags remain preserved. Saved summaries are in
[reasoning acceptance evidence](examples/reasoning-acceptance/README.md), with
per-suite implementation fingerprints. Iterations are separate evidence, not one
aggregated reliability estimate. Documentation/status wording was refreshed after
some live runs; their captured fingerprints identify the versions used then.

### Offline and protocol checks

- **154 application tests passed** using `python -m unittest discover -q`.
  No cloud model requests are made by those tests. Simulated responses are
  explicitly labelled; source data, H-MEM child processes and validators are real.
- **13/13 official H-MEM conformance checks passed**. Vendored reference source,
  compiled runtime, dependency lock and prepared Pokémon data are unchanged.
- Declared offline suite `637540197d0b4238b91218744b993b50`: **12 passed,
  0 failed, 1 skipped, 0 model requests**. Rain is intentionally skipped without
  live AI. Offline seed detection is not presented as live AI correction.
- Named revision contracts reject unrelated legal edits and different sets that
  leave the same issue. Stale options/evidence and wrong affected species are
  refused; disclosure is separate from repair.
- Real six-lock regression: Charizard, Pelipper, Torkoal, Rillaboom, Indeedee-F
  and Sneasler previously could be falsely rejected by beam pruning. Exact
  distinct-item forward matching now retains a feasible branch. An independent
  exhaustive oracle checks the matching on 80 deterministic small domains.
- Invalid, unsupported, duplicate and conflicting inputs are checked before
  preference updates. The H-MEM adapter checks the effective locks/avoidance
  under its profile lock before committing either explicit preference.
- Protocol tests check authenticated model discovery before a POST, missing
  concrete route, final model identity, stream completion, corruption, limits,
  safe fixed-vocabulary diagnostics and suite budgets including failed calls.
  Transport/envelope corruption does not receive a semantic JSON repair.
- Authenticated HTTP continuation passed with simulated model responses: missing
  form token cannot continue; an interrupted build returns 503 with a manual
  continuation; the same review later completes; repeated continuation makes no
  extra request. Report/progress and HTML escaping remain checked.
- Continuation tests cover original request/time budgets, no tool replay,
  changed preferences, expiry, concurrency and finished-state refusal.
- A sourced rain adaptation is also exercised with scripted responses and full
  real team validation. This test is separate from real model acceptance.

### Genuine live repair

Run `9e375830601240a5a2ea5d590bb2e9cd` used real Zetaris, actual H-MEM and
`nvidia/nemotron-3.5-lightning-30b-a3b` through Nightshift. The declared legal
fixture contained Sneasler with Psychic Seed/Unburden and no Psychic Terrain
setter. It is a deliberate evaluation input, not a claimed spontaneous builder
failure. Charizard/Sneasler were locked; Incineroar was avoided.

The Critic required a change for `missing_seed_terrain`; the Planner investigated
sourced choices and selected Focus Sash/Poison Touch. The edit created version 2;
the named issue disappeared. The Planner submitted new evidence, the Critic
approved and the full independent historical validator passed. **Seven actual
model requests, one revision round, one real set mutation, no continuation,
approximately 271 seconds.** No model decision or verdict was scripted.

[Public input/report/export/trace](examples/reasoning-repair/README.md) retain
actual decisions and times, with synthetic memory labels/IDs removed or replaced.
Two subsequent real repair runs (`087926cb620d4fc4b0ae0cd31d80b58a` and
`d706815e43d04bb58987748b0da285a5`) also passed in seven requests each. The
latest uses edit-delivered fresh validation rather than requiring a separate
model inspection round trip. That local validation is not counted as an
additional AI-requested tool.

### Genuine recovery and broader cases

Core live suite `40c3def5556c46178e370fc444bfa792`: **9 acceptance cases
passed, 13 total attempted model requests, 4 live approved team reports**.
The other five passed cases are expected input refusals with zero model calls;
they are not AI approvals. One, three and six favourites were preserved; the
remembered-avoidance case recalled the constraint through a fresh H-MEM process.

Run `64dc42d4cca84e2b8915f9fa0808e0ad` genuinely encountered a gateway error,
paused, explicitly continued once and passed. **Four requests including the
failed attempt**; the baseline was retained and only the Critic role ran. Its
trace has one catalogue load, one build (five slot-fill events) and one executed
inspection. Successful work was not replayed.
[Public recovery proof](examples/reasoning-recovery/README.md).

Extended suite `0c970a67cbfa47189d7727da37e62c3a`: **3 passed, 1 failed,
17 model requests, 3 live approvals**. It includes the second real seed repair,
a live remembered avoidance of Torkoal that actually changes the team compared
with the otherwise identical unconstrained reference, and six retained favourites
with disclosed field-effect trade-offs. The rain case was withheld after two
provider interruptions, despite one explicitly authorised continuation.

Suite `ea72530a2338468889794a553240069f`: **1 passed, 1 failed, 14 model
requests, 1 live approval**. Seed repair passed again. Rain encountered a provider
interruption, one continuation, invalid tool arguments and another interruption;
no team was approved. This exposed ambiguous mode-vs-condition repair guidance,
which was subsequently clarified. Its failure remains in the evidence.

The subsequent rain suite `ff1f252c75f74804b6db6b3f18a2ac0e` passed. Run
`1c3663366e604c65b102de197a53cb09` completed in **six real model requests,
one Critic revision round, no continuation, approximately 249 seconds**. The
Critic identified missing rain support; the Planner searched weather partners,
selected Pelipper and invoked a real rebuild. Drizzle support appeared in version
2, the named objective contract resolved, the Planner submitted a rain strategy,
and the Critic approved after independent validation. Charizard stayed locked;
Incineroar stayed avoided. The report discloses rain weakening Fire attacks and
leaving Solar Power unsupported. This demonstrates delivery of the scoped rain
objective, not that Charizard is optimal on rain teams.
[Public rain report/trace](examples/reasoning-rain/README.md).

The later context retention regression additionally verifies that two refused
tool commands do not erase successful source-search results from model context;
all eight attempts still count toward the original budget. That context-only
fix and dashboard wording postdate the live rain run's recorded fingerprint.

### Practical boundaries

The product uses Critic-first dynamic delegation. A good candidate can finish
without a model Planner; a named criticism dispatches the Planner. Both roles use
the same model. Independent code enforces constraints, specific repair completion,
objective labels, source sets, new-version evidence and final legality. Reports
record actual roles, edits, model identities and requests rather than a fabricated
private reasoning transcript.

Discovery checks do not prove a future request will succeed. Gateway stream
errors still occur, commonly near 45 seconds, and are safely withheld. The
1,024-token thinking-budget hint may be ignored by the installed gateway; its
enforcement is not claimed. The independent hard output cap remains 8,192 tokens.
There is no direct NVIDIA/OpenAI route, paid fallback or automatic HTTP retry.

The GUI permits manual Continue; the acceptance CLI requires explicit
`--resume-once`. Both preserve the eight-request lifetime case budget and completed
work. Partial output is not approved. No provider SLA, free/unlimited quota,
current-2026 rules compliance, competitive strength or higher win rate is proved.

### Rubric and remaining work

The supplied Track 3 guidance asks for useful decisions from data, knowledge,
memory and reasoning, with critique, dynamic interaction, shared state and
recovery. These now have concrete live or separately labelled regression proof.
This primarily strengthens Technical (20), Demo evidence (15) and working Sponsor
Tech (10). It supports Innovation (15) without proving uniqueness. Impact (30)
and UX (10) still need player feedback. No awarded/predicted score is claimed.

Final player validation, video, slides, submission fields and any deeper battle
simulation remain unfinished. A public repository and passing tests alone do
not complete the hackathon submission.

### Final delivery checks

The final 154-test discovery run passed in approximately 89 seconds. Generated
browser JavaScript passed its syntax check. Five saved public team examples
passed full legality/export checks; the repair input matches exact prepared sets
and the original recorded fingerprint.

The local app, status page, repair report and acceptance report returned HTTP
200 after the changes were applied to the main project. Browser inspection
confirmed readable builder/report layouts, Offline sample disabling AI, AI mode
enabling its objectives, and the visible resolved issue with actual before/after
item/ability values. Manual continuation is covered by authenticated HTTP tests;
its paused screen was not forced through an additional live model failure.
This is a limited interface check, not a beginner usability study or full
responsive/accessibility audit.

The 138 deliberately selected public files passed scans against actual local
service/GitHub credential values, common secret formats and private owner paths.
All 1,776 encoded public records were decoded and checked. Fifty-five relative
project documentation links and the snapshot/vendor hashes passed. Settings,
owner memory, run folders and dependencies remain excluded. Private synthetic
evaluation records were retained locally for review, including failed attempts.
At that pre-publication checkpoint no new commit, tag or push had been made;
the Demo 2 milestone was preserved. Demo 3 publication follows the additional
history/staged-source audit below. This is a targeted audit, not a
guarantee of production security.

### Demo 3 publication security review

The refreshed remote contains two prior commits and the annotated Demo 1/2 tags.
The checkout is not shallow. Every reachable blob, commit and tag object was
checked, including old/deleted file contents and commit/tag metadata. No actual
service/GitHub credential value, private owner path/contact or runtime/settings
file was detected. Only intended public GitHub identity appears in commit metadata.

Gitleaks 8.30.1 also scanned the full history and the selected release with
recursive decoding and full redaction. Eight generic-key matches per scan were
reviewed individually: all were two-field public Pokémon CSV records whose
decoded values match the source catalogue. An independent scan retaining all
1,776 decoded records reported no leaks. A separate URL-pattern match is an
AST-verified fake loopback rejection fixture, not a service login.

The exact staged release is scanned again before commit, and the resulting
commit/tag are checked against the audited tree before pushing. Local settings,
memory, evaluation runs, scanner binaries/reports and audit helpers are excluded.
See [security audit](docs/SECURITY_AUDIT.md). This records targeted checks and
reviewed false positives, not a guarantee that any scanner detects every secret.
