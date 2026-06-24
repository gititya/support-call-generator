# Support Call Generator

Scrappy synthetic B2B SaaS support-call generator for testing a Voice Support Intelligence Copilot.

The simulator is intentionally separate from the copilot. The copilot should only receive transcript exports. Hidden ground truth is exported separately for scoring.

Generated calls are designed to stress-test operational reasoning, not simple root-cause identification. Scenarios include misleading evidence, false leads, abandoned troubleshooting paths, hypothesis reversals, conflicting observations, and late root-cause reveals.
Each call also includes difficulty metadata, resolution type, leakage detection, operational timelines, and "why difficult" notes for manual review.

## Who this is for (it's a dependency, not a product)

Support Call Generator is infrastructure for two downstream eval projects — not a standalone product:

- **`real-time_support_Updated`** (B2B support-process eval) — consumes `support_process_fixture.v1` via `export_realtime.py`: transcript turns, timed context events, expected per-turn support state, and final-cause timing.
- **Handoff Quality Gate** (B2C) — consumes `b2c_subscription_billing` disputed-charge cases, each carrying an `expected_handoff` answer key (the required, grounded fields a good AI→human handoff must contain).

One proven pipeline is the point, not breadth of packs:

```
generate b2c_subscription_billing case
  -> ground_truth.expected_handoff (answer key)
  -> export-realtime -> support_process_fixture.v1 (+ expected_handoff)
        |
        v
  consumed by real-time_support_Updated / Handoff Quality Gate
```

**What it is not:** not used by Signal (Signal uses real CFPB data — synthetic complaints would undermine its credibility); not a multi-domain "synthetic support data lab"; not a customer-facing or responding agent. The `Evolving support call_generator.md` doc is a reference wishlist, not a build plan — build only what a real consumer asks for.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[ui,llm]"
cp .env.example .env
```

Set `OPENAI_API_KEY` in your shell or `.env` if you want LLM-assisted generation. Without an API key, the generator uses an offline deterministic fallback so the CLI and tests still work.

## CLI

```bash
python -m support_call_generator generate-one --scenario permissions_access
python -m support_call_generator generate-batch --count 50
python -m support_call_generator export-reviewed
```

Scenarios:

- `permissions_access`
- `onboarding_migration`
- `workspace_setup`

## Review UI

```bash
streamlit run app.py
```

Use the UI to read transcripts, inspect hidden truth, accept, reject, and regenerate cases.

## Export Boundary

`export-reviewed` creates:

- `exports/transcripts/`: transcript-only JSON and Markdown for copilot input.
- `exports/ground_truth/`: hidden truth and expected timelines for scoring.
- `exports/review_index.csv`: case-level review metadata.
- `exports/manifest.json`: transcript-only manifest for the main app to fetch generated calls.

Do not give the copilot anything from `exports/ground_truth/`.

For a stable import boundary, export to `exports/latest`:

```bash
python -m support_call_generator export-reviewed --status all --export-dir exports/latest
```

The main app should read `exports/latest/manifest.json`, then load only the transcript paths listed there.
