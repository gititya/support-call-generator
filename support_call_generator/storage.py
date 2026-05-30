from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


CASES_DIR = Path("data/cases")


def save_case(case: dict[str, Any], cases_dir: Path = CASES_DIR) -> Path:
    case_dir = cases_dir / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)

    _write_json(case_dir / "scenario_spec.json", case["scenario_spec"])
    _write_json(case_dir / "transcript.json", case["transcript"])
    (case_dir / "transcript.md").write_text(case["transcript_md"], encoding="utf-8")
    _write_json(case_dir / "ground_truth.json", case["ground_truth"])
    _write_json(case_dir / "expected_timeline.json", case["expected_timeline"])
    _write_json(case_dir / "leakage_report.json", case["leakage_report"])
    _write_json(case_dir / "review.json", case["review"])

    return case_dir


def load_case(case_id: str, cases_dir: Path = CASES_DIR) -> dict[str, Any]:
    case_dir = cases_dir / case_id
    leakage_path = case_dir / "leakage_report.json"
    return {
        "case_id": case_id,
        "scenario_spec": _read_json(case_dir / "scenario_spec.json"),
        "transcript": _read_json(case_dir / "transcript.json"),
        "transcript_md": (case_dir / "transcript.md").read_text(encoding="utf-8"),
        "ground_truth": _read_json(case_dir / "ground_truth.json"),
        "expected_timeline": _read_json(case_dir / "expected_timeline.json"),
        "leakage_report": _read_json(leakage_path) if leakage_path.exists() else {"status": "UNKNOWN", "failures": [], "warnings": []},
        "review": _read_json(case_dir / "review.json"),
    }


def list_cases(cases_dir: Path = CASES_DIR) -> list[dict[str, Any]]:
    if not cases_dir.exists():
        return []

    summaries: list[dict[str, Any]] = []
    for case_dir in sorted(path for path in cases_dir.iterdir() if path.is_dir()):
        try:
            spec = _read_json(case_dir / "scenario_spec.json")
            review = _read_json(case_dir / "review.json")
            truth = _read_json(case_dir / "ground_truth.json")
        except FileNotFoundError:
            continue
        summaries.append(
            {
                "case_id": case_dir.name,
                "scenario_type": spec["scenario_type"],
                "customer_mood": spec["customer_persona"]["mood"],
                "agent_quality": spec["agent_quality"],
                "difficulty": truth.get("difficulty_metadata", {}).get("difficulty", spec.get("difficulty", "")),
                "resolution_type": truth.get("resolution_type", spec.get("resolution_type", "")),
                "root_cause_category": truth.get("root_cause_category", spec.get("root_cause_category", "")),
                "leakage_status": review.get("leakage_status", ""),
                "status": review["status"],
                "model_name": review.get("model_name", ""),
                "seed": review.get("seed", ""),
            }
        )
    return summaries


def update_review(case_id: str, status: str, notes: str, cases_dir: Path = CASES_DIR) -> None:
    if status not in {"draft", "accepted", "rejected"}:
        raise ValueError("status must be draft, accepted, or rejected")

    review_path = cases_dir / case_id / "review.json"
    review = _read_json(review_path)
    review["status"] = status
    review["notes"] = notes
    review["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    _write_json(review_path, review)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
