from __future__ import annotations

from typing import Any

from support_call_generator.models import ValidationResult


REQUIRED_CASE_KEYS = {
    "case_id",
    "scenario_spec",
    "transcript",
    "transcript_md",
    "ground_truth",
    "expected_timeline",
    "consumer_summary",
    "exposure_marker",
    "review",
}

REQUIRED_TRUTH_KEYS = {
    "actual_root_cause",
    "confidence",
    "resolution_type",
    "root_cause_category",
    "difficulty_metadata",
    "issue_path",
    "key_evidence",
    "wrong_paths",
    "misleading_evidence",
    "false_leads",
    "abandoned_troubleshooting_paths",
    "hypothesis_reversals",
    "conflicting_observations",
    "late_reveal_facts",
    "doctrine_adherence",
    "why_difficult",
    "escalation_timeline",
    "escalation_trigger",
    "best_diagnostic_questions",
    "final_outcome",
}

REQUIRED_TIMELINE_STATES = {"activate", "strengthen", "weaken", "discard", "confirm"}


def validate_case(case: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []

    missing = REQUIRED_CASE_KEYS - set(case)
    if missing:
        errors.append(f"missing case keys: {', '.join(sorted(missing))}")

    ground_truth = case.get("ground_truth", {})
    if "ground_truth" in case:
        missing_truth = REQUIRED_TRUTH_KEYS - set(ground_truth)
        if missing_truth:
            errors.append(f"missing ground truth keys: {', '.join(sorted(missing_truth))}")
        difficulty_metadata = ground_truth.get("difficulty_metadata", {})
        for score in ["ambiguity_score", "leakage_score", "realism_score"]:
            value = difficulty_metadata.get(score)
            if not isinstance(value, int) or not 1 <= value <= 5:
                errors.append(f"{score} must be an integer from 1 to 5")
        if ground_truth.get("resolution_type") not in {"resolved", "probable_cause", "escalated", "handoff", "unresolved"}:
            errors.append("resolution_type is invalid")
        confidence = ground_truth.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append("confidence must be between 0 and 1")
        for key in [
            "misleading_evidence",
            "false_leads",
            "abandoned_troubleshooting_paths",
            "hypothesis_reversals",
            "conflicting_observations",
            "late_reveal_facts",
        ]:
            if not isinstance(ground_truth.get(key), list) or len(ground_truth.get(key, [])) < 2:
                errors.append(f"ground truth must include at least two {key}")
        if not isinstance(ground_truth.get("why_difficult"), list) or len(ground_truth.get("why_difficult", [])) < 2:
            errors.append("ground truth must explain why the call is difficult")
        if case.get("scenario_spec", {}).get("scenario_type") == "b2c_subscription_billing":
            _validate_b2c_expected_handoff(ground_truth, errors)

    turns = case.get("transcript", {}).get("turns", [])
    if len(turns) < 16:
        errors.append("transcript must contain at least 16 turns")

    speakers = {turn.get("speaker") for turn in turns}
    if not {"customer", "agent"}.issubset(speakers):
        errors.append("transcript must include customer and agent turns")

    for index, turn in enumerate(turns, start=1):
        if turn.get("turn") != index:
            errors.append("turn numbers must be sequential")
            break
        if not turn.get("text"):
            errors.append(f"turn {index} is missing text")

    root_cause = ground_truth.get("actual_root_cause")
    if root_cause and turns:
        final_third_start = int(len(turns) * 2 / 3)
        early_text = " ".join(turn.get("text", "") for turn in turns[:final_third_start])
        if _normalized(root_cause) in _normalized(early_text):
            errors.append("root cause leaked verbatim before final third of transcript")

    timeline = case.get("expected_timeline")
    if not timeline:
        errors.append("expected timeline cannot be empty")
    else:
        states = {entry.get("state") for entry in timeline}
        missing_states = REQUIRED_TIMELINE_STATES - states
        if missing_states:
            errors.append(f"expected timeline is missing states: {', '.join(sorted(missing_states))}")

        if root_cause and turns:
            final_third_start = int(len(turns) * 2 / 3)
            early_confirmations = [
                entry
                for entry in timeline
                if entry.get("hypothesis") == root_cause
                and entry.get("turn", 0) < final_third_start
                and float(entry.get("confidence", 0)) >= 0.7
            ]
            if early_confirmations:
                errors.append("root cause reached high confidence before final third of transcript")

        hypotheses = {entry.get("hypothesis") for entry in timeline}
        if len(hypotheses) < 3:
            errors.append("expected timeline must track at least three competing hypotheses")

    context_events = case.get("context_events", [])
    if context_events:
        _validate_context_events(context_events, len(turns), errors)

    expected_by_turn = case.get("expected_by_turn", [])
    if expected_by_turn:
        _validate_expected_state(expected_by_turn, len(turns), errors)

    summary = case.get("consumer_summary", {})
    if not isinstance(summary, dict) or not summary.get("summary"):
        errors.append("consumer_summary must include summary")

    exposure = case.get("exposure_marker", {})
    if not isinstance(exposure, dict) or exposure.get("synthetic_only") is not True:
        errors.append("exposure_marker must identify synthetic-only data")
    if exposure.get("sensitivity_level") not in {"low", "medium", "high"}:
        errors.append("exposure_marker sensitivity_level is invalid")

    return ValidationResult(ok=not errors, errors=errors)


def _validate_context_events(events: list, turn_count: int, errors: list[str]) -> None:
    final_third_start = max(1, int(turn_count * 2 / 3))
    reveal_count = 0

    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"context event {i} is not an object")
            continue

        after_turn = event.get("after_turn")
        if not isinstance(after_turn, int) or after_turn < 1 or after_turn > turn_count:
            errors.append(f"context event {i} has invalid after_turn")

        if not event.get("source"):
            errors.append(f"context event {i} is missing source")

        if not event.get("description"):
            errors.append(f"context event {i} is missing description")

        if event.get("reveals_final_cause"):
            reveal_count += 1
            if isinstance(after_turn, int) and after_turn < final_third_start:
                errors.append(f"context event {i} reveals final cause before final third (turn {after_turn} < {final_third_start})")

    if reveal_count > 1:
        errors.append(f"multiple context events ({reveal_count}) marked as reveals_final_cause")


