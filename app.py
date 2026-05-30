from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import random
import subprocess

import streamlit as st

from support_call_generator.generator import generate_call
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


def openai_key_from_keychain() -> str | None:
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_API_KEY")

    result = subprocess.run(
        ["security", "find-generic-password", "-s", "OPENAI_API_KEY", "-w"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


if "cases_dir" not in st.session_state:
    st.session_state["cases_dir"] = str(default_cases_dir())
if "pending_cases_dir" in st.session_state:
    st.session_state["cases_dir"] = st.session_state.pop("pending_cases_dir")

cases_dir = Path(st.sidebar.text_input("Cases directory", key="cases_dir"))

st.sidebar.subheader("Generate")
generation_scenario = st.sidebar.selectbox("New call scenario", ["random", *SCENARIO_TYPES])

if st.sidebar.button("Start fresh run", use_container_width=True):
    fresh_dir = Path("data/llm_runs") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fresh_dir.mkdir(parents=True, exist_ok=True)
    st.session_state["pending_cases_dir"] = str(fresh_dir)
    st.rerun()

if st.sidebar.button("Generate call", type="primary", use_container_width=True):
    scenario = generation_scenario if generation_scenario != "random" else random.choice(SCENARIO_TYPES)
    openai_key = openai_key_from_keychain()
    if not openai_key:
        st.sidebar.error("OpenAI key unavailable. Expected Keychain service: OPENAI_API_KEY.")
    else:
        os.environ["OPENAI_API_KEY"] = openai_key
        with st.spinner("Generating LLM call..."):
            case = generate_call(scenario_type=scenario, use_llm=True)
            save_case(case, cases_dir=cases_dir)
        st.toast(f"Generated {case['case_id']}")
        st.rerun()

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

with left:
    st.subheader(case_id)
    st.caption(
        f"{spec['scenario_type']} · {spec['customer_persona']['mood']} customer · "
        f"{spec['customer_persona']['technical_skill']} technical skill · "
        f"{spec['agent_quality']} agent · {review['status']}"
    )
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
    if show_truth:
        st.subheader("Ground Truth")
        st.json(truth)
        st.subheader("Expected Timeline")
        st.json(case["expected_timeline"])
        st.subheader("Best Questions")
        for question in truth["best_diagnostic_questions"]:
            st.write(f"- {question}")
