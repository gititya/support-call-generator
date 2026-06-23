# Support Call Generator - Evolving

This documents talks about how the support call generator product, as it exists today, need to be evolved with more features to align and support different Customer Support Projects I'm building. 

These additional features were derived, verbatim, from the actual projects themselves on what would be high value for the respective projects to use or have support call generator be a dependency for. 

The projects that provided these feedback were: 
1. Signal - Turns support pain points & friction into evidence-grounded product insights. 
2. ReadlTime Support_Updated - An AI Copilot for human support agents to use whether the customer issue's root_cause is being interpreted correctly by the AI or not. 

Again, these are INCREMENTAL features. They are intended to be built above the current capability of the generator as modes or features. 

## Goal
1. Read through each of these feedback carefully and extract the requirement listed
2. Synthesize and build them out into features or modes into the current generator build that helps support the two products

## Feedback from the AI Copilot product
You’re right. I misunderstood the ask. You are not asking “how do we import generated calls into this repo next?” You are asking:

> What does `support-call-generator` need to become so it can be a reusable dependency for this project and other support-eval projects?

I read the repo. Here is the actual answer.

**What `support-call-generator` Is Today**

It is already a decent synthetic **B2B SaaS support-call generator**.

It can generate support calls with:

- transcript turns
- hidden ground truth
- expected hypothesis timeline
- difficulty metadata
- leakage checks
- review workflow
- transcript-only export boundary
- separate hidden ground-truth export

Current scenarios:

- `permissions_access`
- `onboarding_migration`
- `workspace_setup`

Current generation modes:

- offline deterministic fallback
- optional OpenAI generation

Current output shape:

- `transcript.json`
- `transcript.md`
- `ground_truth.json`
- `expected_timeline.json`
- `leakage_report.json`
- `review.json`

Current review UI:

- Streamlit app
- generate call
- accept/reject/draft
- view transcript
- inspect hidden truth
- inspect why the call is difficult

So it is **not just a toy transcript generator**. It already has the right philosophy: hidden truth, false leads, late reveal, leakage control, and review.

**What It Is Not Yet**

It is not yet a reusable support-eval dependency.

Right now it is more like:

> “A standalone B2B SaaS call generator with its own storage/export format.”

It needs to evolve into:

> “A support-case generation library that can produce transcripts, operational context, hidden truth, expected state timelines, and export adapters for different support-eval projects.”

That distinction matters.

**Main Gap For Our Current Project**

Our project needs this shape:

```text
transcript turn
+ product/support context event at the right turn
+ expected Live Support State after each turn
+ final cause only after mechanism evidence
```

But `support-call-generator` currently produces this shape:

```text
transcript
+ hidden ground truth
+ expected hypothesis timeline
```

That is close, but not enough.

The generator knows the hidden truth, false leads, late facts, expected hypothesis changes, etc. But it does **not yet emit explicit product/support context events** in the format our project needs.

For us, “context” is not just hidden truth. It is simulated operational evidence arriving during the case:

- admin panel state
- billing state
- email delivery state
- SCIM state
- role assignment state
- audit log event
- prior ticket note
- incident note
- deploy note

That needs to become first-class output.

**What It Needs To Evolve Into**

## 1. Add Product/Support Context Events

Today, delayed facts are mostly transcript facts or hidden truth notes.

It needs explicit context events like:

```json
{
  "after_turn": 11,
  "source": "admin_panel",
  "description": "Affected users are in Migrated-CSM, but the group has no workspace role.",
  "facts": [
    "group_membership:Migrated-CSM",
    "workspace_role_missing:Migrated-CSM"
  ],
  "resolved_unknowns": [
    "workspace_role_assignment"
  ],
  "ruled_out_branches": [
    "scim_sync_delay"
  ],
  "candidate_branches": [
    "missing_workspace_role_inheritance"
  ],
  "final_cause": "missing_workspace_role_inheritance"
}
```

This is the biggest missing piece.

Without this, our support-process project has to invent context after generation. That defeats the point of using the generator as a dependency.

## 2. Add Difficulty Levels That Mean More Than “easy/medium/hard”

It already has difficulty, but we need a more operational ladder:

### Simple

- one issue
- one customer correction max
- context arrives cleanly
- final cause has direct evidence
- few false leads

Useful for smoke tests.

### Hard

- 16-28 turns
- two or more plausible branches
- at least one wrong path strengthened then weakened
- late context reveal
- customer gives one misleading but true detail
- agent may be average/confused

Useful for evaluating Live Support State.

### Harder / Adversarial

- multiple issue surfaces
- irrelevant context from another account
- conflicting context
- delayed correction
- partial resolution or handoff
- final cause may remain probable, not confirmed
- customer pressure/escalation
- agent asks at least one bad question

Useful for deciding if the assistant is genuinely robust.

