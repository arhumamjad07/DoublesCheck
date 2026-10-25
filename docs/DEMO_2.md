> Historical Demo 2 milestone. Its limitations below describe that release;
> see [Demo 3](DEMO_3.md) for later live repair and recovery evidence.

# Demo 2 - explicit AI reasoning

Demo 1 (`demo-1`) established the local data, memory, legality and coaching tools.
Demo 2 adds an explicitly selected Nightshift/Nemotron Planner/tool/Critic loop
around those tools. Two real connected balanced reviews completed in three model
requests each, retaining the legal baseline. The [public live example](../examples/demo-2/README.md)
records the actual decisions; scripted revision evidence is labelled separately.

**Preview limitation:** upstream model/gateway errors still occur. A rain-objective
attempt was withheld on a stream error. Live team mutation and live critic-required
repair have not been demonstrated. See the [verification log](../VERIFICATION.md)
for failures as well as the passing result. This is not a reliability guarantee.

## Material difference from Demo 1

| Demo 1 | Demo 2 |
| --- | --- |
| Local bounded team search | Local baseline plus model-selected tool use and permitted team/set edits |
| Local validation only | Distinct Planner and Critic roles, with independent local checks retaining final authority |
| No cloud model requests in the main product | Explicit AI mode through the local Nightshift gateway to the approved NVIDIA model |
| Static local reasoning trace | Requested/actual model, tool decisions, evidence versions, critique, mutations and approval/refusal |
| Factual local report | The same report plus AI-selected checked evidence, actual changes and acknowledged cautions |

The existing local/sample flow stays available. This is a feature milestone,
not a claim of a completed hackathon submission, trained foundation model,
guaranteed competitive team or production-ready service.

## Run

Start the supplied local Zetaris stack and Nightshift. The Zetaris `driver`
and API must be healthy; Docker merely being open is insufficient. Store the
NVIDIA key only in Nightshift and your runtime token only in local settings.

```powershell
python app.py
# Or use the CLI explicitly:
python team.py --ai --favourites Charizard --objective simple --profile demo2
```

In the GUI, select connected Zetaris data and Nightshift AI. Local planning is
still the default. Offline sample cannot send a model request.

## What to inspect

1. Original favourites and recalled avoidance reach the Planner and Critic.
2. The model requests an allowed tool and uses its results.
3. A Critic may require a real change or disclosure; a required change cannot be
   satisfied by a claim that nothing actually changed.
4. Each mutation gets a new team version. Old evidence cannot justify it.
5. All remaining supported cautions are acknowledged before final approval.
6. The final independent validator can still withhold output.
7. The report identifies the actual model, requests, tools, revisions and whether
   the AI changed or retained the local baseline.

Do not describe every live run as a critique-driven revision. If a sound baseline
is retained, the report says so. Tests proving the revision/refusal paths are
separate from the actions that a particular live model actually chose.

## Bounds and failure behaviour

The implementation permits at most eight model requests, twelve tools and two
critic revision rounds, with input/output limits and a time budget. No automatic
transport retry, provider switch or silently substituted local result is allowed.
Secrets, full prompts and hidden reasoning are not printed into public evidence.

See [AI reasoning](AI_REASONING.md) for the tool contracts, evidence policy,
security boundaries and mapping to the supplied Reasoning Architecture criteria.
See the root verification log for actual tests, live outcomes and remaining limits.
