from __future__ import annotations

from typing import Any


def build_consumer_summary(spec: dict[str, Any], transcript: dict[str, Any]) -> dict[str, Any]:
    summary = transcript.get("summary") or _fallback_summary(spec)
    return {
        "summary": summary,
        "scenario_type": spec["scenario_type"],
        "customer_role": spec["customer_persona"]["role"],
        "customer_mood": spec["customer_persona"]["mood"],
        "agent_quality": spec["agent_quality"],
        "difficulty": spec["difficulty"],
        "resolution_type": spec["resolution_type"],
    }


def build_exposure_marker(spec: dict[str, Any], transcript: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(turn.get("text", "") for turn in transcript.get("turns", [])).lower()
    categories = _scenario_categories(spec["scenario_type"])

    if any(term in text for term in ["admin", "user", "customer", "email", "domain", "workspace"]):
        categories.add("simulated_account_context")
    if any(term in text for term in ["billing", "invoice", "plan", "seat", "subscription", "payment"]):
        categories.add("simulated_billing_context")
    if any(term in text for term in ["sso", "oauth", "scim", "permission", "role", "identity"]):
        categories.add("simulated_admin_security_context")
    if any(term in text for term in ["deadline", "executive", "go live", "rollout"]):
        categories.add("simulated_business_impact")

    sensitivity = "low"
    if "simulated_admin_security_context" in categories or "simulated_billing_context" in categories:
        sensitivity = "medium"

    return {
        "sensitivity_level": sensitivity,
        "categories": sorted(categories),
        "contains_real_pii": False,
        "synthetic_only": True,
        "handling_note": "Synthetic fixture data. Safe for local evaluation, but treat as customer-like operational content in logs and demos.",
    }


def _scenario_categories(scenario_type: str) -> set[str]:
    return {
        "permissions_access": {"simulated_admin_security_context"},
        "onboarding_migration": {"simulated_operational_migration_context"},
        "workspace_setup": {"simulated_admin_setup_context"},
        "integrations_data_sync": {"simulated_integration_context"},
        "billing_plan_entitlement": {"simulated_billing_context"},
        "b2c_subscription_billing": {"simulated_b2c_billing_context"},
    }.get(scenario_type, {"simulated_b2b_support_context"})


def _fallback_summary(spec: dict[str, Any]) -> str:
    scenario = spec["scenario_type"].replace("_", " ")
    return f"Synthetic {scenario} support call with delayed evidence and competing operational hypotheses."