So the generator should expose difficulty as a structured “case complexity profile,” not just a label.

## 3. Add B2C Availability

Today the repo is B2B SaaS-only. That fits our current project, but not “other support projects.”

Add domain families:

```text
B2B SaaS
B2C Account / Login
B2C Billing / Subscription
B2C Delivery / Order
B2C Device / App Troubleshooting
Marketplace / Two-sided support
Healthcare / Financial support simulation, with safety constraints
```

B2C cases need different context sources:

- order status
- refund state
- payment attempt
- device/app version
- account lock / MFA
- delivery carrier events
- subscription entitlement
- customer identity verification status

B2C also needs different language. B2B cases are admin/workspace/integration-heavy. B2C cases are more emotional, account-specific, and policy-heavy.

## 4. Add Scenario Packs

Right now scenarios are hardcoded in `scenarios.py`.

To become reusable, it should support scenario packs:

```text
support_call_generator/packs/b2b_saas/
support_call_generator/packs/b2c_account/
support_call_generator/packs/b2c_billing/
support_call_generator/packs/marketplace/
```

Each pack should define:

- scenario types
- root-cause catalog
- context sources
- customer personas
- agent behaviors
- allowed resolution types
- known bad branches
- expected timeline rules

This lets this repo use a B2B SaaS pack, while another project could use B2C billing without forking the generator.

## 5. Add Export Adapters

Today export gives transcript-only and ground-truth files.

Good boundary, but for reuse it needs adapters:

```bash
support-call-generator export --format transcript
support-call-generator export --format support-process-fixtures
support-call-generator export --format hypothesis-timeline
support-call-generator export --format jsonl
support-call-generator export --format eval-dataset
```

For our project specifically, it needs:

```bash
support-call-generator export --format realtime-support-fixtures
```

That adapter should output fixtures compatible with this repo:

```json
{
  "case_id": "...",
  "title": "...",
  "scenario": "...",
  "transcript_turns": [...],
  "context_events": [...],
  "expected_by_turn": [...],
  "final_cause": "..."
}
```

Then our project can consume generated cases directly.

## 6. Add Expected Live Support State

Current `expected_timeline` tracks hypotheses:

```json
{
  "turn": 8,
  "hypothesis": "...",
  "state": "discard",
  "confidence": 0.15,
  "evidence": [...]
}
```

Our project needs expected support state:

```json
{
  "after_turn": 8,
  "facts": [],
  "unknowns": [],
  "candidate_branches": [],
  "ruled_out_branches": [],
  "next_check_contains": [],
  "final_cause_allowed": false
}
```

The generator does not need to use exactly our labels internally, but it needs to export this shape.

This is what turns it from “call generator” into “support-process eval generator.”

## 7. Add Context Leakage Controls

It already has transcript leakage checks. Good.

But once context events exist, it also needs context leakage checks:

- context must not include final cause too early
- irrelevant context must be marked irrelevant
- context facts must not contradict hidden truth unless intentionally marked conflicting
- final-cause evidence must appear only at the intended reveal turn
- transcript-only export must not include context unless the consuming project asks for it

This is crucial because our project’s whole point is timing.

## 8. Add Case Intent Tags

Right now it has scenario and difficulty. It should also tag what capability each case tests.

Examples:

```json
"tests": [
  "premature_final_cause",
  "wrong_path_recovery",
  "irrelevant_context_filtering",
  "customer_correction",
  "late_evidence_reveal"
]
```

This helps us build targeted eval sets:

- 10 correction cases
- 10 irrelevant-context cases
- 10 late-reveal cases
- 10 unresolved/handoff cases

That is better than just “generate 50.”

## 9. Add Simple > Hard > Harder Case Presets

The CLI should support:

```bash
support-call-generator generate-batch --profile simple --count 20
support-call-generator generate-batch --profile hard --count 20
support-call-generator generate-batch --profile harder --count 20
```

Each profile should control:

- transcript length
- number of hypotheses
- number of context events
- number of irrelevant/context-conflict events
- number of customer corrections
- agent quality
- resolution type distribution
- whether final cause is confirmed or only probable

This is exactly what we need next.

## 10. Add A Stable Python API

Right now it has `generate_call(...)`, but the package is still oriented around CLI/storage.

For dependency reuse, expose a small stable API:

```python
from support_call_generator import generate_case, export_case

case = generate_case(
    domain="b2b_saas",
    scenario="permissions_access",
    profile="hard",
    output_schema="support_process",
    seed=123,
)
```

And return a typed-ish dict with guaranteed keys.

This project should not need to know internal files like `scenarios.py`.

## 11. Add Versioned Schemas

Currently there is no strong schema version for case format except export manifest `schema_version`.

It needs:

```json
{
  "schema_version": "support-call-generator.case.v2",
  "transcript_schema_version": "...",
  "ground_truth_schema_version": "...",
  "context_schema_version": "...",
  "export_format": "realtime_support_fixture.v1"
}
```

