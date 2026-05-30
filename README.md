# Support Call Generator

Scrappy synthetic B2B SaaS support-call generator for testing a Voice Support Intelligence Copilot.

The simulator is intentionally separate from the copilot. The copilot should only receive transcript exports. Hidden ground truth is exported separately for scoring.

Generated calls are designed to stress-test operational reasoning, not simple root-cause identification. Scenarios include misleading evidence, false leads, abandoned troubleshooting paths, hypothesis reversals, conflicting observations, and late root-cause reveals.
Each call also includes difficulty metadata, resolution type, leakage detection, operational timelines, and "why difficult" notes for manual review.

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
