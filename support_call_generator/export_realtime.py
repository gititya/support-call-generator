from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from support_call_generator.storage import CASES_DIR, list_cases, load_case


EXPORT_DIR = Path("exports")
REALTIME_SCHEMA = "support_process_fixture.v1"

_HANDOFF_RESOLUTIONS = {"handoff", "escalated", "unresolved"}
_BANNED_SUPPORT_FACING_PHRASES = [
    "hidden configuration detail",
    "mechanism evidence",
    "support-process guidance",
    "active branches",
    "presenting likely cause",
]


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

    compact_cause = _compact_root_cause(spec.get("root_cause_id", ""), final_cause)

    translated_events = _translate_context_events(
        case.get("context_events", []),
        "" if is_handoff else compact_cause,
        case.get("expected_by_turn", []),
        expected_outcome,
        resolution,
        spec["scenario_type"],
    )
    turn_count = len(case["transcript"]["turns"])
    translated_events = _ensure_turn_guidance_events(
        translated_events,
        turn_count,
        expected_outcome,
        resolution,
        spec["scenario_type"],
    )
    translated_states = _compute_expected_states(translated_events, turn_count)

    fixture: dict[str, Any] = {
        "schema_version": REALTIME_SCHEMA,
        "case_id": case["case_id"],
        "title": _build_title(case),
        "scenario": spec["scenario_type"],
        "difficulty_profile": profile.get("name", spec.get("difficulty", "unknown")),
        "transcript_turns": case["transcript"]["turns"],
        "context_events": translated_events,
        "expected_by_turn": translated_states,
        "final_cause": "" if is_handoff else compact_cause,
        "resolution_type": resolution,
        "intent_tags": case.get("intent_tags", []),
        "expected_outcome": expected_outcome,
        "safe_customer_summary": _build_safe_customer_summary(case, expected_outcome),
        "customer_safe_summary": _build_safe_customer_summary(case, expected_outcome),
        "evidence_summary": _build_evidence_summary(translated_events, spec["scenario_type"]),
        "next_best_action": _top_level_next_best_action(spec["scenario_type"], expected_outcome, resolution),
    }
    if is_handoff:
        fixture["handoff_summary"] = _build_handoff_summary(case)
        fixture["next_owner"] = _derive_next_owner(case)
    return fixture


def _compact_root_cause(root_cause_id: str, actual_root_cause: str) -> str:
    slug = root_cause_id or _slugify_spaces(actual_root_cause.lower())
    return slug.strip("_")


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
    expected_outcome: str,
    resolution: str,
    scenario_type: str,
) -> list[dict[str, Any]]:
    states_by_turn: dict[int, dict[str, Any]] = {}
    for state in expected_states:
        states_by_turn[state["after_turn"]] = state

    translated = []
    for event in events:
        out = dict(event)
        out["relevant"] = not event.get("is_irrelevant", False)
        out.pop("is_irrelevant", None)

        out["facts"] = [_compact_label(f) for f in event.get("facts", [])]
        out["ruled_out_branches"] = [_slugify_spaces(b) for b in event.get("ruled_out_branches", [])]
        out["candidate_branches"] = [_slugify_spaces(b) for b in event.get("candidate_branches", [])]
        out["resolved_unknowns"] = [_slugify_spaces(u) for u in event.get("resolved_unknowns", [])]

        if event.get("reveals_final_cause") and final_cause:
            out["final_cause"] = final_cause

        turn = event.get("after_turn", 0)
        state = states_by_turn.get(turn)
        out["next_check"] = _derive_event_next_check(event, state, expected_outcome, resolution)
        out["description"] = _concrete_context_description(out, scenario_type)
        out["evidence_summary"] = out["description"]
        out["next_best_action"] = _support_action_for_context(out, scenario_type, expected_outcome, resolution)

        translated.append(out)
    return translated


def _derive_event_next_check(
    event: dict[str, Any],
    state: dict[str, Any] | None,
    expected_outcome: str,
    resolution: str,
) -> str:
    if event.get("reveals_final_cause"):
        if expected_outcome == "resolved":
            return _top_level_next_best_action("", "resolved", resolution)
        if expected_outcome == "probable_cause":
            return _top_level_next_best_action("", "probable_cause", resolution)
        return _handoff_next_check(resolution)

    ruled = event.get("ruled_out_branches", [])
    candidates = event.get("candidate_branches", [])
    if ruled:
        return f"verify evidence after ruling out {_readable_label(ruled[0])}"
    if candidates:
        return f"investigate evidence for {_readable_label(candidates[0])}"

    if state:
        checks = state.get("next_check_contains", [])
        if checks:
            return _slugify_spaces(checks[0])

    facts = event.get("facts", [])
    if facts:
        return f"follow up on {_readable_label(facts[0])}"
    return "continue investigation with the next useful evidence check"


