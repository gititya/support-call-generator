from __future__ import annotations

from typing import Any


def derive_expected_state(
    turns: list[dict[str, Any]],
    context_events: list[dict[str, Any]],
    ground_truth: dict[str, Any],
    expected_timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    turn_count = len(turns)
    if turn_count == 0:
        return []

    events_by_turn: dict[int, list[dict[str, Any]]] = {}
    for event in context_events:
        t = event.get("after_turn", 0)
        events_by_turn.setdefault(t, []).append(event)

    timeline_by_turn: dict[int, list[dict[str, Any]]] = {}
    for entry in expected_timeline:
        t = entry.get("turn", 0)
        timeline_by_turn.setdefault(t, []).append(entry)

    initial_unknowns = _extract_initial_unknowns(ground_truth)

    facts: list[str] = []
    unknowns: list[str] = list(initial_unknowns)
    candidate_branches: list[str] = []
    ruled_out_branches: list[str] = []
    final_cause_allowed = False

    states: list[dict[str, Any]] = []

    for turn_num in range(1, turn_count + 1):
        for entry in timeline_by_turn.get(turn_num, []):
            hyp = entry.get("hypothesis", "")
            state = entry.get("state", "")
            if state == "activate" and hyp not in candidate_branches:
                candidate_branches.append(hyp)
            elif state == "strengthen":
                pass
            elif state == "weaken":
                pass
            elif state == "discard":
                if hyp in candidate_branches:
                    candidate_branches.remove(hyp)
                if hyp not in ruled_out_branches:
                    ruled_out_branches.append(hyp)
            elif state == "confirm":
                if hyp not in candidate_branches:
                    candidate_branches.append(hyp)

        for event in events_by_turn.get(turn_num, []):
            if event.get("is_irrelevant"):
                continue

            for fact in event.get("facts", []):
                if fact not in facts:
                    facts.append(fact)

            for unknown in event.get("resolved_unknowns", []):
                if unknown in unknowns:
                    unknowns.remove(unknown)

            for branch in event.get("ruled_out_branches", []):
                if branch in candidate_branches:
                    candidate_branches.remove(branch)
                if branch not in ruled_out_branches:
                    ruled_out_branches.append(branch)

            for branch in event.get("candidate_branches", []):
                if branch not in candidate_branches and branch not in ruled_out_branches:
                    candidate_branches.append(branch)

            if event.get("reveals_final_cause"):
                final_cause_allowed = True

        next_checks = _derive_next_checks(unknowns, candidate_branches)

        states.append({
            "after_turn": turn_num,
            "facts": list(facts),
            "unknowns": list(unknowns),
            "candidate_branches": list(candidate_branches),
            "ruled_out_branches": list(ruled_out_branches),
            "next_check_contains": next_checks,
            "final_cause_allowed": final_cause_allowed,
        })

    return states


def _extract_initial_unknowns(ground_truth: dict[str, Any]) -> list[str]:
    unknowns = []
    for path in ground_truth.get("wrong_paths", []):
        unknowns.append(path)
    root_cause = ground_truth.get("actual_root_cause", "")
    if root_cause:
        slug = "_".join(root_cause.lower().split()[:5])
        unknowns.append(slug)
    return unknowns


def _derive_next_checks(unknowns: list[str], candidate_branches: list[str]) -> list[str]:
    checks = []
    if unknowns:
        checks.append(f"investigate_{unknowns[0]}")
    if len(candidate_branches) > 1:
        checks.append(f"compare_{candidate_branches[0]}_vs_{candidate_branches[1]}")
    elif candidate_branches:
        checks.append(f"verify_{candidate_branches[0]}")
    return checks
