from __future__ import annotations

from collections import Counter
from typing import Any


def print_batch_report(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "0 cases generated"

    n = len(cases)
    profiles = Counter()
    scenarios = Counter()
    resolutions = Counter()
    leakage = Counter()
    tags_counter = Counter()
    root_causes = set()
    turn_counts = []

    for case in cases:
        spec = case.get("scenario_spec", {})
        gt = case.get("ground_truth", {})
        profile = spec.get("profile", {})

        profiles[profile.get("name", spec.get("difficulty", "none"))] += 1
        scenarios[spec.get("scenario_type", "unknown")] += 1
        resolutions[gt.get("resolution_type", "unknown")] += 1
        leakage[case.get("leakage_report", {}).get("status", "UNKNOWN")] += 1
        root_causes.add(spec.get("root_cause_id", "unknown"))
        turn_counts.append(len(case.get("transcript", {}).get("turns", [])))

        for tag in case.get("intent_tags", []):
            tags_counter[tag] += 1

    avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0

    lines = [f"{n} cases generated"]
    lines.append(f"Profiles:     {_format_counter(profiles)}")
    lines.append(f"Scenarios:    {_format_counter(scenarios)}")
    lines.append(f"Resolutions:  {_format_counter(resolutions)}")
    lines.append(f"Leakage:      {_format_counter(leakage)}")
    if tags_counter:
        lines.append(f"Intent tags:  {_format_counter(tags_counter)}")
    lines.append(f"Root causes:  {len(root_causes)} unique")
    lines.append(f"Avg turns:    {avg_turns:.1f}")

    report = "\n".join(lines)
    print(report)
    return report


def _format_counter(counter: Counter) -> str:
    parts = [f"{count} {key}" for key, count in counter.most_common()]
    return ", ".join(parts)
