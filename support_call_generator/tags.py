from __future__ import annotations

from typing import Any


def derive_intent_tags(case: dict[str, Any]) -> list[str]:
    tags: set[str] = set()
    gt = case.get("ground_truth", {})
    ctx = case.get("context_events", [])
    timeline = case.get("expected_timeline", [])
    turns = case.get("transcript", {}).get("turns", [])
    turn_count = len(turns)
    final_third_start = max(1, int(turn_count * 2 / 3))
    last_quarter_start = max(1, int(turn_count * 3 / 4))

    for entry in timeline:
        hyp = entry.get("hypothesis", "")
        state = entry.get("state", "")
        turn = entry.get("turn", 0)
        if state == "confirm" and hyp == gt.get("actual_root_cause") and turn < final_third_start:
            tags.add("premature_final_cause")

    wrong_hyps: dict[str, list[str]] = {}
    for entry in timeline:
        hyp = entry.get("hypothesis", "")
        if hyp != gt.get("actual_root_cause"):
            wrong_hyps.setdefault(hyp, []).append(entry.get("state", ""))
    for hyp, states in wrong_hyps.items():
        if "activate" in states and ("strengthen" in states or "weaken" in states) and "discard" in states:
            tags.add("wrong_path_recovery")
            break

    if any(e.get("is_irrelevant") for e in ctx):
        tags.add("irrelevant_context_filtering")

    if any(e.get("is_conflicting") for e in ctx):
        tags.add("conflicting_context")

    spec = case.get("scenario_spec", {})
    if spec.get("customer_unreliability"):
        tags.add("customer_correction")

    if any(e.get("after_turn", 0) >= last_quarter_start for e in ctx if not e.get("is_irrelevant")):
        tags.add("late_evidence_reveal")

    resolution = gt.get("resolution_type", "")
    if resolution in ("escalated", "handoff", "unresolved"):
        tags.add("unresolved_outcome")

    return sorted(tags)