def _ensure_turn_guidance_events(
    events: list[dict[str, Any]],
    turn_count: int,
    expected_outcome: str,
    resolution: str,
    scenario_type: str,
) -> list[dict[str, Any]]:
    by_turn = {int(event.get("after_turn", 0)): event for event in events if event.get("next_check")}
    enriched = list(events)
    final_third = max(1, int(turn_count * 2 / 3))

    for turn in range(1, turn_count + 1):
        if turn in by_turn:
            continue
        enriched.append({
            "after_turn": turn,
            "source": "support_process_guidance",
            "description": _turn_guidance_description(turn, turn_count, scenario_type),
            "facts": [],
            "resolved_unknowns": [],
            "ruled_out_branches": [],
            "candidate_branches": [],
            "relevant": True,
            "is_conflicting": False,
            "reveals_final_cause": False,
            "next_check": _turn_guidance_next_check(turn, turn_count, final_third, expected_outcome, resolution, scenario_type),
            "evidence_summary": _turn_guidance_description(turn, turn_count, scenario_type),
            "next_best_action": _turn_guidance_next_check(turn, turn_count, final_third, expected_outcome, resolution, scenario_type),
        })

    enriched.sort(key=lambda e: (int(e.get("after_turn", 0)), e.get("source", "")))
    return enriched


def _turn_guidance_next_check(
    turn: int,
    turn_count: int,
    final_third: int,
    expected_outcome: str,
    resolution: str,
    scenario_type: str,
) -> str:
    domain = scenario_type.replace("_", " ")
    if turn < max(3, int(turn_count / 3)):
        return f"Ask what changed recently and collect one working example and one affected example for the {domain} issue."
    if turn < final_third:
        return f"Compare the working and affected examples, then check the strongest product signal for the {domain} issue."
    if expected_outcome == "resolved":
        return _top_level_next_best_action(scenario_type, "resolved", resolution)
    if expected_outcome == "probable_cause":
        return _top_level_next_best_action(scenario_type, "probable_cause", resolution)
    return _handoff_next_check(resolution)


def _handoff_next_check(resolution: str) -> str:
    if resolution == "escalated":
        return "Send the evidence summary, affected examples, and latest warning details to engineering or product support."
    if resolution == "unresolved":
        return "Assign a follow-up owner and keep the open verification steps attached to the case."
    return "Send the evidence summary to the customer admin or implementation owner and ask them to confirm the remaining dependency."


def _turn_guidance_description(turn: int, turn_count: int, scenario_type: str) -> str:
    domain = scenario_type.replace("_", " ")
    if turn < max(3, int(turn_count / 3)):
        return f"No new system evidence yet; the agent should gather a working and affected example for the {domain} issue."
    return f"No new system evidence at this turn; continue comparing product signals for the {domain} issue."


def _concrete_context_description(event: dict[str, Any], scenario_type: str) -> str:
    facts = set(event.get("facts", []))
    description = event.get("description", "")
    if "comparison:config_differs" in facts or "hidden configuration detail" in description.lower():
        return _comparison_description(scenario_type)
    if "logs:warning_dismissed" in facts:
        return _warning_description(scenario_type)
    if "admin:late_mention" in facts:
        return _admin_detail_description(scenario_type)
    if "sso_group:membership" in facts:
        return "Identity provider data shows group membership is relevant to the affected user comparison."
    if "billing_status:active" in facts:
        return "Billing shows the account is active and payment is current, so a billing hold is less likely."
    if description:
        return _clean_support_text(description)
    return _turn_guidance_description(1, 3, scenario_type)


