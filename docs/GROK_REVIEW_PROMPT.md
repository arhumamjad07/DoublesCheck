# Genuine Grok / SpaceXAI evidence task — not yet performed

Use Grok Build **or the exact tool the organisers confirm**. This file is a
prepared prompt, not proof that any SpaceXAI agent has run. Codex implemented
the current upgrade. Do not describe its work as another tool's work.

## Paste this prompt into the confirmed tool

> Review DoublesCheck's `zetaris_schema.py`, `zetaris_partners.py` and
> `test_zetaris_partners.py` on a separate review branch. The submission baseline
> must remain untouched. Review table grains, uniqueness, SQL joins and the
> meaning of summed association weights across multiple favourites. Add a
> meaningful local integration test proving that reversing the same two locked
> favourites leaves the SQL candidate set and association weights unchanged,
> with avoidance still applied and deterministic name tie-breaking preserved.
> Execute the actual SQL using the existing relational test fixture. Explain
> any findings and the limits of SQLite versus the live Zetaris/Spark check.
> Make only the bounded test/review change; do not ingest new data, change
> credentials, contact paid models, replace the builder, or alter saved model
> evidence. Run the new test and existing Evidence Lens tests. Report your diff,
> command output and any unresolved concern. Never manufacture a passing result.

## Record genuine evidence

- Confirm the exact tool's name and challenge eligibility with organisers.
- Save your original prompt and record the tool UI identifying the tool.
- Record actual agent activity: file reads, proposed edits, execution and results.
- Save the resulting Git diff and commit; preserve failures/fixes if any occurred.
- Record the test's actual query inputs and resulting partner rows/weights.
- Record real passing test output; label fixture SQL versus live Zetaris honestly.
- Run the full app suite before considering a merge. Keep this work separate
  if the submission freeze or reliability gate would be threatened.
- Never show credentials, private environment values or personal app history.

Do not create a synthetic agent activity log to fill a missing challenge requirement.
