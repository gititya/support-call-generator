---
status: "in-progress"
current_phase: "Realtime support evolution — context events, expected state, difficulty profiles, export adapter built."
next_action: "Update LLM prompt (llm.py) to generate context events. Update Streamlit UI (app.py) to display new fields. Add Anthropic provider support."
things_to_know:
  - "Used by real-time_support; do not reimplement inside the harness."
  - "feat/realtime-support branch adds: profiles.py, context.py, expected_state.py, tags.py, export_realtime.py, report.py"
  - "Offline generation fully supports all new features. LLM prompt not yet updated for context events."
  - "Export boundary: --format realtime_support produces fixtures with no ground_truth internals."
  - "18 tests (4 original + 14 new) all passing."
---

# support-call-generator — SKILL.md

This file was created for the Builds dashboard. Replace this note with project-specific operating context after review.
