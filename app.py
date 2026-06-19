from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import random
import subprocess

import streamlit as st

from support_call_generator.export_realtime import export_realtime_support
from support_call_generator.exporter import EXPORT_BUNDLES, export_reviewed
from support_call_generator.generator import generate_call
from support_call_generator.profiles import PROFILE_NAMES
from support_call_generator.scenarios import SCENARIO_TYPES
from support_call_generator.storage import (
    CASES_DIR,
    list_cases,
    load_case,
    save_case,
    update_review,
)


st.set_page_config(page_title="Support Call Generator", layout="wide")

st.title("Support Call Generator")


def default_cases_dir() -> Path:
    runs_dir = Path("data/llm_runs")
    if runs_dir.exists():
        runs = [path for path in runs_dir.iterdir() if path.is_dir()]
        if runs:
            return max(runs, key=lambda path: path.stat().st_mtime)
    return CASES_DIR


def _key_from_keychain(env_var: str, keychain_services: list[str]) -> str | None:
    if os.getenv(env_var):
        return os.getenv(env_var)
    for service in keychain_services:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "aditya", "-s", service, "-w"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def openai_key_from_keychain() -> str | None:
    return _key_from_keychain("OPENAI_API_KEY", ["OpenAI:voice"])


def anthropic_key_from_keychain() -> str | None:
    return _key_from_keychain("ANTHROPIC_API_KEY", ["Anthropic:api"])


if "cases_dir" not in st.session_state:
    st.session_state["cases_dir"] = str(default_cases_dir())
if "pending_cases_dir" in st.session_state:
    st.session_state["cases_dir"] = st.session_state.pop("pending_cases_dir")

cases_dir = Path(st.sidebar.text_input("Cases directory", key="cases_dir"))

st.sidebar.subheader("Generate")
generation_scenario = st.sidebar.selectbox("New call scenario", ["random", *SCENARIO_TYPES])
generation_profile = st.sidebar.selectbox("Difficulty profile", ["none", *PROFILE_NAMES])
generation_count = st.sidebar.number_input("Calls to generate", min_value=1, max_value=50, value=1, step=1)

if st.sidebar.button("Start fresh run", use_container_width=True):
    fresh_dir = Path("data/llm_runs") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fresh_dir.mkdir(parents=True, exist_ok=True)
    st.session_state["pending_cases_dir"] = str(fresh_dir)
    st.rerun()

generation_provider = st.sidebar.selectbox("LLM provider", ["openai", "anthropic"])

if st.sidebar.button("Generate", type="primary", use_container_width=True):
    if generation_provider == "anthropic":
        api_key = anthropic_key_from_keychain()
        if not api_key:
            st.sidebar.error("Anthropic key unavailable. Set ANTHROPIC_API_KEY or add Keychain service: Anthropic:api.")
        else:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            os.environ["SCG_PROVIDER"] = "anthropic"
    else:
        api_key = openai_key_from_keychain()
        if not api_key:
            st.sidebar.error("OpenAI key unavailable. Expected Keychain service: OpenAI:voice.")
        else:
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["SCG_PROVIDER"] = "openai"
    if api_key:
        selected_profile = generation_profile if generation_profile != "none" else None
        generated = []
        with st.spinner(f"Generating {generation_count} with {generation_provider}..."):
            for _ in range(int(generation_count)):
                scenario = generation_scenario if generation_scenario != "random" else random.choice(SCENARIO_TYPES)
                case = generate_call(scenario_type=scenario, use_llm=True, profile=selected_profile)
                save_case(case, cases_dir=cases_dir)
                generated.append(case["case_id"])
        st.toast(f"Generated {len(generated)} call{'s' if len(generated) != 1 else ''}")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Export")
