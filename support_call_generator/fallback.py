from __future__ import annotations

from typing import Any


def build_offline_payload(spec: dict[str, Any]) -> dict[str, Any]:
    persona = spec["customer_persona"]
    root_cause = spec["hidden_root_cause"]
    stressors = spec["stressors"]
    wrong_path = stressors["false_leads"][0]
    second_wrong_path = stressors["false_leads"][1]
    delayed_fact = spec["delayed_facts"][0]
    late_fact = stressors["late_reveal_facts"][0]
    conflicting_observation = stressors["conflicting_observations"][0]
    misleading_evidence = stressors["misleading_evidence"][0]
    issue_path = spec["issue_path"]

    customer_prefix = {
        "calm": "I need help with something odd.",
        "confused": "I'm not totally sure what's going on, but something broke.",
        "frustrated": "This is becoming a real blocker for us.",
        "anxious": "I'm worried we're going to miss our deadline.",
        "impatient": "I need a fast answer here.",
    }[persona["mood"]]

    agent_style = {
        "good": "Let's separate what we know from what we still need to verify.",
        "average": "Okay, I can check a few things with you.",
        "confused": "I think this may be a login thing, but let's see.",
        "overly_rigid": "I need to follow the standard checklist before we discuss escalation.",
    }[spec["agent_quality"]]

    turns = [
        {"turn": 1, "speaker": "customer", "text": f"{customer_prefix} {spec['known_facts'][0]}."},
        {"turn": 2, "speaker": "agent", "text": f"{agent_style} When did this first start?"},
        {"turn": 3, "speaker": "customer", "text": spec["known_facts"][1]},
        {"turn": 4, "speaker": "agent", "text": f"That points me toward {wrong_path}, but I want to keep this tentative. What changed right before the issue started?"},
        {"turn": 5, "speaker": "customer", "text": f"The confusing part is this: {misleading_evidence}"},
        {"turn": 6, "speaker": "agent", "text": f"Let's test {wrong_path} first. If that fits, we should see the same behavior on a known-good example."},
        {"turn": 7, "speaker": "customer", "text": f"We checked one example and it seemed to fit, but then another example did not. {conflicting_observation}"},
        {"turn": 8, "speaker": "agent", "text": f"That weakens {wrong_path}. I am going to abandon that path for now and check {second_wrong_path}."},
        {"turn": 9, "speaker": "customer", "text": f"{second_wrong_path} happened to us once before, so that sounds plausible, but the symptoms are not exactly the same."},
        {"turn": 10, "speaker": "agent", "text": f"Agreed. {second_wrong_path} is possible, but the evidence is mixed. I need a comparison between a working and blocked case."},
        {"turn": 11, "speaker": "customer", "text": f"One working case has the same visible setup. Also, {delayed_fact}."},
        {"turn": 12, "speaker": "agent", "text": "That reverses the direction. The visible setup may not be the control point. I want to inspect the shared configuration boundary."},
        {"turn": 13, "speaker": "customer", "text": f"I just got a note from someone else: {late_fact}. {spec['escalation_conditions'][0]}."},
        {"turn": 14, "speaker": "agent", "text": f"That late detail finally makes the actual path coherent. The likely root cause is: {root_cause}"},
        {"turn": 15, "speaker": "customer", "text": "So the earlier checks were not wasted, but they were pointing at the wrong control point?"},
        {"turn": 16, "speaker": "agent", "text": f"Correct. The earlier paths were plausible but abandoned after conflicting evidence. Final outcome: {spec['final_outcome']}"},
    ]

    return {
        "transcript": {
            "turns": turns,
            "summary": "Synthetic support interaction with misleading evidence, abandoned paths, conflicting observations, a hypothesis reversal, and a late root-cause reveal.",
        },
        "ground_truth": {
            "actual_root_cause": root_cause,
            "confidence": 0.92 if spec["resolution_type"] == "resolved" else 0.72,
            "resolution_type": spec["resolution_type"],
            "root_cause_category": spec["root_cause_category"],
            "difficulty_metadata": spec["difficulty_metadata"],
            "issue_path": issue_path,
            "key_evidence": [spec["known_facts"][1], delayed_fact],
            "wrong_paths": spec["wrong_paths"],
            "misleading_evidence": stressors["misleading_evidence"],
            "false_leads": stressors["false_leads"],
            "abandoned_troubleshooting_paths": stressors["abandoned_troubleshooting_paths"],
            "hypothesis_reversals": stressors["hypothesis_reversals"],
            "conflicting_observations": stressors["conflicting_observations"],
            "late_reveal_facts": stressors["late_reveal_facts"],
            "doctrine_adherence": {
                "uncertainty_pressure": "The call keeps multiple explanations alive before narrowing.",
                "information_asymmetry": "Customer, agent, and admin details arrive at different times.",
                "leakage_controls": [
                    "The customer does not state the hidden root cause directly.",
                    "Late facts explain the answer only after false leads are weakened.",
                    "The agent abandons plausible paths before confirming the answer.",
                ],
                "non_perfect_troubleshooting": "The agent tests two plausible wrong paths before the correct operational boundary becomes clear.",
            },
            "why_difficult": [
                "early evidence supports the wrong branch",
                "customer corrects the timeline after the agent has already tested a dead end",
                "the late fact changes the operational boundary",
            ],
            "escalation_timeline": [
                {"turn": 7, "moment": spec["escalation_conditions"][0], "type": "escalation"},
                {"turn": 10, "moment": "agent nearly overcommits to a weak path", "type": "missed_opportunity"},
            ],
            "escalation_trigger": spec["escalation_conditions"][0],
            "best_diagnostic_questions": [
                "Which users or records are affected, and what do they have in common?",
                "What changed immediately before the issue started?",
                "Can we compare one working example with one blocked example?",
                "Is this failing for a role, group, workspace, or integration boundary?",
                "What evidence would disprove the current leading hypothesis?",
            ],
            "final_outcome": spec["final_outcome"],
        },
        "expected_timeline": [
            {
                "turn": 1,
                "hypothesis": issue_path[0],
                "state": "activate",
                "confidence": 0.35,
                "evidence": [spec["known_facts"][0]],
            },
            {
                "turn": 4,
                "hypothesis": wrong_path,
                "state": "strengthen",
                "confidence": 0.55,
                "evidence": [misleading_evidence],
            },
            {
                "turn": 8,
                "hypothesis": wrong_path,
                "state": "discard",
                "confidence": 0.15,
                "evidence": [conflicting_observation],
            },
            {
                "turn": 10,
                "hypothesis": second_wrong_path,
                "state": "weaken",
                "confidence": 0.3,
                "evidence": ["comparison case does not fit the second false lead"],
            },
            {
                "turn": 12,
                "hypothesis": root_cause,
                "state": "activate",
                "confidence": 0.55,
                "evidence": [delayed_fact],
            },
            {
                "turn": 14,
                "hypothesis": root_cause,
                "state": "confirm",
                "confidence": 0.9,
                "evidence": [late_fact, spec["final_outcome"]],
            },
        ],
    }
