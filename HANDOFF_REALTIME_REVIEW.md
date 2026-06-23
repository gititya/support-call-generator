# Handoff: Review support-call-generator output in real-time_support_Updated

**From:** `support-call-generator` repo (branch `feat/realtime-support`, PR #1)
**To:** `real-time_support_Updated` repo
**Purpose:** Verify that generated fixtures are compatible with and useful for the realtime support copilot before merging.

---

## What was built

The support-call-generator now produces synthetic B2B support cases with:

1. **Difficulty profiles** (`--profile simple|hard|harder`) — structural controls over turn count, hypothesis count, noise, agent quality, resolution distribution
2. **Context events** — timed operational evidence (admin_panel, audit_log, billing_system, etc.) that arrives between transcript turns
3. **Expected state per turn** — deterministic answer key: facts, unknowns, candidate/ruled-out branches per turn
4. **Intent tags** — what reasoning challenge each case tests (wrong_path_recovery, late_evidence_reveal, etc.)
5. **Realtime support export** (`--format realtime_support`) — clean fixtures excluding generator internals
6. **LLM prompt** — now asks the LLM to generate context events with timing/source/final-cause rules
7. **Anthropic provider** — `SCG_PROVIDER=anthropic` uses Claude Sonnet 4.6

## What the spec asked for

The original spec (from `Evolving support call_generator.md`) requested these features for the copilot:

| Spec requirement | Status | Notes |
|---|---|---|
| Context events as first-class output | Built | Timed, sourced, with irrelevant/conflicting noise |
| Expected live support state per turn | Built | Deterministic accumulation of facts/unknowns/branches |
| Difficulty profiles (simple/hard/harder) | Built | Structural controls, not just labels |
| Realtime support export adapter | Built | `--format realtime_support` |
| Context leakage controls | Built | Final cause timing, early reveal detection |
| Case intent tags | Built | Derived from case structure |
| Quality reports | Built | Batch composition reports |

---

## Schema differences to check

The generator's export shape differs from the hand-authored fixtures in `real-time_support_Updated/fixtures/`. Here's what to verify:

### Top-level keys

| Key | Hand-authored fixtures | Generator export | Action needed |
|---|---|---|---|
| `case_id` | present | present | compatible |
| `title` | present | present | compatible |
| `scenario` | present | present | compatible |
| `transcript_turns` | present | present | compatible |
| `context_events` | present | present | **check shape below** |
| `expected_by_turn` | present | present | **check shape below** |
| `final_cause` | present | present | compatible |
| `expected_outcome` | some fixtures | not present | decide if needed |
| `handoff_summary` | some fixtures | not present | decide if needed |
| `schema_version` | not present | present | harmless extra |
| `difficulty_profile` | not present | present | harmless extra |
| `resolution_type` | not present | present | harmless extra |
| `intent_tags` | not present | present | harmless extra |

### Context event shape

| Field | Hand-authored | Generator | Notes |
|---|---|---|---|
| `after_turn` | present | present | same |
| `description` | present | present | same |
| `facts` | present | present | same key:value format |
| `resolved_unknowns` | present | present | same |
| `ruled_out_branches` | present | present | same |
| `candidate_branches` | present | present | same |
| `final_cause` | present (string) | **not present** | Generator uses `reveals_final_cause` (bool) instead |
| `next_check` | present (string) | **not present** | Generator doesn't produce this |
| `unknowns` | some fixtures | **not present** | Generator tracks unknowns in expected_state instead |
| `relevant` | some fixtures | **not present** | Generator uses `is_irrelevant` (bool) instead |
| `source` | not present | present | New field: admin_panel, audit_log, etc. |
| `is_irrelevant` | not present | present | New field |
| `is_conflicting` | not present | present | New field |
| `reveals_final_cause` | not present | present | New field (replaces `final_cause` string on context events) |

### Expected state shape

| Field | Hand-authored | Generator | Notes |
|---|---|---|---|
| `after_turn` | present | present | same |
| `facts` | present | present | same |
| `unknowns` | present | present | same |
| `candidate_branches` | present | present | same |
| `ruled_out_branches` | present | present | same |
| `next_check_contains` | present | present | same |
| `final_cause_allowed` | not present | present | New field — when can the copilot declare root cause? |

---

## How to check

### 1. Generate test fixtures

In the `support-call-generator` repo:

```bash
git checkout feat/realtime-support

# Generate a batch with profiles
python -m support_call_generator generate-batch --count 6 --offline --profile hard

# Or generate individual cases
python -m support_call_generator generate-one --scenario permissions_access --offline --profile hard
python -m support_call_generator generate-one --scenario onboarding_migration --offline --profile harder
python -m support_call_generator generate-one --scenario workspace_setup --offline --profile simple
```

### 2. Review in Streamlit UI (optional)

```bash
streamlit run app.py
```

Accept cases you want to export, then:

```bash
python -m support_call_generator export-reviewed --format realtime_support
```

Exported fixtures land in `exports/realtime_support/`.

### 3. Copy fixtures to realtime support repo

```bash
cp exports/realtime_support/*.json ~/Documents/Projects/real-time_support_Updated/fixtures/
```

### 4. Run validate_fixtures.py

```bash
cd ~/Documents/Projects/real-time_support_Updated
python validate_fixtures.py
```

**Expected result:** Validation will likely fail because of schema differences (see table above). This is the key question: **does the generator's export shape need to change, or does the realtime repo's validator need to evolve?**

### 5. Run the actual support process pipeline

```bash
python run.py
# or
python run_all.py
```

Check if the process/predictive/real models can consume the generated fixtures. Key things to verify:

- Do context events arrive at sensible turns?
- Is the expected state per turn reasonable for the scenario?
- Does the final cause reveal timing make sense?
- Are irrelevant/conflicting events actually useful noise, or just confusing?
- Are the generated transcript turns long enough and messy enough?

### 6. Compare generated vs hand-authored

Pick one generated fixture and one hand-authored fixture for the same scenario type. Compare:

- **Transcript quality:** Is the generated version as realistic and operationally messy?
- **Context event richness:** Are generated events as specific and domain-aware?
- **Expected state accuracy:** Does the per-turn state make sense given the transcript and context?
- **Difficulty calibration:** Does "hard" feel harder than "simple"?

---

## Feedback mechanism

After review, create or update this file in the **support-call-generator** repo:

**File:** `REALTIME_FEEDBACK.md`

Use this template:

```markdown
# Realtime Support Fixture Review — Feedback

**Reviewed by:** [name]
**Date:** [date]
**Fixtures reviewed:** [list case_ids or "batch of N"]

## Verdict
[ ] Ready to use as-is
[ ] Needs schema alignment (see below)
[ ] Needs quality improvements (see below)
[ ] Needs both

## Schema alignment needed

### Context events
- [ ] Add `final_cause` string field (currently only `reveals_final_cause` bool)
- [ ] Add `next_check` string field
- [ ] Rename `is_irrelevant` → `relevant` (inverted bool)
- [ ] Remove/keep `source` field?
- [ ] Remove/keep `is_conflicting` field?
- [ ] Other: ___

### Expected state
- [ ] Remove/keep `final_cause_allowed` field?
- [ ] Other: ___

### Top-level
- [ ] Add `expected_outcome` field?
- [ ] Add `handoff_summary` field?
- [ ] Remove/keep `schema_version`, `difficulty_profile`, `resolution_type`, `intent_tags`?

## Quality feedback

### Transcript quality
- Realistic enough? [ ] yes [ ] no
- Operationally messy enough? [ ] yes [ ] no
- Turn count appropriate? [ ] yes [ ] no
- Notes: ___

### Context events
- Timing makes sense? [ ] yes [ ] no
- Descriptions specific enough? [ ] yes [ ] no
- Irrelevant events useful as noise? [ ] yes [ ] no
- Conflicting events useful? [ ] yes [ ] no
- Notes: ___

### Expected state
- Facts accumulate sensibly? [ ] yes [ ] no
- Unknowns resolve at right pace? [ ] yes [ ] no
- Branch tracking useful? [ ] yes [ ] no
- Notes: ___

### Difficulty profiles
- Simple feels like a smoke test? [ ] yes [ ] no
- Hard stresses reasoning? [ ] yes [ ] no
- Harder is genuinely adversarial? [ ] yes [ ] no
- Notes: ___

## Specific issues
[List any specific problems with specific case_ids]

## Suggestions
[Anything else]
```

When this file exists in the support-call-generator repo, the next session will pick it up and act on the feedback.

---

## Quick reference: generator commands

```bash
# Generate
python -m support_call_generator generate-one --scenario permissions_access --offline --profile hard
python -m support_call_generator generate-batch --count 20 --offline --profile hard

# Review UI
streamlit run app.py

# Export accepted cases as realtime support fixtures
python -m support_call_generator export-reviewed --format realtime_support

# Run tests
python -m pytest tests/ -v
```
