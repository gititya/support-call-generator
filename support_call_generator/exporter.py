from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import shutil
from pathlib import Path

from support_call_generator.storage import CASES_DIR, load_case, list_cases


EXPORT_DIR = Path("exports")
EXPORT_BUNDLES = ("transcripts_only", "review_pack", "eval_pack")
EXPORT_BUNDLE_DESCRIPTIONS = {
    "transcripts_only": "Only transcript Markdown/JSON plus manifest and review index.",
    "review_pack": "Transcripts plus safe review metadata: summaries, exposure markers, manifest, and review index.",
    "eval_pack": "Review pack plus evaluator-only answer keys, expected timeline, and leakage report.",
}


def export_reviewed(
    cases_dir: Path = CASES_DIR,
    export_dir: Path = EXPORT_DIR,
    status: str = "accepted",
    bundle: str = "eval_pack",
) -> dict[str, int]:
    if bundle not in EXPORT_BUNDLES:
        raise ValueError(f"Unknown bundle '{bundle}'. Expected one of: {', '.join(EXPORT_BUNDLES)}")

    transcript_dir = export_dir / "transcripts"
    truth_dir = export_dir / "ground_truth"
    metadata_dir = export_dir / "metadata"
    if transcript_dir.exists():
        shutil.rmtree(transcript_dir)
    if truth_dir.exists():
        shutil.rmtree(truth_dir)
    if metadata_dir.exists():
        shutil.rmtree(metadata_dir)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    if bundle == "eval_pack":
        truth_dir.mkdir(parents=True, exist_ok=True)
    if bundle in {"review_pack", "eval_pack"}:
        metadata_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    manifest_cases: list[dict[str, str]] = []
    exported = 0

    for summary in list_cases(cases_dir):
        if status != "all" and summary["status"] != status:
            continue

        case = load_case(summary["case_id"], cases_dir)
        case_id = case["case_id"]
        source_dir = cases_dir / case_id

        shutil.copyfile(source_dir / "transcript.json", transcript_dir / f"{case_id}.json")
        shutil.copyfile(source_dir / "transcript.md", transcript_dir / f"{case_id}.md")
        if bundle == "eval_pack":
            shutil.copyfile(source_dir / "ground_truth.json", truth_dir / f"{case_id}.ground_truth.json")
            shutil.copyfile(source_dir / "expected_timeline.json", truth_dir / f"{case_id}.expected_timeline.json")
            leakage_path = source_dir / "leakage_report.json"
            if leakage_path.exists():
                shutil.copyfile(leakage_path, truth_dir / f"{case_id}.leakage_report.json")
        if bundle in {"review_pack", "eval_pack"}:
            summary_path = source_dir / "consumer_summary.json"
            if summary_path.exists():
                shutil.copyfile(summary_path, metadata_dir / f"{case_id}.consumer_summary.json")
            exposure_path = source_dir / "exposure_marker.json"
            if exposure_path.exists():
                shutil.copyfile(exposure_path, metadata_dir / f"{case_id}.exposure_marker.json")

        spec = case["scenario_spec"]
        review = case["review"]
        rows.append(
            {
                "case_id": case_id,
                "status": review["status"],
                "scenario_type": spec["scenario_type"],
                "customer_mood": spec["customer_persona"]["mood"],
                "customer_clarity": spec["customer_persona"]["clarity"],
                "customer_patience": spec["customer_persona"]["patience"],
                "technical_skill": spec["customer_persona"]["technical_skill"],
                "agent_quality": spec["agent_quality"],
                "difficulty": case["ground_truth"].get("difficulty_metadata", {}).get("difficulty", ""),
                "resolution_type": case["ground_truth"].get("resolution_type", ""),
                "root_cause_category": case["ground_truth"].get("root_cause_category", ""),
                "leakage_status": case["leakage_report"]["status"],
                "sensitivity_level": case.get("exposure_marker", {}).get("sensitivity_level", ""),
                "escalation_risk": spec["escalation_risk"],
                "model_name": review.get("model_name", ""),
                "generation_mode": review.get("generation_mode", ""),
                "notes": review.get("notes", ""),
            }
        )
        manifest_cases.append(
            {
                "case_id": case_id,
                "status": review["status"],
                "scenario_type": spec["scenario_type"],
                "difficulty": case["ground_truth"].get("difficulty_metadata", {}).get("difficulty", ""),
                "resolution_type": case["ground_truth"].get("resolution_type", ""),
                "leakage_status": case["leakage_report"]["status"],
                "transcript_json": f"transcripts/{case_id}.json",
                "transcript_markdown": f"transcripts/{case_id}.md",
                **_metadata_manifest_paths(case_id, bundle),
            }
        )
        exported += 1

    _write_index(export_dir / "review_index.csv", rows)
    _write_manifest(export_dir / "manifest.json", status, bundle, manifest_cases)
    return {"exported": exported}


def _write_index(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "case_id",
        "status",
        "scenario_type",
        "customer_mood",
        "customer_clarity",
        "customer_patience",
        "technical_skill",
        "agent_quality",
        "difficulty",
        "resolution_type",
        "root_cause_category",
        "leakage_status",
        "sensitivity_level",
        "escalation_risk",
        "model_name",
        "generation_mode",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _metadata_manifest_paths(case_id: str, bundle: str) -> dict[str, str]:
    if bundle not in {"review_pack", "eval_pack"}:
        return {}
    return {
        "consumer_summary": f"metadata/{case_id}.consumer_summary.json",
        "exposure_marker": f"metadata/{case_id}.exposure_marker.json",
    }


def _write_manifest(path: Path, status: str, bundle: str, cases: list[dict[str, str]]) -> None:
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_filter": status,
        "bundle": bundle,
        "case_count": len(cases),
        "boundary": "Transcript-only manifest for copilot/main-app consumption. Hidden ground truth is intentionally excluded.",
        "cases": cases,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