def _comparison_description(scenario_type: str) -> str:
    return {
        "permissions_access": "A working user and a blocked user differ in access configuration; compare identity group and workspace role assignments.",
        "onboarding_migration": "A migrated record that worked and a missing record differ in source export settings; compare archive and ownership settings.",
        "workspace_setup": "A working workspace and the failed workspace differ in setup configuration; compare region, template, and admin approval settings.",
        "integrations_data_sync": "A successful sync and failed sync differ in connector configuration; compare OAuth scope, object mapping, and job warnings.",
        "billing_plan_entitlement": "A correctly entitled account and affected account differ in billing entitlement state; compare plan, seat, and refresh status.",
    }.get(scenario_type, "A working example and affected example differ in configuration; compare the exact setting before closing the case.")


def _warning_description(scenario_type: str) -> str:
    return {
        "permissions_access": "The audit log contains an access warning that should be checked against the affected user's role source.",
        "onboarding_migration": "The migration log contains a warning that should be checked against the affected records.",
        "workspace_setup": "The workspace setup log contains a warning that should be checked before retrying setup.",
        "integrations_data_sync": "The sync log contains a warning that should be checked against the failed job.",
        "billing_plan_entitlement": "The entitlement service contains a warning that should be checked against the plan refresh.",
    }.get(scenario_type, "The product log contains a warning that should be checked before closing the case.")


def _admin_detail_description(scenario_type: str) -> str:
    return {
        "permissions_access": "An admin shared a late access detail; verify it against identity provider and workspace role records.",
        "onboarding_migration": "An admin shared a late migration detail; verify it against the source export and migration job logs.",
        "workspace_setup": "An admin shared a late setup detail; verify it against workspace setup settings.",
        "integrations_data_sync": "An admin shared a late integration detail; verify it against connector settings and sync logs.",
        "billing_plan_entitlement": "An admin shared a late billing detail; verify it against entitlement and invoice records.",
    }.get(scenario_type, "An admin shared a late detail; verify it against product records.")


def _support_action_for_context(
    event: dict[str, Any],
    scenario_type: str,
    expected_outcome: str,
    resolution: str,
) -> str:
    if event.get("reveals_final_cause"):
        return _top_level_next_best_action(scenario_type, expected_outcome, resolution)
    if event.get("ruled_out_branches"):
        return f"Update the case notes with why {_readable_label(event['ruled_out_branches'][0])} is less likely, then continue the comparison check."
    if event.get("candidate_branches"):
        return f"Check product records that would confirm or weaken {_readable_label(event['candidate_branches'][0])}."
    return _turn_guidance_next_check(2, 6, 4, expected_outcome, resolution, scenario_type)


def _top_level_next_best_action(scenario_type: str, expected_outcome: str, resolution: str) -> str:
    if expected_outcome == "handoff":
        return _handoff_next_check(resolution)
    if expected_outcome == "probable_cause":
        return {
            "permissions_access": "Compare one blocked user with one working user in the identity provider before treating the access cause as resolved.",
            "onboarding_migration": "Verify one affected record against the source export before treating the migration cause as resolved.",
            "workspace_setup": "Verify the failed workspace settings against a working workspace before treating the setup cause as resolved.",
            "integrations_data_sync": "Verify the failed sync job against a recent successful job before treating the integration cause as resolved.",
            "billing_plan_entitlement": "Confirm the entitlement refresh status before treating the billing issue as resolved.",
        }.get(scenario_type, "Verify one more product signal before treating the likely cause as resolved.")
    return {
        "permissions_access": "Confirm the affected user can access the workspace after the role or group fix.",
        "onboarding_migration": "Confirm the affected record appears correctly after the migration correction.",
        "workspace_setup": "Confirm the workspace can complete setup after the configuration correction.",
        "integrations_data_sync": "Confirm the affected object syncs successfully after the connector correction.",
        "billing_plan_entitlement": "Confirm the customer sees the correct plan after entitlement refresh.",
    }.get(scenario_type, "Confirm the customer can complete the affected workflow after the fix.")