export_bundle = st.sidebar.selectbox(
    "Bundle",
    ["review_pack", "transcripts_only", "eval_pack", "process_fixture"],
    help="Review pack is the best default for sharing generated calls without exposing hidden truth.",
)
export_status = st.sidebar.selectbox("Export status", ["accepted", "all", "draft", "rejected"])
export_dir = Path(st.sidebar.text_input("Export directory", value="exports/latest"))
if st.sidebar.button("Export bundle", use_container_width=True):
    if export_bundle == "process_fixture":
        result = export_realtime_support(cases_dir=cases_dir, export_dir=export_dir, status=export_status)
    else:
        result = export_reviewed(cases_dir=cases_dir, export_dir=export_dir, status=export_status, bundle=export_bundle)
    st.sidebar.success(f"Exported {result['exported']} cases to {export_dir}")

st.sidebar.divider()
st.sidebar.subheader("Browse generated calls")
st.sidebar.caption("All generated calls live in the selected cases directory. Use the filters below, then choose a case from the dropdown.")

scenario_filter = st.sidebar.selectbox("Scenario filter", ["all", *SCENARIO_TYPES])
status_filter = st.sidebar.selectbox("Review status filter", ["all", "draft", "accepted", "rejected"])
agent_filter = st.sidebar.selectbox("Agent quality filter", ["all", "good", "average", "confused", "overly_rigid"])

cases = list_cases(cases_dir)

filtered = []
for summary in cases:
    if scenario_filter != "all" and summary["scenario_type"] != scenario_filter:
        continue
    if status_filter != "all" and summary["status"] != status_filter:
        continue
    if agent_filter != "all" and summary["agent_quality"] != agent_filter:
        continue
    filtered.append(summary)

st.sidebar.metric("Generated calls", len(cases))
st.sidebar.caption(f"{len(filtered)} calls match the current filters")

st.caption(f"Viewing generated calls from `{cases_dir}`")

if not filtered:
    if cases:
        st.info("Generated calls exist, but none match the current filters. Set filters to all to view everything.")
    else:
        st.info("No generated calls yet. Use Generate call in the sidebar to create one.")
    st.stop()

with st.expander("All generated calls", expanded=True):
    st.dataframe(
        filtered,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "case_id",
            "status",
            "scenario_type",
            "customer_mood",
            "agent_quality",
            "difficulty",
            "resolution_type",
            "leakage_status",
            "generation_mode",
            "model_name",
        ],
    )

case_id = st.sidebar.selectbox(
    "Open call",
    [case["case_id"] for case in filtered],
    format_func=lambda item: f"{item} · {next(c['scenario_type'] for c in filtered if c['case_id'] == item)}",
)

case = load_case(case_id, cases_dir=cases_dir)

spec = case["scenario_spec"]
review = case["review"]
truth = case["ground_truth"]
leakage = case.get("leakage_report", {"status": "UNKNOWN", "failures": [], "warnings": []})
difficulty_metadata = truth.get("difficulty_metadata", {"difficulty": "unknown", "ambiguity_score": "n/a"})
has_current_metadata = "difficulty_metadata" in truth and leakage.get("status") != "UNKNOWN"

left, right = st.columns([0.65, 0.35], gap="large")

intent_tags = case.get("intent_tags", [])
context_events = case.get("context_events", [])
expected_by_turn = case.get("expected_by_turn", [])
profile_info = spec.get("profile", {})

with left:
    st.subheader(case_id)
    caption_parts = [
        f"{spec['scenario_type']} · {spec['customer_persona']['mood']} customer",
        f"{spec['customer_persona']['technical_skill']} technical skill",
        f"{spec['agent_quality']} agent · {review['status']}",
    ]
    if profile_info:
        caption_parts.insert(0, f"**{profile_info.get('name', '')}** profile")
    st.caption(" · ".join(caption_parts))
    if intent_tags:
        st.markdown(" ".join(f"`{tag}`" for tag in intent_tags))
    badge_cols = st.columns(4)
    badge_cols[0].metric("Difficulty", difficulty_metadata.get("difficulty", "unknown"))
    badge_cols[1].metric("Ambiguity", difficulty_metadata.get("ambiguity_score", "n/a"))
    badge_cols[2].metric("Resolution", truth.get("resolution_type", "unknown"))
    badge_cols[3].metric("Leakage", leakage.get("status", "UNKNOWN"))
    if not has_current_metadata:
        st.info("This call was generated before the difficulty/resolution/leakage metadata upgrade. Regenerate it or start a fresh run to see current metadata.")
    st.markdown(case["transcript_md"])

