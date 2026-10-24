# Deliberately public live AI example

This is the real connected evaluation `961f5d9281f6439d8d626fedd9520f72`,
24 October 2026, using a synthetic test profile: favourite Charizard, avoided
partner Incineroar, beginner balanced objective. It contains no owner chat history.

Zetaris returned the historical catalogue, H-MEM supplied the preferences,
Nemotron requested `inspect_team`, the Planner submitted the current proposal,
the Critic approved with checked evidence, and the independent validator passed.

- Actual returned model: `nvidia/nemotron-3.5-lightning-30b-a3b`.
- Three model requests, one executed tool, zero revision rounds.
- The local baseline was retained. **This example does not demonstrate a live
  model-induced team mutation or a live critic-required repair.**
- Total observed workflow time: approximately 70 seconds, including local work.
- Both current cautions were acknowledged. No probability of winning is claimed.

Open `report.html` locally; `report.json`, `team.txt` and `trace.jsonl` provide
the structured result, Showdown import and decisions. GitHub shows HTML source.

Only the synthetic memory profile label and memory record identifiers were
replaced/removed for publication; team, model identities, call counts, decisions,
evidence and original event times are retained. No prompts, provider responses,
hidden reasoning, settings, keys or memory files are included.

The separate `test_ai_coach` regression fixture proves a critic can force a real,
source-backed Psychic Seed repair and new-version inspection. Those scripted
responses are explicitly simulated and must not be described as this live run.

Other live attempts encountered provider/gateway failures and were withheld.
One passing example is not a provider reliability guarantee. See the root
verification log and `docs/DEMO_2.md` for the current milestone scope.
