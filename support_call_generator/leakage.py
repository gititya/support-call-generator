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
