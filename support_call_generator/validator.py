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

    return ValidationResult(ok=not errors, errors=errors)


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())
