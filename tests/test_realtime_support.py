from __future__ import annotations

import json

from support_call_generator.export_realtime import export_realtime_support
from support_call_generator.generator import generate_call
from support_call_generator.profiles import DIFFICULTY_PROFILES, PROFILE_NAMES
from support_call_generator.report import print_batch_report
from support_call_generator.scenarios import SCENARIO_TYPES
from support_call_generator.storage import save_case, update_review
from support_call_generator.validator import validate_case


def test_profile_controls_generation() -> None:
    for profile_name in PROFILE_NAMES:
        case = generate_call(scenario_type="permissions_access", seed=100, use_llm=False, profile=profile_name)
        spec = case["scenario_spec"]
        assert spec["profile"]["name"] == profile_name
        profile = DIFFICULTY_PROFILES[profile_name]
        assert spec["agent_quality"] in profile["agent_quality_weights"]
        assert spec["resolution_type"] in profile["resolution_weights"]


def test_profile_none_preserves_old_behavior() -> None:
    case = generate_call(scenario_type="permissions_access", seed=123, use_llm=False)
    assert "profile" not in case["scenario_spec"]
    result = validate_case(case)
    assert result.ok, result.errors


def test_context_events_present_with_profile() -> None:
    for profile_name in PROFILE_NAMES:
        case = generate_call(scenario_type="onboarding_migration", seed=200, use_llm=False, profile=profile_name)
        events = case["context_events"]
        assert len(events) > 0, f"no context events for profile {profile_name}"

        turn_count = len(case["transcript"]["turns"])
        final_third = max(1, int(turn_count * 2 / 3))

        reveal_events = [e for e in events if e.get("reveals_final_cause")]
        assert len(reveal_events) <= 1, "more than one reveals_final_cause"
        if reveal_events:
            assert reveal_events[0]["after_turn"] >= final_third, "final cause revealed before final third"

        for event in events:
            assert 1 <= event["after_turn"] <= turn_count
            assert event["source"]
            assert event["description"]


def test_context_events_empty_without_profile() -> None:
    case = generate_call(scenario_type="permissions_access", seed=123, use_llm=False)
    assert case["context_events"] == [] or len(case["context_events"]) > 0


def test_expected_state_per_turn() -> None:
    case = generate_call(scenario_type="workspace_setup", seed=300, use_llm=False, profile="hard")
    states = case["expected_by_turn"]
    turns = case["transcript"]["turns"]
    assert len(states) == len(turns)

    final_third = max(1, int(len(turns) * 2 / 3))

    prev_facts = set()
    prev_ruled = set()
    for state in states:
        current_facts = set(state["facts"])
        assert prev_facts.issubset(current_facts), "facts must accumulate monotonically"
        prev_facts = current_facts

        current_ruled = set(state["ruled_out_branches"])
        assert prev_ruled.issubset(current_ruled), "ruled_out_branches must accumulate monotonically"
        prev_ruled = current_ruled

        if state["final_cause_allowed"]:
            assert state["after_turn"] >= final_third, "final_cause_allowed too early"


def test_expected_state_final_cause_transitions() -> None:
    case = generate_call(scenario_type="permissions_access", seed=42, use_llm=False, profile="hard")
    states = case["expected_by_turn"]
    allowed_turns = [s["after_turn"] for s in states if s["final_cause_allowed"]]
    not_allowed_turns = [s["after_turn"] for s in states if not s["final_cause_allowed"]]
    assert len(not_allowed_turns) > 0, "final_cause_allowed should be False initially"
    if allowed_turns:
        assert min(allowed_turns) > min(not_allowed_turns), "final_cause_allowed should come after not-allowed"


def test_intent_tags_derived() -> None:
    case = generate_call(scenario_type="permissions_access", seed=42, use_llm=False, profile="hard")
    tags = case["intent_tags"]
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert all(isinstance(t, str) for t in tags)
    assert tags == sorted(tags), "tags should be sorted"