with right:
    st.subheader("Review")
    notes = st.text_area("Notes", review.get("notes", ""), height=100)

    accept, reject, draft = st.columns(3)
    with accept:
        if st.button("Accept", use_container_width=True):
            update_review(case_id, "accepted", notes, cases_dir=cases_dir)
            st.rerun()
    with reject:
        if st.button("Reject", use_container_width=True):
            update_review(case_id, "rejected", notes, cases_dir=cases_dir)
            st.rerun()
    with draft:
        if st.button("Draft", use_container_width=True):
            update_review(case_id, "draft", notes, cases_dir=cases_dir)
            st.rerun()

    if st.button("Regenerate", use_container_width=True):
        new_case = generate_call(
            scenario_type=spec["scenario_type"],
            seed=random.randint(1, 999_999_999),
            case_id=case_id,
        )
        new_case["review"]["regeneration_count"] = review.get("regeneration_count", 0) + 1
        new_case["review"]["notes"] = notes
        save_case(new_case, cases_dir=cases_dir)
        st.rerun()

    show_truth = st.toggle("Show hidden truth", value=False)
    with st.expander("Why this call is difficult", expanded=False):
        st.write("Misleading clues")
        for item in truth.get("misleading_evidence", []):
            st.write(f"- {item}")
        st.write("Delayed clues")
        for item in truth.get("late_reveal_facts", []):
            st.write(f"- {item}")
        st.write("Contradictory evidence")
        for item in truth.get("conflicting_observations", []):
            st.write(f"- {item}")
        st.write("Expected wrong paths")
        for item in truth.get("false_leads", []):
            st.write(f"- {item}")
        if leakage.get("warnings"):
            st.write("Leakage warnings")
            for item in leakage.get("warnings", []):
                st.write(f"- {item}")
    if context_events:
        with st.expander(f"Context Events ({len(context_events)})", expanded=False):
            for event in context_events:
                icon = ""
                if event.get("reveals_final_cause"):
                    icon = " [REVEALS CAUSE]"
                elif event.get("is_irrelevant"):
                    icon = " [IRRELEVANT]"
                elif event.get("is_conflicting"):
                    icon = " [CONFLICTING]"
                st.markdown(f"**After turn {event['after_turn']}** — `{event['source']}`{icon}")
                st.write(event["description"])
                if event.get("facts"):
                    st.caption("Facts: " + ", ".join(event["facts"]))
                st.divider()

    if expected_by_turn:
        with st.expander(f"Expected State ({len(expected_by_turn)} turns)", expanded=False):
            for state in expected_by_turn:
                cause_badge = " **[final cause allowed]**" if state.get("final_cause_allowed") else ""
                st.markdown(f"**After turn {state['after_turn']}**{cause_badge}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if state.get("facts"):
                        st.caption("Facts: " + ", ".join(state["facts"]))
                    if state.get("unknowns"):
                        st.caption("Unknowns: " + ", ".join(state["unknowns"]))
                with col_b:
                    if state.get("candidate_branches"):
                        st.caption("Candidates: " + ", ".join(state["candidate_branches"]))
                    if state.get("ruled_out_branches"):
                        st.caption("Ruled out: " + ", ".join(state["ruled_out_branches"]))
                st.divider()

    if show_truth:
        st.subheader("Ground Truth")
        st.json(truth)
        st.subheader("Expected Timeline")
        st.json(case["expected_timeline"])
        st.subheader("Best Questions")
        for question in truth["best_diagnostic_questions"]:
            st.write(f"- {question}")
