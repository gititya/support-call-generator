---
status: "in-progress"
current_phase: "Realtime support evolution — all offline + LLM features complete. Anthropic provider added. Streamlit UI updated."
next_action: "Live LLM test with both providers. Visual verification of Streamlit UI. Generate batch, review, export realtime_support fixtures."
things_to_know:
  - "Used by real-time_support; do not reimplement inside the harness."
  - "feat/realtime-support branch adds: profiles.py, context.py, expected_state.py, tags.py, export_realtime.py, report.py"
  - "LLM prompt now includes context_events in expected JSON schema + generation rules."
  - "Anthropic provider: SCG_PROVIDER=anthropic dispatches to claude-sonnet-4-6. pip install -e '.[anthropic]' to enable."
  - "Streamlit UI: profile/provider selectors, intent tag badges, context events + expected state expanders."
  - "Export boundary: --format realtime_support produces fixtures with no ground_truth internals."
  - "18 tests (4 original + 14 new) all passing."
---

# support-call-generator — SKILL.md

This file was created for the Builds dashboard. Replace this note with project-specific operating context after review.