def _validate_expected_state(states: list, turn_count: int, errors: list[str]) -> None:
    if len(states) != turn_count:
        errors.append(f"expected_by_turn has {len(states)} entries but transcript has {turn_count} turns")
        return

    final_third_start = max(1, int(turn_count * 2 / 3))
    prev_facts: set[str] = set()
    prev_ruled_out: set[str] = set()

    for i, state in enumerate(states):
        if not isinstance(state, dict):
            errors.append(f"expected_by_turn entry {i} is not an object")
            continue

        turn = state.get("after_turn")
        if turn != i + 1:
            errors.append(f"expected_by_turn entry {i} has wrong after_turn: {turn}")

        current_facts = set(state.get("facts", []))
        if not prev_facts.issubset(current_facts):
            lost = prev_facts - current_facts
            errors.append(f"expected_by_turn lost facts at turn {turn}: {lost}")
        prev_facts = current_facts

        current_ruled = set(state.get("ruled_out_branches", []))
        if not prev_ruled_out.issubset(current_ruled):
            lost = prev_ruled_out - current_ruled
            errors.append(f"expected_by_turn lost ruled_out_branches at turn {turn}: {lost}")
        prev_ruled_out = current_ruled

        if state.get("final_cause_allowed") and turn < final_third_start:
            errors.append(f"final_cause_allowed is true before final third (turn {turn})")


def _validate_b2c_expected_handoff(ground_truth: dict[str, Any], errors: list[str]) -> None:
    handoff = ground_truth.get("expected_handoff")
    if not isinstance(handoff, dict):
        errors.append("b2c_subscription_billing ground truth must include expected_handoff")
        return

    ai_to_human = handoff.get("ai_to_human")
    if not isinstance(ai_to_human, dict):
        errors.append("expected_handoff must include ai_to_human")
        return

    required = {
        "customer_account_identity",
        "charge",
        "customer_claim",
        "desired_outcome",
        "checks_with_results",
        "ruled_out_branches",
        "likely_cause",
        "confidence",
        "risk_urgency",
        "next_step",
        "what_not_to_promise",
    }
    missing = required - set(ai_to_human)
    if missing:
        errors.append(f"expected_handoff.ai_to_human missing fields: {', '.join(sorted(missing))}")

    charge = ai_to_human.get("charge", {})
    if not isinstance(charge, dict) or not {"amount", "date", "last4", "descriptor", "transaction_id"}.issubset(charge):
        errors.append("expected_handoff.ai_to_human.charge must include amount, date, last4, descriptor, and transaction_id")

    if ground_truth.get("resolution_type") == "escalated" and "human_to_engineering" not in handoff:
        errors.append("escalated b2c_subscription_billing cases must include human_to_engineering")


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())