Without this, downstream projects will break when the generator evolves.

## 12. Add Generated Dataset Quality Reports

The generator should report dataset composition:

- domain mix
- scenario mix
- difficulty mix
- resolution type mix
- root-cause diversity
- average turn count
- leakage pass/warning/fail
- capability tags covered

This matters when this repo asks: “Did we actually test hard things?”

A batch should output something like:

```text
50 cases generated
- 20 hard
- 20 harder
- 10 simple
- 14 correction cases
- 11 irrelevant context cases
- 8 unresolved/handoff cases
- 0 leakage failures
```

## How This Maps To Our Current Project

Our current project needs `support-call-generator` to provide:

1. Longer generated B2B support transcripts.
2. Product/support context events at specific turns.
3. Expected Live Support State after each turn.
4. Final-cause timing constraints.
5. Fixture export in this repo’s format.
6. Difficulty profiles.
7. Capability tags for targeted test batches.

Then this repo can stop hand-authoring all fixtures.

The flow should become:

```text
support-call-generator
  generate hard B2B case
  export realtime-support fixture
        ↓
real-time_support_Updated
  validate fixture
  run process/predictive/real model
  render support panel report
```

## What To Build First In `support-call-generator`

Do not start with B2C. Start with making it reusable for this repo.

Best first milestone:

### Milestone 1: `support_process` Export Adapter

Add:

```bash
support-call-generator export-reviewed --format support_process
```

or:

```bash
support-call-generator export-support-process
```

It should export accepted generated cases into our fixture format:

- `transcript_turns`
- `context_events`
- `expected_by_turn`
- `final_cause`

This forces the generator to become useful as a dependency.

### Milestone 2: First-Class Context Events

Add `context_events` to generated cases.

Do this before B2C.

Context event sources:

- `admin_panel`
- `billing_system`
- `identity_provider`
- `email_delivery`
- `audit_log`
- `migration_log`
- `incident_note`
- `prior_ticket`

### Milestone 3: Difficulty Profiles

Add profiles:

- `simple`
- `hard`
- `harder`

Do not just rename current difficulty. Make profiles control structure.

### Milestone 4: B2C Packs

Only after B2B support-process export works.

Add:

- `b2c_account_access`
- `b2c_subscription_billing`
- `b2c_order_delivery`
- `b2c_app_troubleshooting`

Each with its own context sources and support policies.

## What Should Not Be Done Yet

Do not make `support-call-generator` a polished SaaS app.

Do not make the Streamlit UI the main integration surface.

Do not make real integrations.

Do not generate voice/audio.

Do not collapse hidden ground truth into transcript exports.

Do not optimize for “realistic conversation” at the expense of diagnostic structure.

## Bottom Line

`support-call-generator` is already philosophically aligned with this project. It has hidden truth, false leads, late reveals, difficulty metadata, review, and export separation.

But to support this project as a reusable dependency, it needs to evolve from:

> transcript + hidden root-cause generator

into:

> support-case generator with transcript, timed operational context, expected live support state, difficulty profiles, domain packs, and export adapters.



---



## Feedback from Signal
Signal does not need all of those features inside Signal. Signal benefits if support-call-generator evolves into a broader synthetic customer-evidence generator that can produce raw input data different support/product-intelligence tools can consume.
So the better framing is:
support-call-generator should stay its own generator product, but add export modes / case packs for different downstream products.
For example:
Current use case: B2B SaaS support-call transcripts for a voice support copilot.
Signal use case: B2C complaint/review/ticket-style evidence with hidden PM-signal ground truth.
Support product X: maybe agent coaching calls with expected coaching feedback.
Support product Y: maybe escalation prediction cases with expected risk labels.
So Signal doesn’t need the generator to become Signal-specific. It needs the generator to support a Signal-compatible data mode.
The clean architecture would be:
support-call-generator
  core/
    scenario generation
    difficulty controls
    hidden truth separation
    leakage checks
    review UI
    export system

  packs/
    b2b_saas_calls/
    credit_reporting_complaints/
    fintech_app_reviews/
    support_tickets/
    escalation_cases/

  exports/
    transcript_only/
    cfpb_csv/
    signal_eval_fixture/
    coaching_eval_fixture/
For Signal specifically, the useful added feature is not “more call generation.” It is:
generate messy customer evidence that looks like CFPB complaints, app reviews, tickets, or call summaries, with hidden truth for the evidence bucket, PM-facing signal, signal type, and rationale.

That lets Signal prove it can mine raw customer feedback into product signals.
So I would not turn the whole repo into a Signal tool. I’d evolve it into a multi-product synthetic support data lab, where Signal is one consumer. The first Signal-facing feature should be a credit_reporting_complaints pack plus a signal_eval_fixture export.