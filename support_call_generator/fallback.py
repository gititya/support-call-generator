from __future__ import annotations

from typing import Any


def build_offline_payload(spec: dict[str, Any]) -> dict[str, Any]:
    if spec["scenario_type"] == "b2c_subscription_billing":
        return _build_b2c_subscription_payload(spec)

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


def _build_b2c_subscription_payload(spec: dict[str, Any]) -> dict[str, Any]:
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
    seed = spec.get("expected_handoff_seed", {})
    charge = seed.get("charge", {})

    customer_prefix = {
        "confused": "I'm confused about a charge on my card.",
        "frustrated": "I'm really frustrated about this charge.",
        "anxious": "I'm worried my card may have been charged without permission.",
        "impatient": "I need a clear answer about this charge quickly.",
    }.get(persona["mood"], "I need help with a subscription charge.")

    agent_style = {
        "good": "I can help separate what is confirmed from what still needs review.",
        "average": "I can check the billing records with you.",
        "confused": "This might be a subscription renewal, but I need to verify that.",
        "overly_rigid": "I need to verify identity and charge details before discussing refund or fraud options.",
    }[spec["agent_quality"]]

    charge_line = (
        f"{charge.get('amount', 'the charge')} on {charge.get('date', 'the card statement')} "
        f"with descriptor {charge.get('descriptor', 'the subscription descriptor')}"
    )
    if charge.get("last4"):
        charge_line += f" on card ending {charge['last4']}"

    is_fraud_flagged = bool(seed.get("fraud_flagged")) or "fraud" in root_cause.lower() or "card-not-recognized" in root_cause.lower()
    final_agent_text = (
        "I am not going to confirm fraud from this chat. I will preserve the transaction details, note that the charge is unexplained on the verified account, and route this to the fraud/payments team."
        if is_fraud_flagged
        else f"Based on the evidence we have now, the likely billing explanation is: {root_cause}"
    )

    turns = [
        {"turn": 1, "speaker": "customer", "text": f"{customer_prefix} I see {charge_line}, and I don't recognize why it happened."},
        {"turn": 2, "speaker": "agent", "text": f"{agent_style} First I need to verify the account and the exact charge, then I can check refund or fraud routing policy."},
        {"turn": 3, "speaker": "customer", "text": spec["known_facts"][1]},
        {"turn": 4, "speaker": "agent", "text": f"That could fit {wrong_path}, but I don't want to assume. Is the card charge pending or posted?"},
        {"turn": 5, "speaker": "customer", "text": f"The confusing part is this: {misleading_evidence}"},
        {"turn": 6, "speaker": "agent", "text": f"Let's check {wrong_path} first. If that is right, the payment status and subscription history should line up."},
        {"turn": 7, "speaker": "customer", "text": f"I checked the banking app again and it is not as simple as I thought. {conflicting_observation}"},
        {"turn": 8, "speaker": "agent", "text": f"That weakens {wrong_path}. I am going to stop leaning on that and check {second_wrong_path}."},
        {"turn": 9, "speaker": "customer", "text": f"{second_wrong_path} sounds possible because another person in my house sometimes uses streaming apps, but nobody remembers buying this."},
        {"turn": 10, "speaker": "agent", "text": f"That is useful, but still not enough to decide. I need to compare the verified account, the card transaction, and subscription records."},
        {"turn": 11, "speaker": "customer", "text": f"I found one more detail: {delayed_fact}."},
        {"turn": 12, "speaker": "agent", "text": "That changes the direction. I need to treat the payment record and subscription record as separate checks before saying what happened."},
        {"turn": 13, "speaker": "customer", "text": f"I just noticed this too: {late_fact}. {spec['escalation_conditions'][0]}."},
        {"turn": 14, "speaker": "agent", "text": final_agent_text},
        {"turn": 15, "speaker": "customer", "text": "So you can document what you checked, but you can't promise a refund or call it fraud yet?"},
        {"turn": 16, "speaker": "agent", "text": f"Correct. I will include the charge, identity check, ruled-out paths, next step, and what we should not promise. Final outcome: {spec['final_outcome']}"},
    ]

    confidence = 0.45 if is_fraud_flagged else (0.92 if spec["resolution_type"] == "resolved" else 0.72)

    return {
        "transcript": {
            "turns": turns,
            "summary": "Synthetic B2C subscription billing dispute with misleading payment evidence, policy boundaries, and a late handoff decision.",
        },
        "ground_truth": {
            "actual_root_cause": root_cause,
            "confidence": confidence,
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
                "uncertainty_pressure": "The call keeps refund, billing, household, and fraud explanations separate until evidence narrows them.",
                "information_asymmetry": "The customer sees bank statement details while support sees identity, subscription, payment, and refund records at different times.",
                "leakage_controls": [
                    "The customer does not name the planted billing cause directly.",
                    "Late payment and subscription facts explain the answer only after false leads are weakened.",
                    "The agent preserves policy boundaries and avoids promising refund or fraud outcomes early.",
                ],
                "non_perfect_troubleshooting": "The agent tests two plausible consumer billing paths before the right support boundary becomes clear.",
            },
            "why_difficult": [
                "bank statement language can make pending, duplicate, and settled charges sound similar",
                "household account behavior creates a plausible false explanation",
                "fraud language must be handled without confirming fraud prematurely",
            ],
            "escalation_timeline": [
                {"turn": 7, "moment": spec["escalation_conditions"][0], "type": "escalation"},
                {"turn": 10, "moment": "agent nearly treats a weak billing hypothesis as enough", "type": "missed_opportunity"},
            ],
            "escalation_trigger": spec["escalation_conditions"][0],
            "best_diagnostic_questions": [
                "Can you confirm the charge amount, date, descriptor, and card last four?",
                "Is the charge pending or posted in the banking app?",
                "Which account email or household profile may have used the subscription?",
                "Do subscription records show a matching renewal, trial conversion, or plan change?",
                "What evidence would require fraud or payments escalation instead of normal refund handling?",
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
                "evidence": ["subscription and payment records need separate verification"],
            },
            {
                "turn": 12,
                "hypothesis": root_cause,
                "state": "activate",
                "confidence": 0.55 if not is_fraud_flagged else 0.35,
                "evidence": [delayed_fact],
            },
            {
                "turn": 14,
                "hypothesis": root_cause,
                "state": "confirm",
                "confidence": 0.9 if not is_fraud_flagged else 0.55,
                "evidence": [late_fact, spec["final_outcome"]],
            },
        ],
    }
