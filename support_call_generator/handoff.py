from __future__ import annotations

from typing import Any


B2C_SCENARIO = "b2c_subscription_billing"
FRAUD_FLAG = "unexplained / fraud-flagged"


def ensure_expected_handoff(spec: dict[str, Any], ground_truth: dict[str, Any]) -> None:
    if spec.get("scenario_type") != B2C_SCENARIO:
        return
    if isinstance(ground_truth.get("expected_handoff"), dict):
        return
    ground_truth["expected_handoff"] = build_expected_handoff(spec, ground_truth)


def build_expected_handoff(spec: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    seed = dict(spec.get("expected_handoff_seed") or {})
    charge = dict(seed.get("charge") or {})
    resolution = ground_truth.get("resolution_type", spec.get("resolution_type", ""))
    root_text = str(ground_truth.get("actual_root_cause", spec.get("hidden_root_cause", ""))).lower()
    fraud_flagged = bool(seed.get("fraud_flagged")) or "fraud" in root_text or "card-not-recognized" in root_text
    likely_cause = FRAUD_FLAG if fraud_flagged else ground_truth.get("actual_root_cause", spec.get("hidden_root_cause", ""))
    confidence = "low" if fraud_flagged else _confidence_label(float(ground_truth.get("confidence", 0.0)))

    handoff: dict[str, Any] = {
        "ai_to_human": {
            "customer_account_identity": seed.get("customer_identity", "Verified subscriber identity and account ownership."),
            "account_id": seed.get("account_id", ""),
            "subscription_id": seed.get("subscription_id", ""),
            "charge": {
                "amount": charge.get("amount", ""),
                "date": charge.get("date", ""),
                "descriptor": charge.get("descriptor", ""),
                "last4": charge.get("last4", ""),
                "transaction_id": charge.get("transaction_id", ""),
            },
            "customer_claim": seed.get("customer_claim", "Customer disputes a subscription charge."),
            "desired_outcome": seed.get("desired_outcome", "Explain the charge and apply the correct support policy."),
            "checks_with_results": list(seed.get("checks", [])),
            "ruled_out_branches": list(seed.get("ruled_out", spec.get("wrong_paths", []))),
            "likely_cause": likely_cause,
            "confidence": confidence,
            "risk_urgency": seed.get("risk", spec.get("escalation_conditions", [""])[0]),
            "next_step": seed.get("next_step", "Continue billing review under policy boundaries."),
            "what_not_to_promise": seed.get("what_not_to_promise", "Do not promise refund timing before policy or fraud review."),
        }
    }

    if resolution == "escalated":
        handoff["human_to_engineering"] = {
            "account_id": seed.get("account_id", ""),
            "subscription_id": seed.get("subscription_id", ""),
            "charges": [handoff["ai_to_human"]["charge"]],
            "system_discrepancy": seed.get(
                "engineering_discrepancy",
                "Billing or payment records require payments-engineering review before support can close the dispute.",
            ),
            "support_ruled_out": list(seed.get("ruled_out", [])),
            "evidence_handles": list(seed.get("evidence_handles", [])),
            "impact_urgency": seed.get("risk", ""),
            "specific_ask": seed.get("engineering_ask", "Review the payment/subscription discrepancy and advise the corrective billing action."),
        }

    return handoff


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"
