from __future__ import annotations

from datetime import datetime, timezone
import os
import random
from typing import Any
from uuid import uuid4

from support_call_generator.fallback import build_offline_payload
from support_call_generator.leakage import assess_leakage
from support_call_generator.llm import generate_with_openai
from support_call_generator.render import render_transcript_markdown
from support_call_generator.scenarios import SCENARIO_TYPES, build_scenario_spec
from support_call_generator.validator import validate_case


REQUIRED_LLM_TRUTH_KEYS = {
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


def generate_call(
    scenario_type: str | None = None,
    seed: int | None = None,
    case_id: str | None = None,
    use_llm: bool | None = None,
    max_attempts: int = 3,
    root_cause_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    seed = seed if seed is not None else random.randint(1, 999_999_999)
    rng = random.Random(seed)
    scenario_type = scenario_type or rng.choice(SCENARIO_TYPES)
    case_id = case_id or f"call_{uuid4().hex[:10]}"

    spec = build_scenario_spec(scenario_type, seed, root_cause_counts=root_cause_counts)
    model_name = os.getenv("SCG_MODEL", "gpt-5.4-mini")

    should_use_llm = bool(os.getenv("OPENAI_API_KEY")) if use_llm is None else use_llm
    if should_use_llm:
        return _generate_llm_case(case_id, spec, model_name, seed, max_attempts)
    else:
        payload = build_offline_payload(spec)
        model_name = "offline-template"
        generation_mode = "offline"

    case = _build_case(case_id, spec, payload, model_name, generation_mode, seed)
    return _validate_and_attach_leakage(case)


def _generate_llm_case(
    case_id: str,
    spec: dict[str, Any],
    model_name: str,
    seed: int,
    max_attempts: int,
) -> dict[str, Any]:
    errors: list[str] = []
    for _ in range(max(1, max_attempts)):
        try:
            payload = generate_with_openai(spec, model=model_name)
            _validate_payload_shape(payload)
            case = _build_case(case_id, spec, payload, model_name, "llm", seed)
            return _validate_and_attach_leakage(case)
        except Exception as exc:
            if exc.__class__.__name__ == "AuthenticationError":
                raise
            errors.append(exc.__class__.__name__)
    raise ValueError("OpenAI generation failed validation after retries: " + ", ".join(errors))


def _validate_and_attach_leakage(case: dict[str, Any]) -> dict[str, Any]:
    result = validate_case(case)
    if not result.ok:
        raise ValueError("Generated case failed validation: " + "; ".join(result.errors))

    leakage_report = assess_leakage(case)
    if leakage_report["status"] == "FAIL":
        raise ValueError("Generated case failed leakage detection: " + "; ".join(leakage_report["failures"]))
    case["leakage_report"] = leakage_report
    case["review"]["leakage_status"] = leakage_report["status"]

    return case


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload is not an object")

    transcript = payload.get("transcript")
    if not isinstance(transcript, dict) or not isinstance(transcript.get("turns"), list):
        raise ValueError("payload transcript is missing turns")
    for index, turn in enumerate(transcript["turns"], start=1):
        if not isinstance(turn, dict):
            raise ValueError("payload transcript turn is not an object")
        if turn.get("turn") != index or turn.get("speaker") not in {"customer", "agent"} or not turn.get("text"):
            raise ValueError("payload transcript turn is malformed")

    ground_truth = payload.get("ground_truth")
    if not isinstance(ground_truth, dict):
        raise ValueError("payload ground_truth is missing")
    missing_truth = REQUIRED_LLM_TRUTH_KEYS - set(ground_truth)
    if missing_truth:
        raise ValueError("payload ground_truth is incomplete")

    timeline = payload.get("expected_timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError("payload expected_timeline is missing")
    if len(timeline) < 6:
        raise ValueError("payload expected_timeline is too short")


def _build_case(
    case_id: str,
    spec: dict[str, Any],
    payload: dict[str, Any],
    model_name: str,
    generation_mode: str,
    seed: int,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "scenario_spec": spec,
        "transcript": payload["transcript"],
        "transcript_md": render_transcript_markdown(case_id, spec, payload["transcript"]),
        "ground_truth": payload["ground_truth"],
        "expected_timeline": payload["expected_timeline"],
        "leakage_report": payload.get("leakage_report", {"status": "UNKNOWN", "failures": [], "warnings": []}),
        "review": {
            "status": "draft",
            "notes": "",
            "seed": seed,
            "model_name": model_name,
            "generation_mode": generation_mode,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "regeneration_count": 0,
        },
    }
