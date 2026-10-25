# Real interrupted review and explicit continuation

Evaluation `64dc42d4cca84e2b8915f9fa0808e0ad`, 25 October 2026, used actual
Zetaris, H-MEM and the approved NVIDIA model through Nightshift. This was a
naturally interrupted live service call, not an injected model response.

The runtime reported a stream error. The review paused without approving a
partial result. The acceptance invocation explicitly enabled `--resume-once`,
so it continued the same review within its original budget and subsequently
completed Critic approval and full local validation.

Four model requests total, including the failed attempt. One continuation. The
local candidate was retained, not changed. Only the Critic model role was used.
The trace records one catalogue load, one build (five slot-fill events) and one
executed `inspect_team`; successful work was not replayed. This demonstrates
recovery, not a team repair or guaranteed provider reliability.

The GUI requires a manual Continue action and does not retry automatically.
The CLI's one-continuation option is explicit and recorded in suite output.
Both preserve the original lifetime request budget.

The synthetic memory profile label and record identifiers were removed/replaced
for this example. Decisions, errors, event times, model identities and counters
remain actual. No raw provider errors, prompts, private reasoning, settings,
credentials or owner history are included. This was a development iteration;
see the verification log for suite-specific code fingerprints.

Open `report.html` locally, or inspect `report.json` and `trace.jsonl`.
