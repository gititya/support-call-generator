from __future__ import annotations

import json
import tomllib

import support_call_generator as scg
from support_call_generator.exporter import export_reviewed
from support_call_generator.generator import generate_call
from support_call_generator.scenarios import SCENARIO_TYPES
from support_call_generator.storage import list_cases, save_case, update_review
from support_call_generator.validator import validate_case


def test_generate_one_for_each_scenario() -> None:
    for scenario in SCENARIO_TYPES:
        case = generate_call(scenario_type=scenario, seed=123, use_llm=False)
        result = validate_case(case)
        assert result.ok, result.errors
        assert case["scenario_spec"]["scenario_type"] == scenario
        assert case["ground_truth"]["actual_root_cause"]
        assert case["ground_truth"]["resolution_type"]
        assert case["ground_truth"]["confidence"] >= 0
        assert case["ground_truth"]["difficulty_metadata"]["difficulty"]
        assert case["ground_truth"]["misleading_evidence"]
        assert case["ground_truth"]["false_leads"]
        assert case["ground_truth"]["abandoned_troubleshooting_paths"]
        assert case["ground_truth"]["hypothesis_reversals"]
        assert case["ground_truth"]["conflicting_observations"]
        assert case["ground_truth"]["late_reveal_facts"]
        assert case["ground_truth"]["doctrine_adherence"]["leakage_controls"]
        assert case["ground_truth"]["why_difficult"]
        assert case["consumer_summary"]["summary"]
        assert case["consumer_summary"]["scenario_type"] == scenario
        assert case["exposure_marker"]["synthetic_only"] is True
        assert case["exposure_marker"]["sensitivity_level"] in {"low", "medium", "high"}
        assert case["leakage_report"]["status"] in {"PASS", "WARNING"}
        assert case["expected_timeline"]
        assert {entry["state"] for entry in case["expected_timeline"]} >= {
            "activate",
            "strengthen",
            "weaken",
            "discard",
            "confirm",
        }


def test_batch_has_unique_ids_and_variation() -> None:
    cases = [
        generate_call(scenario_type=SCENARIO_TYPES[index % len(SCENARIO_TYPES)], use_llm=False)
        for index in range(50)
    ]
    assert len({case["case_id"] for case in cases}) == 50
    assert {case["scenario_spec"]["scenario_type"] for case in cases} == set(SCENARIO_TYPES)
    assert len({case["scenario_spec"]["customer_persona"]["mood"] for case in cases}) > 1
    assert len({case["scenario_spec"]["agent_quality"] for case in cases}) > 1


def test_export_keeps_transcripts_separate_from_truth(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    case = generate_call(scenario_type="permissions_access", seed=456, use_llm=False)
    save_case(case, cases_dir=cases_dir)
    update_review(case["case_id"], "accepted", "usable", cases_dir=cases_dir)

    result = export_reviewed(cases_dir=cases_dir, export_dir=export_dir)

    assert result == {"exported": 1}
    assert (export_dir / "transcripts" / f"{case['case_id']}.json").exists()
    assert (export_dir / "transcripts" / f"{case['case_id']}.md").exists()
    assert (export_dir / "ground_truth" / f"{case['case_id']}.ground_truth.json").exists()
    assert (export_dir / "ground_truth" / f"{case['case_id']}.expected_timeline.json").exists()
    assert (export_dir / "ground_truth" / f"{case['case_id']}.leakage_report.json").exists()
    assert (export_dir / "metadata" / f"{case['case_id']}.consumer_summary.json").exists()
    assert (export_dir / "metadata" / f"{case['case_id']}.exposure_marker.json").exists()
    assert (export_dir / "review_index.csv").exists()
    assert (export_dir / "manifest.json").exists()

    transcript_export = json.loads((export_dir / "transcripts" / f"{case['case_id']}.json").read_text())
    assert "ground_truth" not in transcript_export
    assert "expected_timeline" not in transcript_export
    assert "scenario_spec" not in transcript_export

    manifest = json.loads((export_dir / "manifest.json").read_text())
    assert manifest["case_count"] == 1
    assert manifest["bundle"] == "eval_pack"
    assert manifest["cases"][0]["transcript_json"] == f"transcripts/{case['case_id']}.json"
    assert manifest["cases"][0]["exposure_marker"] == f"metadata/{case['case_id']}.exposure_marker.json"
    assert "ground_truth" not in json.dumps(manifest)
    assert "leakage_report" not in json.dumps(manifest)


def test_export_bundle_transcripts_only(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    case = generate_call(scenario_type="permissions_access", seed=456, use_llm=False)
    save_case(case, cases_dir=cases_dir)
    update_review(case["case_id"], "accepted", "usable", cases_dir=cases_dir)

    result = export_reviewed(cases_dir=cases_dir, export_dir=export_dir, bundle="transcripts_only")

    assert result == {"exported": 1}
    assert (export_dir / "transcripts" / f"{case['case_id']}.json").exists()
    assert (export_dir / "transcripts" / f"{case['case_id']}.md").exists()
    assert not (export_dir / "ground_truth").exists()
    assert not (export_dir / "metadata").exists()

    manifest = json.loads((export_dir / "manifest.json").read_text())
    assert manifest["bundle"] == "transcripts_only"
    assert "consumer_summary" not in manifest["cases"][0]


def test_export_bundle_review_pack(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    case = generate_call(scenario_type="permissions_access", seed=456, use_llm=False)
    save_case(case, cases_dir=cases_dir)
    update_review(case["case_id"], "accepted", "usable", cases_dir=cases_dir)

    result = export_reviewed(cases_dir=cases_dir, export_dir=export_dir, bundle="review_pack")

    assert result == {"exported": 1}
    assert (export_dir / "transcripts" / f"{case['case_id']}.json").exists()
    assert (export_dir / "metadata" / f"{case['case_id']}.consumer_summary.json").exists()
    assert (export_dir / "metadata" / f"{case['case_id']}.exposure_marker.json").exists()
    assert not (export_dir / "ground_truth").exists()

    manifest = json.loads((export_dir / "manifest.json").read_text())
    assert manifest["bundle"] == "review_pack"
    assert manifest["cases"][0]["consumer_summary"] == f"metadata/{case['case_id']}.consumer_summary.json"


def test_review_status_persists(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    case = generate_call(scenario_type="workspace_setup", seed=789, use_llm=False)
    save_case(case, cases_dir=cases_dir)

    update_review(case["case_id"], "rejected", "too obvious", cases_dir=cases_dir)

    summaries = list_cases(cases_dir)
    assert summaries[0]["status"] == "rejected"


def test_package_public_api_and_console_script() -> None:
    case = scg.generate_call(scenario_type="permissions_access", seed=123, use_llm=False)
    assert case["case_id"]
    assert "permissions_access" in scg.SCENARIO_TYPES
    assert "review_pack" in scg.EXPORT_BUNDLES

    pyproject = tomllib.loads(open("pyproject.toml", encoding="utf-8").read())
    assert pyproject["project"]["scripts"]["support-call-generator"] == "support_call_generator.cli:main"