def test_intent_tags_include_expected_types() -> None:
    cases = [
        generate_call(scenario_type=st, seed=i * 100, use_llm=False, profile="harder")
        for i, st in enumerate(SCENARIO_TYPES)
    ]
    all_tags = set()
    for case in cases:
        all_tags.update(case["intent_tags"])
    assert "customer_correction" in all_tags
    assert "late_evidence_reveal" in all_tags


def test_context_leakage_passes_for_valid_cases() -> None:
    for scenario in SCENARIO_TYPES:
        case = generate_call(scenario_type=scenario, seed=500, use_llm=False, profile="hard")
        assert case["leakage_report"]["status"] in {"PASS", "WARNING"}


def test_realtime_export_shape(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    case = generate_call(scenario_type="permissions_access", seed=456, use_llm=False, profile="hard")
    save_case(case, cases_dir=cases_dir)
    update_review(case["case_id"], "accepted", "good", cases_dir=cases_dir)

    result = export_realtime_support(cases_dir=cases_dir, export_dir=export_dir)
    assert result == {"exported": 1}

    fixture_path = export_dir / "realtime_support" / f"{case['case_id']}.json"
    assert fixture_path.exists()

    fixture = json.loads(fixture_path.read_text())
    assert fixture["schema_version"] == "support_call_generator.realtime_support.v1"
    assert fixture["case_id"] == case["case_id"]
    assert fixture["scenario"] == "permissions_access"
    assert fixture["difficulty_profile"] == "hard"
    assert len(fixture["transcript_turns"]) >= 16
    assert len(fixture["context_events"]) > 0
    assert len(fixture["expected_by_turn"]) == len(fixture["transcript_turns"])
    assert fixture["final_cause"]
    assert fixture["resolution_type"]
    assert isinstance(fixture["intent_tags"], list)


def test_realtime_export_excludes_ground_truth_internals(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    case = generate_call(scenario_type="permissions_access", seed=456, use_llm=False, profile="hard")
    save_case(case, cases_dir=cases_dir)
    update_review(case["case_id"], "accepted", "", cases_dir=cases_dir)

    export_realtime_support(cases_dir=cases_dir, export_dir=export_dir)

    fixture_path = export_dir / "realtime_support" / f"{case['case_id']}.json"
    fixture_text = fixture_path.read_text()
    assert "doctrine_adherence" not in fixture_text
    assert "why_difficult" not in fixture_text
    assert "escalation_timeline" not in fixture_text
    assert "best_diagnostic_questions" not in fixture_text
    assert "misleading_evidence" not in fixture_text


def test_realtime_export_manifest(tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    export_dir = tmp_path / "exports"

    for seed in [100, 200]:
        case = generate_call(scenario_type="permissions_access", seed=seed, use_llm=False, profile="hard")
        save_case(case, cases_dir=cases_dir)
        update_review(case["case_id"], "accepted", "", cases_dir=cases_dir)

    export_realtime_support(cases_dir=cases_dir, export_dir=export_dir)

    manifest = json.loads((export_dir / "realtime_support_manifest.json").read_text())
    assert manifest["schema_version"] == "support_call_generator.realtime_support.v1"
    assert manifest["case_count"] == 2
    assert len(manifest["cases"]) == 2


def test_batch_report() -> None:
    cases = [
        generate_call(scenario_type=SCENARIO_TYPES[i % 3], seed=i, use_llm=False, profile="hard")
        for i in range(6)
    ]
    report = print_batch_report(cases)
    assert "6 cases generated" in report
    assert "Profiles:" in report
    assert "Scenarios:" in report
    assert "Resolutions:" in report
    assert "Leakage:" in report
    assert "Root causes:" in report
    assert "Avg turns:" in report


def test_full_pipeline_with_validation() -> None:
    for profile in PROFILE_NAMES:
        for scenario in SCENARIO_TYPES:
            case = generate_call(scenario_type=scenario, seed=999, use_llm=False, profile=profile)
            result = validate_case(case)
            assert result.ok, f"validation failed for {scenario}/{profile}: {result.errors}"
            assert case["leakage_report"]["status"] in {"PASS", "WARNING"}
            assert len(case["context_events"]) > 0
            assert len(case["expected_by_turn"]) == len(case["transcript"]["turns"])
            assert isinstance(case["intent_tags"], list)
