# Realtime Support Fixture Review - Feedback

**Reviewed by:** Codex
**Date:** 2026-06-19
**Fixtures reviewed:** generated batch of 3 hard offline realtime-support exports, plus one inspected fixture

## Verdict

[ ] Ready to use as-is
[x] Needs schema alignment
[x] Needs quality improvements
[ ] Needs both after another review pass

Short version: the branch is directionally right, and the generator's own tests pass, but the realtime export is not yet good enough to commit as ready for `real-time_support_Updated`. It fails the current importer before fixture validation starts, and the inspected expected state is too generic to be useful as a Live Support State answer key.

## Tests run

From `support-call-generator`:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/scg_pycache /Users/aditya/venvs/support/bin/python -m pytest tests/ -v
```

Result: failed because `pytest` is not installed in `/Users/aditya/venvs/support`.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/scg_pycache /Users/aditya/venvs/support/bin/python -m compileall app.py support_call_generator tests
```

Result: passed.

Direct Python test-function run:

```text
18 direct tests passed
```

Security scan:

```bash
rg -n "sk-ant-|AIza|ghp_|xoxb-|sk_live|sk_test|Bearer |AWS_SECRET|PRIVATE_KEY|dangerouslyAllowBrowser|cors\(\{ origin: '\*' \}\)" .
```

Result: only matched the literal scan command in `AGENTS.md`; no secret finding.

Compatibility test against `real-time_support_Updated` importer:

```text
IMPORT_FAIL call_6e98291e82.json Unsupported schema_version: support_call_generator.realtime_support.v1
IMPORT_FAIL call_c677558038.json Unsupported schema_version: support_call_generator.realtime_support.v1
IMPORT_FAIL call_eaf9904469.json Unsupported schema_version: support_call_generator.realtime_support.v1
failures 3
```

## Schema alignment needed

### Top-level

- [x] Change or wrap `schema_version` to `support_process_fixture.v1`, or update the realtime repo importer to explicitly accept `support_call_generator.realtime_support.v1`.
- [x] Keep `difficulty_profile`, `resolution_type`, and `intent_tags`; they are useful harmless metadata.
- [x] Add `expected_outcome` when the generator creates `handoff`, `probable_cause`, or unresolved cases.
- [x] Add `handoff_summary` for unresolved/handoff cases.

### Context events

- [x] Add `final_cause` string field on the event that reveals the mechanism. The realtime repo currently expects this, not only `reveals_final_cause: true`.
- [x] Add `next_check` string field. The support panel needs a clear next useful check after context arrives.
- [x] Rename `is_irrelevant` to `relevant` with inverted boolean, or export both for now.
- [x] Keep `source`; it is useful for inspection.
- [x] Keep `is_conflicting`; it is useful metadata, but the realtime repo will ignore it unless promoted later.
- [x] Consider adding `unknowns` when context creates a new open investigation item.

### Expected state

- [x] Keep `final_cause_allowed`; it is useful metadata.
- [x] But also ensure the regular expected-state fields use the same operational labels as the realtime repo: compact labels like `auth:works`, `workspace_role:present`, `billing_refresh:pending`, not broad prose.

## Quality feedback

### Transcript quality

- Realistic enough? [x] partly
- Operationally messy enough? [x] partly
- Turn count appropriate? [x] yes
- Notes: The generator is producing longer cases with profiles, which is good. It should still be reviewed for whether each transcript turn creates support-relevant state changes rather than filler.

### Context events

- Timing makes sense? [x] partly
- Descriptions specific enough? [x] partly
- Irrelevant events useful as noise? [x] yes
- Conflicting events useful? [x] partly
- Notes: The irrelevant event inspected was useful noise: `prior_ticket:password_policy`. The issue is not the idea; it is export compatibility and state-label quality.

### Expected state

- Facts accumulate sensibly? [ ] not enough evidence
- Unknowns resolve at right pace? [ ] not enough evidence
- Branch tracking useful? [ ] no
- Notes: The inspected expected state had generic values like `customer reports a access issue`, `browser cache`, `license limit`, and `the_access_failure_is_caused`. That is not yet precise enough for the realtime repo, whose evaluator expects operational state like facts, unknowns, candidate branches, ruled-out branches, and next checks that map to support mechanisms.

### Difficulty profiles

- Simple feels like a smoke test? [ ] not reviewed
- Hard stresses reasoning? [x] structurally yes
- Harder is genuinely adversarial? [ ] not reviewed
- Notes: The structural controls are present and tests cover them, but difficulty quality should be judged after schema alignment lets generated cases run through the realtime support panel.