def _clean_support_text(text: str) -> str:
    cleaned = text
    replacements = {
        "a working example differs in one hidden configuration detail": "a working example and affected example differ in configuration",
        "Support-process guidance for the next useful investigation step.": "No new system evidence at this turn; continue the next support check.",
        "mechanism evidence": "product evidence",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned


def _unknowns_from_event(event: dict[str, Any]) -> list[str]:
    candidates = event.get("candidate_branches", [])
    if candidates:
        return [f"investigate_{c}" for c in candidates]
    return []


def _compute_expected_states(
    translated_events: list[dict[str, Any]],
    turn_count: int,
) -> list[dict[str, Any]]:
    events_by_turn: dict[int, list[dict[str, Any]]] = {}
    for event in translated_events:
        t = int(event.get("after_turn", 0))
        events_by_turn.setdefault(t, []).append(event)

    facts: list[str] = []
    unknowns: list[str] = []
    candidate_branches: list[str] = []
    ruled_out_branches: list[str] = []
    next_check = ""
    final_cause_allowed = False

    states: list[dict[str, Any]] = []

    for turn_num in range(1, turn_count + 1):
        for event in events_by_turn.get(turn_num, []):
            if event.get("relevant") is False:
                continue
            for f in event.get("facts", []):
                if f not in facts:
                    facts.append(f)
            for u in event.get("unknowns", []):
                if u not in facts and u not in unknowns:
                    unknowns.append(u)
            for u in event.get("resolved_unknowns", []):
                while u in unknowns:
                    unknowns.remove(u)
            for b in event.get("candidate_branches", []):
                if b not in ruled_out_branches and b not in candidate_branches:
                    candidate_branches.append(b)
            for b in event.get("ruled_out_branches", []):
                while b in candidate_branches:
                    candidate_branches.remove(b)
                if b not in ruled_out_branches:
                    ruled_out_branches.append(b)
            if event.get("next_check"):
                next_check = event["next_check"]
            fc = event.get("final_cause", "")
            if fc:
                final_cause_allowed = True
                if fc not in candidate_branches:
                    candidate_branches.append(fc)
                while fc in ruled_out_branches:
                    ruled_out_branches.remove(fc)
            if event.get("reveals_final_cause"):
                final_cause_allowed = True
            # reconcile: ruled_out not in candidates
            for b in list(ruled_out_branches):
                while b in candidate_branches:
                    candidate_branches.remove(b)

        next_check_contains = _extract_check_terms(next_check) if next_check else []

        states.append({
            "after_turn": turn_num,
            "facts": list(facts),
            "unknowns": list(unknowns),
            "candidate_branches": list(candidate_branches),
            "ruled_out_branches": list(ruled_out_branches),
            "next_check": next_check or "continue support investigation with the next useful evidence check",
            "next_check_contains": next_check_contains,
            "final_cause_allowed": final_cause_allowed,
        })

    return states


def _extract_check_terms(next_check: str) -> list[str]:
    words = next_check.replace("_", " ").split()
    terms = [w for w in words if len(w) > 3 and w.lower() not in _LABEL_STOP]
    if len(terms) > 3:
        terms = terms[:3]
    return terms


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


def _readable_label(text: str) -> str:
    return text.replace("_", " ").replace(":", " ")


def _build_safe_customer_summary(case: dict[str, Any], expected_outcome: str) -> str:
    gt = case["ground_truth"]
    spec = case["scenario_spec"]
    outcome = gt.get("final_outcome", spec.get("final_outcome", ""))

    if expected_outcome == "resolved":
        return f"Support found product evidence and can confirm the corrective action. {outcome}".strip()
    if expected_outcome == "probable_cause":
        cause = gt.get("actual_root_cause", "the leading operational cause")
        return (
            f"The likely cause is {cause}. Support should verify the remaining product evidence before treating it as fully resolved."
        )
    return _build_handoff_summary(case)


def _build_evidence_summary(events: list[dict[str, Any]], scenario_type: str) -> str:
    relevant = [event for event in events if event.get("relevant", True)]
    final_events = [
        event
        for event in relevant
        if event.get("final_cause") or event.get("reveals_final_cause")
    ]
    candidates = final_events or relevant
    for event in reversed(candidates):
        description = event.get("evidence_summary") or event.get("description")
        if description:
            return description
    return _comparison_description(scenario_type)


def _derive_next_owner(case: dict[str, Any]) -> str:
    resolution = case["ground_truth"]["resolution_type"]
    scenario = case["scenario_spec"]["scenario_type"]
    if resolution == "escalated":
        return "engineering/product support"
    if scenario == "permissions_access":
        return "customer admin or identity owner"
    if scenario == "workspace_setup":
        return "customer admin or implementation owner"
    if scenario == "integrations_data_sync":
        return "integration owner or engineering support"
    if scenario == "billing_plan_entitlement":
        return "billing owner or account support"
    return "follow-up support owner"


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
