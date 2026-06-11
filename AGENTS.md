# AGENTS.md - Support Call Generator

## Project Purpose

This repo generates synthetic B2B SaaS support-call transcripts for evaluating a separate Voice Support Intelligence Copilot.

It is not the copilot, a support bot, a voice agent, or a customer-facing product.

## Hard Boundaries

- Keep simulator and copilot logic separate.
- The copilot/main app may consume only transcript exports and `exports/latest/manifest.json`.
- Never expose `ground_truth`, `expected_timeline`, or `leakage_report` to transcript-only consumers.
- Generated data in `data/` and `exports/` is local output and should not be committed by default.

## Generation Doctrine

Every generated call should stress-test operational reasoning, not simple root-cause identification.

Calls should include:

- uncertainty and incomplete information
- misleading evidence and plausible false leads
- abandoned troubleshooting paths
- hypothesis reversals
- conflicting observations
- unreliable customer narration
- imperfect agent behavior
- late root-cause emergence

Prevent simulator leakage. Do not let transcripts reveal hidden truth through unusually specific observations, convenient clues, agent intuition without evidence, or perfect troubleshooting.

## Required Case Shape

Each case must include:

- `scenario_spec.json`
- `transcript.json`
- `transcript.md`
- `ground_truth.json`
- `expected_timeline.json`
- `leakage_report.json`
- `review.json`

Exports must include:

- `exports/latest/manifest.json`
- `exports/latest/transcripts/`
- `exports/latest/ground_truth/`
- `exports/latest/review_index.csv`

`manifest.json` must remain transcript-only.

## Verification

Run focused checks after source changes:

```bash
/Users/aditya/venvs/support/bin/python -B -c "import tempfile; from pathlib import Path; import tests.test_generator as t; t.test_generate_one_for_each_scenario(); t.test_batch_has_unique_ids_and_variation(); t.test_export_keeps_transcripts_separate_from_truth(Path(tempfile.mkdtemp())); t.test_review_status_persists(Path(tempfile.mkdtemp())); print('tests passed')"
PYTHONPYCACHEPREFIX=/private/tmp/scg_pycache /Users/aditya/venvs/support/bin/python -m compileall app.py support_call_generator tests
```

Before pushing, run a secret-pattern scan:

```bash
rg -n "sk-ant-|AIza|ghp_|xoxb-|sk_live|sk_test|Bearer |AWS_SECRET|PRIVATE_KEY|dangerouslyAllowBrowser|cors\(\{ origin: '\*' \}\)" .
```

## Keychain / API Use

The Streamlit UI reads the OpenAI key from `OPENAI_API_KEY` in the environment, then macOS Keychain service `OpenAI:voice` under account `aditya`.

Do not print API keys. Do not commit `.env` files. If the key is unavailable, generation should fail visibly rather than silently falling back to offline mode.
