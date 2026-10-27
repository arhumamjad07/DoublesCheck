# Evidence Lens submission gate — 27 October 2026

**Decision: GO for tonight's local demonstration and submission upgrade.**
Feature work froze at approximately **15:47 UTC**, ahead of the 18:30 UTC cutoff.
The decision followed two independent clean installations, real local Zetaris
rehearsals and a genuine Nightshift repair regression. This is a demonstration
readiness decision, not a competitive-strength or provider-availability guarantee.

## Preserved baseline

- `demo-3`: `acc708bf565d786e1d1d1bcde3903fe8229b7192`.
- Work occurred on `challenge/zetaris-evidence-lens`, in an isolated worktree.
- Existing `examples/`, `vendor/`, `data/catalogue.json`, `data/sources.json` and
  original `data/zetaris/` files are unchanged from Demo 3.
- Saved genuine runs and owner preferences were not erased. Offline mode retains
  its original catalogue and builder. Existing model budgets and source/legality
  guards remain unchanged.

## Automated checks

| Check | Result |
| --- | --- |
| First visible Lens slice | 160 application tests passed, including the original 154 |
| Final full suite, clean installation 1 | **174 passed**, 185.775 seconds |
| Final full suite, clean installation 2 | **174 passed**, 186.090 seconds |
| Official H-MEM conformance, both clean installations | **13/13 passed** each |
| Focused final Lens/HTTP/continuation checks | Passed |
| Connected catalogue versus bundled snapshot | Exact semantic equality |
| SQL ranking versus independent sample projection | Equal for Charizard, Pelipper and Charizard + Sneasler with avoidance |
| Same returned pool with connected/sample facts | Same independently valid team |
| Controlled changed pool | Changes the actual recommendation |
| Corruption and failure tests | Missing/duplicate rows, malformed values, historical mismatch and unsafe SQL inputs refused |
| Connected SQL failure over HTTP | Result withheld before builder invocation; no sample fallback |
| Offline / saved-report labels | Explicitly tested |
| Public receipts | Allowlisted fields only, no transport/header/URL/raw-SQL data copied |

Tests use service fixtures where stated. They do not pass fixture output off as
live model evidence or live Spark output. Live checks below are separate.

## Clean setup and exact recording path

Two independent source exports used fresh Python 3.13.14 virtual environments,
dependency installation from the unchanged requirements and npm lockfile, both
registration commands and normalisation. No installed `node_modules`, existing
virtual environment, owner memory or saved run was copied into these setups.
Local `.env` credentials were supplied privately for connected tests.

Windows PowerShell initially blocked `npm.ps1`. The sequence then passed using
`npm.cmd`, without changing execution policy. The setup guide now states that.

`verify-evidence-path.py` exercised genuine HTTP form submissions, real SQL,
report/progress output and the labelled saved repair. Each installation passed:

| Fresh installation | Charizard build | Pelipper build | Query totals | Result |
| --- | ---: | ---: | --- | --- |
| 1 | 13.310 s | 12.469 s | 7.023 / 6.924 s | Passed |
| 2 | 13.221 s | 12.517 s | 6.904 / 6.927 s | Passed |

Both paths considered 356 eligible partners, returned 48 and made **zero model
requests**. Charizard's first SQL partner was Torkoal; Pelipper's was Archaludon.
Both final teams preserved the chosen favourite and passed historical legality.

Both browser rehearsals then repeated Charizard → inspect/expand receipts →
Build another team → Pelipper → labelled saved genuine repair, using fresh demo
memory profiles. The two independent installs displayed the expected changed
query evidence and teams. The second browser showed no recorded console errors.
The recording navigation was corrected to remain on the active app's origin.

The viewed Pelipper report `7436afa847504fa682298a5854cb6df4` supplied the actual
27 October product screenshot. Its query total was 6.714 seconds. These timings
are observations on this machine, not a latency promise.

## Genuine reasoning regression

```powershell
python evaluate_reasoning.py --live --cases seed-repair --env-file .env --max-model-requests 8 --resume-once
```

The existing declared legal Sneasler fixture passed through actual
`nvidia/nemotron-3.5-lightning-30b-a3b` requests via local Nightshift. It used
**seven requests**, **one Critic revision**, and a real set change. The named
`missing_seed_terrain` condition resolved in version 2, the requested objective
was met, and the final team passed independent historical validation.

There was **one gateway stream interruption** and the explicitly authorised
single continuation. Total time: **364.672 seconds**. The original failure was
not relabelled or removed. Private acceptance suite:
`62c3216b709f433aafcd846c9c42d929`; case:
`e2edd244c9364af3bc8dfab924cd2f34`. These are synthetic evaluation identifiers,
not a claim of personal battle history.

The recording still uses the proven, clearly labelled 25 October saved repair,
about 271 seconds originally. It does not require another live AI run on camera.

## Security and publication

The candidate and all reachable Git history were checked for actual locally
available credentials, credential patterns, private paths, author contacts and
accidentally tracked settings/state. No real credential or private-data leak
was detected. Gitleaks 8.30.1 identified eight previously reviewed generic matches
in encoded public Pokémon CSV rows. Each was checked as an exact catalogue
projection. A decoded-source independent scan returned zero findings, including
the new normalised tables. Credentials and raw scanner matches were not printed.

This describes the checks performed, not a guarantee that any scanner can detect
every possible secret. `.env`, runs, memory, logs, dependencies and private audit
helpers remain excluded from publication.

Only the affected sponsor content on **slide 5**, product screenshot on **slide
7** and recording script were updated. The other six slides and notes remain
byte-identical in the PPTX and pixel-identical after rendering. The PDF companion
replaces only pages 5 and 7. Original submission artifacts remain available.

## Remaining risks and exact recording sequence

Use the three-minute sequence in `ZETARIS_EVIDENCE_LENS.md`: live Charizard SQL
Lens, sanitised receipt, live Pelipper comparison, **saved** genuine Sneasler
repair, sponsor boundaries and limitations. Use the revised recording script
for the complete hackathon video, kept below four minutes.

- Docker/driver availability is required for connected mode; failures withhold output.
- Nightshift gateway interruptions remain possible. No paid/provider fallback was added.
- Partner association is a heuristic signal, not win rate, optimality or causal compatibility.
- Historical Regulation H / November 2024 only; no current-2026 eligibility claim.
- No hands-on player outcome study, second month, opponent preview or PokéAPI feature.
- The separate Grok/SpaceXAI prompt is prepared, **not performed**. Do not claim its evidence.
- The final hackathon form, video upload and submission confirmation remain the creator's task.
