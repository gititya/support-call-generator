---
status: "in-progress"
current_phase: "Schema alignment complete. Exported fixtures pass realtime repo importer + validator. Ready for panel evaluation in realtime repo."
next_action: "Run exported fixtures through realtime support panel (test_experiment.py + report.py) in the realtime repo. Then evaluate expected-state quality under live panel conditions."
things_to_know:
  - "Used by real-time_support; do not reimplement inside the harness."
  - "feat/realtime-support branch adds: profiles.py, context.py, expected_state.py, tags.py, export_realtime.py, report.py"
  - "LLM prompt now includes context_events in expected JSON schema + generation rules."
  - "Anthropic provider: SCG_PROVIDER=anthropic dispatches to claude-sonnet-4-6. pip install -e '.[anthropic]' to enable."
  - "Streamlit UI: profile/provider selectors, intent tag badges, context events + expected state expanders."
  - "Export boundary: --format realtime_support produces fixtures with no ground_truth internals."
  - "18 tests (4 original + 14 new) all passing."
  - "HANDOFF_REALTIME_REVIEW.md has review instructions + feedback template for the realtime repo."
  - "Schema alignment done: export emits support_process_fixture.v1, is_irrelevant→relevant (inverted), final_cause string on revealing event, next_check per event, compact operational labels, expected_outcome + handoff_summary fields."
  - "Export produces both individual fixture files (no schema_version) and envelope JSON (with schema_version + inline cases) — both pass realtime repo importer."
  - "Validated: import_generated.py + validate_fixtures.py pass on 3 exported hard fixtures across all scenario types."
  - "Signal (future): needs B2C packs (credit_reporting_complaints, fintech_app_reviews, support_tickets) + signal_eval_fixture export adapter. Architecture ready — CONTEXT_SOURCES, DIFFICULTY_PROFILES, export adapters are all dict-based. No structural work needed, just new entries + new export file."
---

# support-call-generator — SKILL.md

This file was created for the Builds dashboard. Replace this note with project-specific operating context after review.
