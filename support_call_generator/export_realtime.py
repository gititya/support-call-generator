from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from support_call_generator.storage import CASES_DIR, list_cases, load_case


EXPORT_DIR = Path("exports")
REALTIME_SCHEMA = "support_process_fixture.v1"

_HANDOFF_RESOLUTIONS = {"handoff", "escalated", "unresolved"}


def export_realtime_support(
    cases_dir: Path = CASES_DIR,
    export_dir: Path = EXPORT_DIR,
    status: str = "accepted",
) -> dict[str, int]:
    out_dir = export_dir / "realtime_support"
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fixtures: list[dict[str, Any]] = []
    exported = 0

    for summary in list_cases(cases_dir):
        if status != "all" and summary["status"] != status:
            continue

        case = load_case(summary["case_id"], cases_dir)
        fixture = _build_fixture(case)
        individual = {k: v for k, v in fixture.items() if k != "schema_version"}
        fixture_path = out_dir / f"{case['case_id']}.json"
        fixture_path.write_text(json.dumps(individual, indent=2) + "\n", encoding="utf-8")
        fixtures.append(fixture)
        exported += 1

    envelope = {
        "schema_version": REALTIME_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_filter": status,
        "case_count": len(fixtures),
        "cases": fixtures,
    }
    (export_dir / "realtime_support_envelope.json").write_text(
        json.dumps(envelope, indent=2) + "\n", encoding="utf-8",
    )
    return {"exported": exported}


def _build_fixture(case: dict[str, Any]) -> dict[str, Any]:
    spec = case["scenario_spec"]
    gt = case["ground_truth"]
    profile = spec.get("profile", {})
    resolution = gt["resolution_type"]
    final_cause = gt["actual_root_cause"]

    is_handoff = resolution in _HANDOFF_RESOLUTIONS
    expected_outcome = _derive_expected_outcome(resolution)

    translated_events = _translate_context_events(
        case.get("context_events", []),
        final_cause,
        case.get("expected_by_turn", []),
    )
    translated_states = _translate_expected_states(case.get("expected_by_turn", []))

    fixture: dict[str, Any] = {
        "schema_version": REALTIME_SCHEMA,
        "case_id": case["case_id"],
        "title": _build_title(case),
        "scenario": spec["scenario_type"],
        "difficulty_profile": profile.get("name", spec.get("difficulty", "unknown")),
        "transcript_turns": case["transcript"]["turns"],
        "context_events": translated_events,
        "expected_by_turn": translated_states,
        "final_cause": "" if is_handoff else final_cause,
        "resolution_type": resolution,
        "intent_tags": case.get("intent_tags", []),
        "expected_outcome": expected_outcome,
    }
    if is_handoff:
        fixture["handoff_summary"] = _build_handoff_summary(case)
    return fixture


def _derive_expected_outcome(resolution: str) -> str:
    return {
        "resolved": "resolved",
        "probable_cause": "probable_cause",
        "escalated": "handoff",
        "handoff": "handoff",
        "unresolved": "handoff",
    }.get(resolution, resolution)


def _translate_context_events(
    events: list[dict[str, Any]],
    final_cause: str,
    expected_states: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    states_by_turn: dict[int, dict[str, Any]] = {}
    for state in expected_states:
        states_by_turn[state["after_turn"]] = state

    translated = []
    for event in events:
        out = dict(event)
        out["relevant"] = not event.get("is_irrelevant", False)
        out.pop("is_irrelevant", None)

        if event.get("reveals_final_cause") and final_cause:
            out["final_cause"] = final_cause

        turn = event.get("after_turn", 0)
        state = states_by_turn.get(turn)
        out["next_check"] = _derive_event_next_check(event, state)

        if event.get("is_irrelevant", False) or not event.get("relevant", True):
            unknowns = _unknowns_from_event(event)
            if unknowns:
                out["unknowns"] = unknowns

        translated.append(out)
    return translated


def _derive_event_next_check(event: dict[str, Any], state: dict[str, Any] | None) -> str:
    if event.get("reveals_final_cause"):
        return "confirm_root_cause"

    ruled = event.get("ruled_out_branches", [])
    candidates = event.get("candidate_branches", [])
    if ruled:
        return _slugify_spaces(f"verify_after_ruling_out_{ruled[0]}")
    if candidates:
        return _slugify_spaces(f"investigate_{candidates[0]}")

    if state:
        checks = state.get("next_check_contains", [])
        if checks:
            return _slugify_spaces(checks[0])

    facts = event.get("facts", [])
    if facts:
        return _slugify_spaces(f"follow_up_{facts[0]}")
    return "continue_investigation"


def _unknowns_from_event(event: dict[str, Any]) -> list[str]:
    candidates = event.get("candidate_branches", [])
    if candidates:
        return [f"investigate_{c}" for c in candidates]
    return []


def _translate_expected_states(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated = []
    for state in states:
        out = dict(state)
        out["facts"] = _dedup([_compact_label(f) for f in state.get("facts", [])])
        out["unknowns"] = _dedup([_compact_label(u) for u in state.get("unknowns", [])])
        out["candidate_branches"] = _dedup([_compact_label(b) for b in state.get("candidate_branches", [])])
        out["ruled_out_branches"] = _dedup([_compact_label(b) for b in state.get("ruled_out_branches", [])])
        out["next_check_contains"] = [_compact_check(c) for c in state.get("next_check_contains", [])]
        translated.append(out)
    return translated


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _compact_label(raw: str) -> str:
    if ":" in raw and len(raw) < 50 and " " not in raw:
        return raw
    words = raw.lower().replace(",", "").replace(".", "").replace("_", " ").split()
    words = [w for w in words if w not in _LABEL_STOP and len(w) > 2]
    if len(words) >= 2:
        return f"{words[0]}:{words[1]}"
    if words:
        return words[0]
    return raw


_LABEL_STOP = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "has",
    "been", "not", "but", "they", "their", "into", "also", "more", "than",
}


def _compact_check(raw: str) -> str:
    slug = _slugify_spaces(raw)
    if len(slug) > 60:
        slug = slug[:57].rstrip("_") + "..."
    return slug


def _slugify_spaces(text: str) -> str:
    return text.replace(" ", "_").replace(".", "").strip("_")


def _build_handoff_summary(case: dict[str, Any]) -> str:
    gt = case["ground_truth"]
    spec = case["scenario_spec"]
    resolution = gt["resolution_type"]
    outcome = gt.get("final_outcome", spec.get("final_outcome", ""))

    parts = []
    if resolution == "escalated":
        parts.append("Escalated to engineering/product.")
    elif resolution == "handoff":
        parts.append("Handed off to customer admin or implementation owner.")
    else:
        parts.append("Investigation remains open with incomplete evidence.")

    if outcome:
        parts.append(outcome)

    evidence = gt.get("key_evidence", [])
    if evidence:
        parts.append(f"Key evidence collected: {'; '.join(evidence[:3])}.")

    return " ".join(parts)


def _build_title(case: dict[str, Any]) -> str:
    summary = case.get("transcript", {}).get("summary")
    if summary and len(summary) < 120:
        return summary
    spec = case["scenario_spec"]
    root = spec.get("hidden_root_cause", "unknown issue")
    scenario = spec["scenario_type"].replace("_", " ")
    if len(root) > 80:
        root = root[:77] + "..."
    return f"{scenario}: {root}"
