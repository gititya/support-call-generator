from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from support_call_generator.storage import CASES_DIR, list_cases, load_case


EXPORT_DIR = Path("exports")


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
        fixture_path = out_dir / f"{case['case_id']}.json"
        fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
        fixtures.append({"case_id": case["case_id"], "file": f"realtime_support/{case['case_id']}.json"})
        exported += 1

    manifest = {
        "schema_version": "support_call_generator.realtime_support.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_filter": status,
        "case_count": len(fixtures),
        "cases": fixtures,
    }
    (export_dir / "realtime_support_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    return {"exported": exported}


def _build_fixture(case: dict[str, Any]) -> dict[str, Any]:
    spec = case["scenario_spec"]
    gt = case["ground_truth"]
    profile = spec.get("profile", {})

    return {
        "schema_version": "support_call_generator.realtime_support.v1",
        "case_id": case["case_id"],
        "title": _build_title(case),
        "scenario": spec["scenario_type"],
        "difficulty_profile": profile.get("name", spec.get("difficulty", "unknown")),
        "transcript_turns": case["transcript"]["turns"],
        "context_events": case.get("context_events", []),
        "expected_by_turn": case.get("expected_by_turn", []),
        "final_cause": gt["actual_root_cause"],
        "resolution_type": gt["resolution_type"],
        "intent_tags": case.get("intent_tags", []),
    }


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
