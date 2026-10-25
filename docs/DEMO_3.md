# Demo 3 — verified AI reasoning and recovery

Milestone tag: `demo-3`. Commit: `Demo 3: verified AI reasoning and recovery`.
Demo 1 and Demo 2 tags remain available with their original contents.

## What changed from Demo 2

Demo 2 established a real AI review that could retain a legal baseline. Demo 3
demonstrates the Critic finding a named problem, dispatching the Planner, applying
a source-backed change, checking that the problem disappeared and approving the
new version. Roles use the same Nemotron model; code retains final authority.

- **Actual repair:** Psychic Seed/Unburden Sneasler without Psychic Terrain was
  changed to a sourced Focus Sash/Poison Touch set. Seven real requests, one
  revision round and a validated new team version. The input is a declared legal
  evaluation fixture; no live model decision was scripted.
- **Actual weather adaptation:** a rain request triggered a partner search, the
  AI's Pelipper choice and a real rebuild. Charizard remained locked and its rain
  trade-offs were disclosed. Six real requests and final approval.
- **Actual interruption recovery:** one review encountered a genuine gateway
  error, explicitly continued and completed without replaying successful work.
- **Broader cases:** one, three and six favourites, memory changing the output,
  conflicting preferences, unsupported/unknown species and retained trade-offs.
- **Stronger controls:** specific repair contracts, shared source results, new
  evidence after edits, authenticated model discovery and bounded continuation.
- **Search/input fixes:** exact distinct-item forward matching and validation
  before preference updates prevent observed false refusals and memory corruption.

## Run and inspect

Start the supplied Zetaris Docker stack and Nightshift. Store tokens only in
local settings and the NVIDIA key in Nightshift. No OpenAI key or paid fallback
was added. Launch `python app.py`; connected AI is explicit, local planning is
the default, and Offline sample always makes zero model requests.

Saved genuine examples can be opened without new requests:

- [Critic-required repair](../examples/reasoning-repair/README.md)
- [Weather-goal adaptation](../examples/reasoning-rain/README.md)
- [Interruption and continuation](../examples/reasoning-recovery/README.md)
- [Acceptance summaries, including failures](../examples/reasoning-acceptance/README.md)

For a new real repair evaluation with your own local services:

```powershell
python evaluate_reasoning.py --live --cases seed-repair --max-model-requests 8 --resume-once
```

`--resume-once` explicitly authorises one continuation for that case. The GUI
requires manual Continue. Eight lifetime requests, twelve tool attempts and two
revision rounds remain enforced. Completed work is retained in RAM, at most four
paused reviews, for 30 minutes after pausing while the app remains open. Requests
do not automatically switch providers or reset budgets.

## Evidence and remaining limits

154 application tests and 13/13 H-MEM conformance checks passed. The offline
acceptance matrix passed 12 applicable cases and skipped rain. Scripted tests
and live results are separately labelled; failures remain in the verification
log. Repeated passing runs are not a statistically measured reliability rate.

The architecture maps to Track 3's data, knowledge, memory, critique, shared state
and recovery expectations. Impact and UX still need player feedback. The final
video, slides and submission fields remain unfinished. A recording should make
elapsed service time and use of saved real evidence clear.

Historical Regulation H/November 2024 only. No current-2026 rules, damage
simulation, optimized IVs, competitive win rate or best-team claim. Provider
interruptions still occur; incomplete results are withheld. NVIDIA quota is
separate from ChatGPT/Codex allowance.

See [architecture](REASONING_ACCEPTANCE.md), [verification](../VERIFICATION.md),
[security audit](SECURITY_AUDIT.md) and [roadmap](ROADMAP.md).
