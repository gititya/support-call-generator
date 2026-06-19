---
status: "in-progress"
current_phase: "Awaiting feedback from real-time_support_Updated repo on fixture compatibility and quality."
next_action: "On resume: ask user for REALTIME_FEEDBACK.md or verbal feedback from realtime repo review. Then act on schema alignment + quality fixes."
things_to_know:
  - "Used by real-time_support; do not reimplement inside the harness."
  - "feat/realtime-support branch adds: profiles.py, context.py, expected_state.py, tags.py, export_realtime.py, report.py"
  - "LLM prompt now includes context_events in expected JSON schema + generation rules."
  - "Anthropic provider: SCG_PROVIDER=anthropic dispatches to claude-sonnet-4-6. pip install -e '.[anthropic]' to enable."
  - "Streamlit UI: profile/provider selectors, intent tag badges, context events + expected state expanders."
  - "Export boundary: --format realtime_support produces fixtures with no ground_truth internals."
  - "18 tests (4 original + 14 new) all passing."
  - "HANDOFF_REALTIME_REVIEW.md has review instructions + feedback template for the realtime repo."
  - "Known schema diffs: generator context_events use reveals_final_cause (bool) + source + is_irrelevant + is_conflicting; realtime repo uses final_cause (string) + next_check + relevant. Alignment pending feedback."
  - "Signal (future): needs B2C packs (credit_reporting_complaints, fintech_app_reviews, support_tickets) + signal_eval_fixture export adapter. Architecture ready — CONTEXT_SOURCES, DIFFICULTY_PROFILES, export adapters are all dict-based. No structural work needed, just new entries + new export file."
---

# support-call-generator — SKILL.md

This file was created for the Builds dashboard. Replace this note with project-specific operating context after review.