## Specific issues

1. Current realtime export fails importer immediately due schema version mismatch.
2. Context final-cause reveal is represented as `reveals_final_cause: true`, but the realtime repo needs the actual `final_cause` string on the revealing context event.
3. Context events do not export `next_check`, which is central to the support-process prototype.
4. Irrelevant context uses `is_irrelevant`; realtime fixtures use `relevant: false`.
5. Expected state labels are too prose-like/generic to serve as a high-signal Live Support State answer key.
6. `pytest` is not available in the configured support venv, so the official test command in the handoff could not be used as written. Direct test-function execution passed.

## Suggestions

Do one focused pass before committing this as ready:

1. Add a realtime export adapter mode that emits exactly `support_process_fixture.v1`.
2. Translate generator context fields into realtime fixture fields:
   - `is_irrelevant: true` -> `relevant: false`
   - `reveals_final_cause: true` + case final cause -> event `final_cause`
   - derive event `next_check`
3. Normalize expected-state labels into compact operational labels.
4. Export one small accepted batch, then run:

```bash
cd /Users/aditya/Documents/Projects/real-time_support_Updated
python3 prototype/import_generated.py /path/to/exported/generated_fixture.json
python3 validate_fixtures.py
python3 -m unittest test_experiment.py
python3 prototype/report.py
```

After those pass, the generator output is ready to test inside the realtime repo.

---

## Re-review After Schema Alignment Changes

**Date:** 2026-06-19

Verdict: closer, but not fully working through the current realtime repo workflow.

What now passes:

- `support_call_generator/export_realtime.py` now exports `schema_version: support_process_fixture.v1`.
- Context events now include `relevant`.
- Context events now include `next_check`.
- Revealing context events now include a `final_cause` string.
- Fixtures now include `expected_outcome`.
- Handoff/escalated fixtures include `handoff_summary` and leave `final_cause` empty.
- Generator compile check passed.
- Direct execution of 22 test functions passed.
- Generator CLI smoke path passed:
  - `generate-batch --count 3 --offline --profile hard`
  - `export-reviewed --format realtime_support --status all`

What still fails:

```text
python3 prototype/import_generated.py /private/tmp/scg_cli_exports/realtime_support/call_8aa96ea19d.json --staging-dir /private/tmp/scg_import_staging
Generated fixture envelope needs a non-empty cases list
```

Cause: each exported realtime fixture is now a single fixture object with `schema_version`, but the realtime repo importer currently treats any file with `schema_version` as an envelope and expects a non-empty `cases` list.

Important nuance: when the same exported fixtures are wrapped manually in this envelope, the realtime repo importer accepts them:

```json
{
  "schema_version": "support_process_fixture.v1",
  "cases": [ ...fixtures... ]
}
```

Wrapped-envelope compatibility result:

```text
ENVELOPE_IMPORT_OK 3
```

Remaining quality concern:

Expected-state labels are improved, but still somewhat coarse. Example inspected labels included:

- `customer:reports`
- `access:failure`
- `browser:cache`
- `license:limit`
- `expired:invitation`

This is good enough for import/staging smoke tests after the file-shape issue is fixed, but not yet as strong as the hand-authored fixtures for final evaluator quality.

Recommended next fix:

Pick one of these:

1. Export a batch envelope file alongside individual fixture files, for example `realtime_support_cases.json`.
2. Or update `real-time_support_Updated/prototype/import_generated.py` so a single fixture object with `schema_version: support_process_fixture.v1` is accepted directly.

After that, rerun direct import on each exported fixture file.

---

## Re-review After Envelope And Bare-Fixture Fix

**Date:** 2026-06-19

Verdict: schema/import compatibility now works. Full live-panel evaluator quality does not pass yet.

What now passes:

- Generator compile check passed.
- Direct execution of 22 generator test functions passed.
- Generator CLI smoke path passed:
  - `generate-batch --count 3 --offline --profile hard`
  - `export-reviewed --format realtime_support --status all`
- Exported envelope exists at `exports/realtime_support_envelope.json`.
- Envelope has `schema_version: support_process_fixture.v1` and inline `cases`.
- Envelope import into `real-time_support_Updated/prototype/import_generated.py` passed.
- Individual fixture import into `real-time_support_Updated/prototype/import_generated.py` passed.
- Staged generated fixtures pass `validate_fixture()`.

Cross-repo import result:

```text
Wrote /private/tmp/scg_realtime_check_staging/call_10953f417f.json
Wrote /private/tmp/scg_realtime_check_staging/call_78c6073828.json
Wrote /private/tmp/scg_realtime_check_staging/call_e551293aba.json
Wrote /private/tmp/scg_realtime_check_single/call_10953f417f.json
```

