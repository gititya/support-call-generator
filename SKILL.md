
# support-call-generator — SKILL.md

This file was created for the Builds dashboard. Replace this note with project-specific operating context after review.

## Operating context

Support Call Generator is **infrastructure, not a standalone product**: a synthetic support-call generator whose only job is to be a reusable dependency for two consumers —

- `real-time_support_Updated` (B2B support-process eval) — via `export_realtime.py` → `support_process_fixture.v1`.
- The Handoff Quality Gate (B2C) — `b2c_subscription_billing` disputed-charge cases carrying an `expected_handoff` answer key.

It is **not** used by Signal (Signal runs on real CFPB data; synthetic complaints would undermine it).

Design invariants (do not break):

- Keep the offline deterministic fallback working — tests must run with no API key.
- Keep the export boundary strict: transcript-only vs. hidden ground-truth. Never leak `ground_truth` / `expected_timeline` / `leakage_report` to transcript consumers.
- `b2c_subscription_billing` cases must carry `expected_handoff` (enforced in `generator.py`).

Scope discipline: build only what realtime or the Handoff Gate actually consumes. The `Evolving support call_generator.md` doc is a **reference wishlist, not a build plan** — do not implement B2C platform packs, a Signal/CFPB export, coaching/escalation packs, or a public API on spec.
