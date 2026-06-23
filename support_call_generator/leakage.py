from __future__ import annotations

from typing import Any


def assess_leakage(case: dict[str, Any]) -> dict[str, Any]:
    turns = case["transcript"]["turns"]
    truth = case["ground_truth"]
    timeline = case["expected_timeline"]
    root_cause = truth["actual_root_cause"]
    final_third_start = int(len(turns) * 2 / 3)
    halfway = int(len(turns) / 2)

    fail: list[str] = []
    warning: list[str] = []

    early_text = _normalize(" ".join(turn["text"] for turn in turns[:final_third_start]))
    if _normalize(root_cause) in early_text:
        fail.append("root cause appears verbatim before final third")

    early_customer_text = _normalize(" ".join(turn["text"] for turn in turns[:halfway] if turn["speaker"] == "customer"))
    root_terms = [term for term in _content_terms(root_cause) if len(term) > 4]
    if root_terms and sum(1 for term in root_terms if term in early_customer_text) >= max(2, len(root_terms) // 2):
        warning.append("customer may reveal too many root-cause-specific terms early")

    early_agent_text = _normalize(" ".join(turn["text"] for turn in turns[:halfway] if turn["speaker"] == "agent"))
    if any(phrase in early_agent_text for phrase in ["the root cause is", "the cause is", "this confirms"]):
        warning.append("agent sounds certain before enough evidence accumulates")

    high_confidence_before_half = [
        entry
        for entry in timeline
        if entry.get("turn", 0) <= halfway and float(entry.get("confidence", 0)) >= 0.7
    ]
    if high_confidence_before_half:
        fail.append("hypothesis confidence exceeds 0.70 before halfway")

    early_hypotheses = {entry.get("hypothesis") for entry in timeline if entry.get("turn", 0) <= halfway}
    if len(early_hypotheses) < 2:
        warning.append("hypothesis space may collapse too early")

    if len(truth.get("false_leads", [])) < 2:
        fail.append("fewer than two false leads")

    context_events = case.get("context_events", [])
    if context_events:
        _check_context_leakage(context_events, root_cause, final_third_start, fail, warning)

    status = "PASS"
    if warning:
        status = "WARNING"
    if fail:
        status = "FAIL"

    return {
        "status": status,
        "failures": fail,
        "warnings": warning,
    }


def _check_context_leakage(
    events: list[dict],
    root_cause: str,
    final_third_start: int,
    fail: list[str],
    warning: list[str],
) -> None:
    root_terms = [t for t in _content_terms(root_cause) if len(t) > 4]

    for i, event in enumerate(events):
        if event.get("reveals_final_cause") and event.get("after_turn", 0) < final_third_start:
            fail.append(f"context event {i} reveals final cause before final third")

        if event.get("reveals_final_cause") or event.get("is_irrelevant"):
            continue

        desc = _normalize(event.get("description", ""))
        fact_text = _normalize(" ".join(event.get("facts", [])))
        combined = desc + " " + fact_text

        if _normalize(root_cause) in combined:
            if event.get("after_turn", 0) < final_third_start:
                fail.append(f"context event {i} contains root cause verbatim before final third")

        if root_terms and event.get("after_turn", 0) < final_third_start:
            matches = sum(1 for t in root_terms if t in combined)
            if matches >= max(2, len(root_terms) // 2):
                warning.append(f"context event {i} may leak too many root-cause terms")


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").replace("/", " ").split())


def _content_terms(text: str) -> list[str]:
    stopwords = {
        "after",
        "because",
        "before",
        "during",
        "from",
        "into",
        "that",
        "the",
        "their",
        "were",
        "with",
    }
    return [term for term in _normalize(text).split() if term not in stopwords]