Validator result on staged generated fixtures:

```text
call_10953f417f.json ok
call_78c6073828.json ok
call_e551293aba.json ok
staged generated fixtures validate
```

What still fails:

When the generated fixtures are temporarily copied into `real-time_support_Updated/fixtures/`, the full evaluator fails:

```text
Validated 13 fixtures
FAIL: test_deterministic_reference_passes
AssertionError: 320 != 504

FAIL: test_process_mock_passes_without_premature_final_cause
AssertionError: 320 != 504
```

Why this matters:

This is no longer an import/schema problem. The generated fixtures can be staged. The issue is that the generated expected state does not match the current realtime repo's deterministic/process updater behavior.

Example mismatch pattern:

```text
CASE call_10953f417f 34 / 96
unknowns missing= ['duplicate:merge', 'migration:problem', 'partial:import', 'timezone:conversion'] actual= []
candidate_branches missing= ['customer:reports'] actual= []
next_check missing= ['investigate_partial_import', 'verify_customer_reports_a_migration_issue'] actual=
```

Similar failures appear for access and workspace setup generated cases.

Interpretation:

- The generator is now ready for staging/import smoke tests.
- It is not yet ready to promote generated cases into `real-time_support_Updated/fixtures/` as source-of-truth eval cases.
- The remaining work is expected-state alignment, not file format.

Recommended next fix:

Choose one of these paths:

1. Teach `real-time_support_Updated` to evaluate generated cases with a generated-case adapter/mode instead of the hand-authored deterministic rules.
2. Or make generator expected states use the exact labels and transition behavior that `run.py` and `mock_llm.py` currently produce.

For this phase, option 1 is probably cleaner: generated fixtures should stage under `outputs/generated_fixture_staging/`, then be reviewed in the prototype report without being treated as accepted root fixtures until their expected states are calibrated.

---

## Re-review After Expected-State Recompute Change

**Date:** 2026-06-19

Verdict: much closer. Import and validation work; generated fixtures are nearly aligned with the deterministic reference path, but not yet with the process mock path.

What passed:

- Generator compile check passed.
- Direct execution of 22 generator test functions passed.
- Security scan had no real secret finding; only matched literal scan commands in docs.
- Fresh CLI generation/export passed:
  - `generate-batch --count 3 --offline --profile hard`
  - `export-reviewed --format realtime_support --status all`
- Envelope import passed.
- Individual fixture import passed.
- Staged generated fixtures passed `validate_fixture()`.
- Prototype report can render a generated fixture.

Fresh generated cases:

```text
call_c5ba5824fc
call_f287812290
call_f9cf1c25e8
```

Full evaluator result when temporarily copied into `real-time_support_Updated/fixtures/`:

```text
Validated 13 fixtures
test_deterministic_reference_passes: 502 != 504
test_process_mock_passes_without_premature_final_cause: 462 != 504
```

This is a major improvement over the previous `320 != 504` result.

Mismatch pattern:

- Deterministic path is almost clean: only 2 next-check misses across the generated batch.
- Process mock still misses many generated-case `next_check` expectations.
- The process mock was built for the small hand-authored label set, so it often leaves `next_check` empty or falls back to billing/migration/invite checks when the generated context uses broader domains.

Examples:

```text
CASE call_c5ba5824fc deterministic 94 / 96
next_check missing= ['verify', 'ruling']

CASE call_f287812290 deterministic 96 / 96
CASE call_f9cf1c25e8 deterministic 96 / 96

CASE call_c5ba5824fc process_mock 81 / 96
CASE call_f287812290 process_mock 83 / 96
CASE call_f9cf1c25e8 process_mock 82 / 96
```

Interpretation:

- Generated fixtures are now good enough for staging/import/report smoke tests.
- They are not yet good enough to be promoted into the root `fixtures/` set if the requirement is that `test_experiment.py` stays fully green.
- The remaining gap is mostly `next_check` alignment and generated-domain mock behavior, not schema.

Recommended next fix:

Either:

1. Add a generated-fixture evaluation mode in `real-time_support_Updated` that scores imported generated cases separately from the hand-authored source-of-truth fixtures.
2. Or export generated `next_check_contains` values that are looser and match what the current process mock can actually produce.
3. Or extend `mock_llm.py` / `run.py` to understand the generated domains, but that expands the realtime repo beyond the current small hand-authored harness.

Best next move: use option 1. Keep generated cases staged and report-renderable first, then calibrate the generated expected states before promotion.
