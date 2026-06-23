from __future__ import annotations

import random
from typing import Any


SCENARIO_TYPES = [
    "permissions_access",
    "onboarding_migration",
    "workspace_setup",
    "integrations_data_sync",
    "billing_plan_entitlement",
    "b2c_subscription_billing",
]

CUSTOMER_MOODS = ["calm", "confused", "frustrated", "anxious", "impatient"]
CUSTOMER_CLARITY = ["clear", "partial", "scattered"]
CUSTOMER_PATIENCE = ["high", "medium", "low"]
TECHNICAL_SKILL = ["low", "medium", "high"]
AGENT_QUALITY = ["good", "average", "confused", "overly_rigid"]
AMBIGUITY_LEVELS = ["low", "medium", "high"]
DELAYED_FACT_TIMING = ["early", "middle", "late"]
ESCALATION_RISK = ["low", "medium", "high"]
DIFFICULTIES = ["easy", "medium", "hard"]
RESOLUTION_TYPES = ["resolved", "probable_cause", "escalated", "handoff", "unresolved"]

AGENT_QUALITY_WEIGHTS = {
    "good": 20,
    "average": 40,
    "overly_rigid": 25,
    "confused": 15,
}

RESOLUTION_WEIGHTS = {
    "resolved": 20,
    "probable_cause": 40,
    "escalated": 25,
    "handoff": 10,
    "unresolved": 5,
}

ROOT_CAUSE_CATALOG = {
    "permissions_access": [
        "missing group role after migration",
        "SSO group mismatch after department change",
        "SCIM sync delay",
        "stale entitlement cache",
        "inherited role conflict",
        "direct assignment conflict",
        "disabled role mapping rule",
        "manually retained user no longer entitled",
    ],
    "onboarding_migration": [
        "archived team export filter",
        "custom legacy role mapping",
        "ownership translation failure",
        "duplicate merge",
        "environment mismatch",
        "inactive owner exclusion",
        "field mapping fallback",
        "partial export scope",
    ],
    "workspace_setup": [
        "DNS record on wrong host",
        "declined OAuth permission",
        "missing integration write scope",
        "admin approval dependency",
        "connector authorization failure",
        "provisioning timeout",
        "template dependency failure",
        "region mismatch",
    ],
    "integrations_data_sync": [
        "expired OAuth refresh token",
        "webhook retry exhaustion",
        "external ID mapping conflict",
        "CRM field type mismatch",
        "rate limit backoff delay",
        "duplicate record merge rule",
        "partial sync cursor reset",
        "stale integration permission scope",
    ],
    "billing_plan_entitlement": [
        "seat limit reached",
        "feature gate missing after plan change",
        "failed invoice grace period",
        "trial expiration entitlement lag",
        "usage meter delay",
        "invoice owner mismatch",
        "downgrade removed premium permission",
        "contracted add-on not provisioned",
    ],
    "b2c_subscription_billing": [
        "trial-to-paid conversion",
        "duplicate retry charge",
        "pending authorization mistaken for settled charge",
        "household family-plan purchase",
        "mid-cycle proration after plan change",
        "failed-payment dunning card retry",
        "price increase not noticed",
        "genuine fraud card not recognized",
    ],
}


SCENARIO_LIBRARY: dict[str, list[dict[str, Any]]] = {
    "permissions_access": [
        {
            "hidden_root_cause": "Migrated workspace groups did not inherit the Billing Analyst role.",
            "issue_path": [
                "customer reports several users lost access",
                "agent checks individual user status",
                "team learns affected users share a migrated group",
                "role inheritance is corrected",
            ],
            "known_facts": [
                "multiple users are affected",
                "the problem started after a workspace migration",
                "admins can still access the workspace",
            ],
            "delayed_facts": [
                "all affected users belong to the Billing Analyst group",
                "the migration completed last night",
                "one manually invited user can access the workspace",
            ],
            "wrong_paths": [
                "password reset",
                "browser cache",
                "expired invitations",
            ],
            "escalation_trigger": "customer has a finance deadline in two hours and three analysts are blocked",
            "final_outcome": "agent identifies missing group role mapping and restores access",
        },
        {
            "hidden_root_cause": "A security policy now requires SSO group membership before app roles apply.",
            "issue_path": [
                "customer reports access denied after SSO enforcement",
                "agent checks app roles",
                "SSO group mismatch is discovered",
                "identity-provider group assignment is corrected",
            ],
            "known_facts": [
                "customer recently enabled SSO enforcement",
                "the user appears active in the app",
                "the error says access denied rather than account missing",
            ],
            "delayed_facts": [
                "the blocked user changed departments last week",
                "department change removed the SSO group",
                "other users in the same app role still have access",
            ],
            "wrong_paths": [
                "license limit",
                "app role deletion",
                "regional outage",
            ],
            "escalation_trigger": "customer threatens to roll back SSO if support cannot explain the failure",
            "final_outcome": "agent separates app permissions from identity-provider group membership",
        },
    ],
    "onboarding_migration": [
        {
            "hidden_root_cause": "Legacy project owners were mapped to viewers during import.",
            "issue_path": [
                "customer says migrated projects are visible but not editable",
                "agent checks migration completion",
                "role mapping table is reviewed",
                "owner roles are remapped and reimported",
            ],
            "known_facts": [
                "migration completed with no fatal errors",
                "projects are visible",
                "owners cannot edit migrated records",
            ],
            "delayed_facts": [
                "a custom legacy owner role existed",
                "migration logs show fallback role mapping",
                "newly created projects are editable",
            ],
            "wrong_paths": [
                "partial data import",
                "browser permissions prompt",
                "workspace storage limit",
            ],
            "escalation_trigger": "customer has an onboarding review with executives tomorrow",
            "final_outcome": "agent finds custom legacy role mapping error and schedules corrected reimport",
        },
        {
            "hidden_root_cause": "CSV import skipped archived teams that still own active records.",
            "issue_path": [
                "customer reports missing records after import",
                "agent checks import totals",
                "missing records are tied to archived source teams",
                "import filter is adjusted",
            ],
            "known_facts": [
                "import finished successfully",
                "record count is lower than expected",
                "customer used the standard migration CSV",
            ],
            "delayed_facts": [
                "some archived teams own active records",
                "the CSV export filtered archived teams by default",
                "missing records share the same legacy team IDs",
            ],
            "wrong_paths": [
                "duplicate merge",
                "file upload corruption",
                "timezone conversion",
            ],
            "escalation_trigger": "customer says they cannot go live without the missing records",
            "final_outcome": "agent identifies the archived-team export filter and reruns import scope",
        },
    ],
    "workspace_setup": [
        {
            "hidden_root_cause": "Workspace domain verification is pending because DNS TXT record was added to the wrong subdomain.",
            "issue_path": [
                "customer cannot finish workspace setup",
                "agent checks setup checklist",
                "DNS verification state is inspected",
                "customer corrects TXT record location",
            ],
            "known_facts": [
                "workspace setup is blocked at domain verification",
                "customer says DNS was updated",
                "verification has been pending for several hours",
            ],
            "delayed_facts": [
                "the TXT record was added to app.company.com",
                "verification expects company.com",
                "customer's IT owner copied from a staging guide",
            ],
            "wrong_paths": [
                "billing hold",
                "workspace region mismatch",
                "invite email delivery",
            ],
            "escalation_trigger": "customer's onboarding session is live while setup is blocked",
            "final_outcome": "agent identifies wrong DNS record placement and gives exact correction",
        },
        {
            "hidden_root_cause": "The workspace template requires an integration permission the customer's admin has not granted.",
            "issue_path": [
                "customer sees workspace template setup fail",
                "agent checks template requirements",
                "missing integration permission is discovered",
                "admin grants permission and setup completes",
            ],
            "known_facts": [
                "workspace creation starts but fails near the end",
                "the customer is using the standard onboarding template",
                "manual workspace creation works",
            ],
            "delayed_facts": [
                "integration permission was declined during OAuth",
                "template automation needs write access",
                "customer's admin role can approve the permission",
            ],
            "wrong_paths": [
                "template outage",
                "workspace name conflict",
                "seat limit",
            ],
            "escalation_trigger": "customer says this is their third failed setup attempt",
            "final_outcome": "agent identifies missing OAuth permission and has admin reauthorize",
        },
    ],
    "integrations_data_sync": [
        {
            "hidden_root_cause": "The CRM sync is stalled because the OAuth refresh token expired after an admin password rotation.",
            "issue_path": [
                "customer reports CRM records stopped updating",
                "agent checks recent sync jobs and field mappings",
                "late evidence shows auth refresh failures after admin rotation",
                "customer reauthorizes the integration owner account",
            ],
            "known_facts": [
                "new CRM records are not appearing in the SaaS workspace",
                "older synced records are still visible",
                "manual CSV import still works",
            ],
            "delayed_facts": [
                "sync logs show repeated refresh token failures",
                "the integration owner changed their password yesterday",
                "webhook delivery is still succeeding for another object type",
            ],
            "wrong_paths": [
                "CRM field mapping",
                "rate limit",
                "webhook outage",
            ],
            "escalation_trigger": "customer's revenue team is missing same-day pipeline updates",
            "final_outcome": "agent identifies expired OAuth refresh token and has the admin reauthorize the CRM integration",
        },
        {
            "hidden_root_cause": "Duplicate records are being created because external IDs changed during a CRM migration.",
            "issue_path": [
                "customer reports duplicate account records after sync",
                "agent checks merge rules and recent connector changes",
                "late evidence shows external IDs changed during migration",
                "sync matching rules are updated before backfill",
            ],
            "known_facts": [
                "duplicates appeared after a CRM migration",
                "new records sync successfully",
                "existing account names look almost identical",
            ],
            "delayed_facts": [
                "external IDs were regenerated in the CRM migration",
                "the connector still matches on the old external ID field",
                "one non-migrated account did not duplicate",
            ],
            "wrong_paths": [
                "merge rule disabled",
                "manual import duplication",
                "field mapping conflict",
            ],
            "escalation_trigger": "customer says sales reps cannot trust account ownership before a forecast review",
            "final_outcome": "agent identifies external ID mapping drift and pauses sync until matching rules are corrected",
        },
    ],
    "billing_plan_entitlement": [
        {
            "hidden_root_cause": "A plan downgrade removed access to the automation feature, but cached UI state still shows the old menu.",
            "issue_path": [
                "customer reports automation suddenly fails for admins",
                "agent checks permissions and recent product changes",
                "late evidence shows a plan downgrade changed entitlements",
                "customer confirms whether to restore the plan or remove the workflow",
            ],
            "known_facts": [
                "automation menu is visible but execution fails",
                "admins can still access other workspace settings",
                "the account changed billing terms recently",
            ],
            "delayed_facts": [
                "entitlement logs show automation disabled after downgrade",
                "UI cache still exposes the old automation menu",
                "a workspace on the previous plan can still run the workflow",
            ],
            "wrong_paths": [
                "workflow misconfiguration",
                "integration permission",
                "regional outage",
            ],
            "escalation_trigger": "customer says a renewal conversation depends on proving whether this is a bug or plan behavior",
            "final_outcome": "agent separates stale UI visibility from downgraded plan entitlement",
        },
        {
            "hidden_root_cause": "New seats cannot be added because a failed invoice put the account into a grace-period entitlement hold.",
            "issue_path": [
                "customer reports they cannot add new users",
                "agent checks role limits and invite delivery",
                "late evidence shows a failed invoice hold",
                "billing owner resolves payment before new seats are added",
            ],
            "known_facts": [
                "existing users can still work",
                "new invites fail near the final step",
                "the admin sees a generic seat availability message",
            ],
            "delayed_facts": [
                "billing system shows a failed invoice in grace period",
                "seat count has room but entitlement expansion is paused",
                "billing owner email differs from the workspace admin",
            ],
            "wrong_paths": [
                "seat limit",
                "invite email delivery",
                "role permission",
            ],
            "escalation_trigger": "customer needs to add a contractor before a same-day onboarding session",
            "final_outcome": "agent identifies grace-period billing hold and routes the payment owner to resolve it",
        },
    ],
    "b2c_subscription_billing": [
        {
            "hidden_root_cause": "The disputed charge is a legitimate trial-to-paid subscription conversion that the customer forgot about.",
            "resolution_type": "resolved",
            "issue_path": [
                "subscriber reports an unrecognized subscription charge",
                "agent verifies account identity and charge details",
                "late evidence shows the free trial converted after renewal reminders",
                "agent explains refund eligibility without overpromising",
            ],
            "known_facts": [
                "customer sees a $19.99 charge from NOVA STREAM PLUS on their card",
                "customer says they cancelled something recently but is not sure which account used the trial",
                "the card last four matches the payment method on the subscription account",
            ],
            "delayed_facts": [
                "subscription service shows a trial started 14 days before the charge",
                "billing system shows two renewal reminder emails before conversion",
                "refund ledger shows no prior refund request for this subscription",
            ],
            "wrong_paths": [
                "duplicate charge",
                "fraudulent card use",
                "pending authorization",
            ],
            "escalation_trigger": "customer says they need the money back today and is worried another charge will post",
            "final_outcome": "agent confirms the charge came from trial conversion and opens the policy-based refund path after cancellation",
            "expected_handoff_seed": {
                "account_id": "acct_consumer_1827",
                "subscription_id": "sub_trial_4412",
                "customer_identity": "Maya R., verified by account email and card last four",
                "charge": {
                    "amount": "$19.99",
                    "date": "2026-06-18",
                    "descriptor": "NOVA STREAM PLUS",
                    "last4": "4242",
                    "transaction_id": "txn_trial_61819",
                },
                "customer_claim": "Customer does not recognize the charge and believes the trial should not have converted.",
                "desired_outcome": "Cancel subscription and request refund if policy allows.",
                "checks": [
                    "Verified account email and card last four.",
                    "Confirmed trial start and conversion timestamp in subscription service.",
                    "Checked refund ledger for prior refund activity.",
                ],
                "ruled_out": ["duplicate charge", "pending authorization", "confirmed fraud"],
                "risk": "Medium urgency because customer is upset about a household budget impact.",
                "next_step": "Cancel renewal, explain refund policy window, and submit refund request if eligible.",
                "what_not_to_promise": "Do not promise an instant refund or call the charge fraud.",
            },
        },
        {
            "hidden_root_cause": "The customer was charged twice because a payment retry succeeded after the first processor response timed out.",
            "resolution_type": "escalated",
            "issue_path": [
                "subscriber reports two identical charges for one subscription renewal",
                "agent compares settled transactions and subscription renewal events",
                "late evidence shows a processor timeout followed by a successful retry",
                "case escalates to payments engineering for refund and ledger correction",
            ],
            "known_facts": [
                "customer sees two $12.99 settled charges with the same descriptor",
                "subscription page shows only one active monthly plan",
                "customer says the bank shows both charges as posted, not pending",
            ],
            "delayed_facts": [
                "payment processor shows two settled transaction IDs for one renewal attempt",
                "billing system shows only one renewal event for the subscription",
                "refund ledger has no automatic reversal for the retry transaction",
            ],
            "wrong_paths": [
                "pending authorization",
                "family member purchase",
                "price increase",
            ],
            "escalation_trigger": "customer is requesting immediate correction because both charges have settled",
            "final_outcome": "agent rules out pending authorization and escalates the duplicate settled transaction to payments engineering",
            "expected_handoff_seed": {
                "account_id": "acct_consumer_2390",
                "subscription_id": "sub_monthly_8821",
                "customer_identity": "Jordan L., verified by SMS code and card last four",
                "charge": {
                    "amount": "$12.99 x2",
                    "date": "2026-06-20",
                    "descriptor": "NOVA STREAM PLUS",
                    "last4": "1881",
                    "transaction_id": "txn_renew_62012 and txn_retry_62013",
                },
                "customer_claim": "Customer says one monthly renewal produced two settled card charges.",
                "desired_outcome": "Refund the duplicate charge and confirm it will not repeat.",
                "checks": [
                    "Verified both charges are settled, not pending authorizations.",
                    "Confirmed only one subscription renewal event exists.",
                    "Checked refund ledger and found no automatic reversal.",
                ],
                "ruled_out": ["pending authorization", "separate family purchase", "price increase"],
                "risk": "High urgency because the customer has two settled charges for one renewal.",
                "next_step": "Escalate to payments engineering with both transaction IDs and request duplicate-charge correction.",
                "what_not_to_promise": "Do not promise same-day bank posting or manually adjust the ledger without payments review.",
                "engineering_discrepancy": "Two settled payment transactions exist for one subscription renewal event, and the duplicate lacks an automatic reversal.",
                "evidence_handles": ["txn_renew_62012", "txn_retry_62013", "renewal_event_62012", "processor_timeout_62012"],
                "engineering_ask": "Void or refund duplicate transaction and reconcile billing ledger to the single renewal event.",
            },
        },
        {
            "hidden_root_cause": "The card-not-recognized claim is unresolved and fraud-flagged because no matching subscription event can be confirmed for the verified account.",
            "resolution_type": "handoff",
            "issue_path": [
                "subscriber reports a card charge they do not recognize",
                "agent verifies identity and checks account subscription history",
                "late evidence shows the charge cannot be tied to the verified subscription account",
                "case routes to fraud and payments review without confirming a root cause",
            ],
            "known_facts": [
                "customer sees a $49.99 charge from NOVA STREAM PLUS but does not recognize the plan",
                "customer says no one in the household admits purchasing it",
                "the verified account email has no matching annual subscription",
            ],
            "delayed_facts": [
                "payment processor has a settled charge with the customer's card last four",
                "identity verification confirms the caller controls the known account",
                "subscription service has no matching subscription event on the verified account",
            ],
            "wrong_paths": [
                "trial-to-paid conversion",
                "family member purchase",
                "price increase",
            ],
            "escalation_trigger": "customer is worried their card was used without permission and asks whether to freeze it",
            "final_outcome": "agent does not confirm fraud, preserves the evidence, and routes the case to the fraud/payments team",
            "expected_handoff_seed": {
                "account_id": "acct_consumer_7741",
                "subscription_id": "no matching subscription event on verified account",
                "customer_identity": "Priya S., verified by email, SMS code, and card last four",
                "charge": {
                    "amount": "$49.99",
                    "date": "2026-06-21",
                    "descriptor": "NOVA STREAM PLUS",
                    "last4": "9090",
                    "transaction_id": "txn_unknown_62149",
                },
                "customer_claim": "Customer does not recognize the charge and says no household member admits purchasing it.",
                "desired_outcome": "Investigate possible unauthorized use and advise next safe step.",
                "checks": [
                    "Verified caller identity for the known account.",
                    "Checked subscription history for trial conversion, annual plan, and family-plan purchase.",
                    "Confirmed no matching subscription event on the verified account.",
                ],
                "ruled_out": ["trial-to-paid conversion on verified account", "price increase", "known family-plan purchase"],
                "risk": "High urgency because the charge is card-not-recognized and cannot be tied to the verified account.",
                "next_step": "Route to fraud/payments team with transaction details and advise customer to contact their card issuer if they suspect unauthorized use.",
                "what_not_to_promise": "Do not confirm fraud, disclose another account, or promise a refund before fraud review.",
                "fraud_flagged": True,
            },
        },
    ],
}


def build_scenario_spec(
    scenario_type: str,
    seed: int,
    root_cause_counts: dict[str, int] | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    if scenario_type not in SCENARIO_TYPES:
        raise ValueError(f"Unknown scenario '{scenario_type}'. Expected one of: {', '.join(SCENARIO_TYPES)}")

    rng = random.Random(seed)
    base = _choose_base(scenario_type, rng, root_cause_counts or {})
    difficulty = _weighted_choice(rng, {"easy": 15, "medium": 45, "hard": 40})
    resolution_type = base.get("resolution_type") or _weighted_choice(rng, RESOLUTION_WEIGHTS)

    persona = _build_persona(scenario_type, rng)
    stressors = _build_stressors(base, rng)

    spec = {
        "scenario_type": scenario_type,
        "hidden_root_cause": base["hidden_root_cause"],
        "customer_persona": persona,
        "agent_quality": _weighted_choice(rng, AGENT_QUALITY_WEIGHTS),
        "difficulty": difficulty,
        "difficulty_metadata": _build_difficulty_metadata(difficulty, rng),
        "resolution_type": resolution_type,
        "resolution_outcome": _resolution_outcome(resolution_type, scenario_type),
        "root_cause_id": base["root_cause_id"],
        "root_cause_category": base["root_cause_category"],
        "product_policy": _build_product_policy(scenario_type),
        "known_facts": list(base["known_facts"]),
        "delayed_facts": list(base["delayed_facts"]),
        "ambiguity_level": rng.choice(AMBIGUITY_LEVELS),
        "delayed_fact_timing": rng.choice(DELAYED_FACT_TIMING),
        "escalation_risk": rng.choice(ESCALATION_RISK),
        "escalation_conditions": [base["escalation_trigger"]],
        "issue_path": list(base["issue_path"]),
        "wrong_paths": list(base["wrong_paths"]),
        "stressors": stressors,
        "customer_unreliability": _build_customer_unreliability(rng, scenario_type),
        "final_outcome": base["final_outcome"],
    }
    if scenario_type == "b2c_subscription_billing":
        spec["expected_handoff_seed"] = dict(base["expected_handoff_seed"])

    if profile:
        from support_call_generator.profiles import apply_profile
        apply_profile(spec, profile, rng)
        if base.get("resolution_type"):
            spec["resolution_type"] = base["resolution_type"]
        spec["resolution_outcome"] = _resolution_outcome(spec["resolution_type"], scenario_type)

    return spec


def _choose_base(scenario_type: str, rng: random.Random, root_cause_counts: dict[str, int]) -> dict[str, Any]:
    options = [_with_root_metadata(scenario_type, base) for base in _expanded_library(scenario_type)]
    least_used = min(root_cause_counts.get(option["root_cause_id"], 0) for option in options)
    underused = [option for option in options if root_cause_counts.get(option["root_cause_id"], 0) == least_used]
    return rng.choice(underused)


def _expanded_library(scenario_type: str) -> list[dict[str, Any]]:
    entries = list(SCENARIO_LIBRARY[scenario_type])
    existing = {_root_id(entry["hidden_root_cause"]) for entry in entries}
    for label in ROOT_CAUSE_CATALOG[scenario_type]:
        root_cause = _root_cause_sentence(scenario_type, label)
        if _root_id(root_cause) in existing:
            continue
        entries.append(_catalog_entry(scenario_type, label, root_cause))
    return entries


def _with_root_metadata(scenario_type: str, base: dict[str, Any]) -> dict[str, Any]:
    item = dict(base)
    item.setdefault("root_cause_id", _root_id(item["hidden_root_cause"]))
    item.setdefault("root_cause_category", scenario_type)
    return item


def _catalog_entry(scenario_type: str, label: str, root_cause: str) -> dict[str, Any]:
    scenario_noun = {
        "permissions_access": "access issue",
        "onboarding_migration": "migration issue",
        "workspace_setup": "workspace setup issue",
        "integrations_data_sync": "integration sync issue",
        "billing_plan_entitlement": "billing or entitlement issue",
        "b2c_subscription_billing": "subscription billing dispute",
    }[scenario_type]
    if scenario_type == "b2c_subscription_billing":
        return _b2c_catalog_entry(label, root_cause)
    return {
        "hidden_root_cause": root_cause,
        "root_cause_id": _root_id(root_cause),
        "root_cause_category": scenario_type,
        "issue_path": [
            f"customer reports a {scenario_noun}",
            "agent tests two plausible but wrong branches",
            f"late evidence points toward {label}",
            "call ends according to the selected resolution type",
        ],
        "known_facts": [
            f"customer reports symptoms consistent with more than one {scenario_noun}",
            "the issue began after a recent operational change",
            "at least one comparison case behaves differently",
        ],
        "delayed_facts": [
            f"an admin later mentions {label}",
            "logs show a warning that was initially dismissed",
            "a working example differs in one hidden configuration detail",
        ],
        "wrong_paths": _wrong_paths_for(scenario_type, label),
        "escalation_trigger": "customer has a time-sensitive rollout or business deadline and trust is degrading",
        "final_outcome": f"agent identifies {label} as the likely operational cause, but certainty depends on the selected resolution type",
    }


def _wrong_paths_for(scenario_type: str, label: str) -> list[str]:
    pool = {
        "permissions_access": ["browser cache", "license limit", "expired invitation", "regional outage", "password reset"],
        "onboarding_migration": ["partial import", "timezone conversion", "duplicate merge", "file upload corruption", "workspace quota"],
        "workspace_setup": ["billing hold", "region mismatch", "template outage", "invite delivery", "workspace name conflict"],
        "integrations_data_sync": ["field mapping conflict", "rate limit", "webhook outage", "manual import duplication", "CRM permission"],
        "billing_plan_entitlement": ["seat limit", "invite email delivery", "role permission", "workflow misconfiguration", "regional outage"],
        "b2c_subscription_billing": ["pending authorization", "family member purchase", "trial conversion", "price increase", "duplicate charge"],
    }[scenario_type]
    return [item for item in pool if item.lower() not in label.lower()][:3]


def _root_cause_sentence(scenario_type: str, label: str) -> str:
    return {
        "permissions_access": f"The access failure is caused by {label}.",
        "onboarding_migration": f"The migration problem is caused by {label}.",
        "workspace_setup": f"The workspace setup failure is caused by {label}.",
        "integrations_data_sync": f"The integration sync problem is caused by {label}.",
        "billing_plan_entitlement": f"The billing or entitlement problem is caused by {label}.",
        "b2c_subscription_billing": (
            "The card-not-recognized claim remains unexplained and fraud-flagged because the verified account has no matching subscription event."
            if "fraud" in label.lower() or "card not recognized" in label.lower()
            else f"The subscription billing dispute is caused by {label}."
        ),
    }[scenario_type]


def _root_id(text: str) -> str:
    return "_".join(text.lower().replace(".", "").replace("/", " ").split()[:8])


def _weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def _build_difficulty_metadata(difficulty: str, rng: random.Random) -> dict[str, int | str]:
    if difficulty == "easy":
        ambiguity = rng.randint(2, 3)
        leakage = rng.randint(4, 5)
    elif difficulty == "medium":
        ambiguity = rng.randint(3, 4)
        leakage = rng.randint(3, 5)
    else:
        ambiguity = rng.randint(4, 5)
        leakage = rng.randint(4, 5)
    return {
        "difficulty": difficulty,
        "ambiguity_score": ambiguity,
        "leakage_score": leakage,
        "realism_score": rng.randint(3, 5),
    }


def _resolution_outcome(resolution_type: str, scenario_type: str = "") -> str:
    if scenario_type == "b2c_subscription_billing":
        return {
            "resolved": "charge explanation and support-policy next step reached during the call",
            "probable_cause": "probable billing explanation identified but payment or refund verification remains",
            "escalated": "escalated to payments engineering with charge and subscription evidence preserved",
            "handoff": "handed off to fraud/payments review with unresolved card-not-recognized evidence",
            "unresolved": "billing investigation remains open with incomplete payment or identity evidence",
        }[resolution_type]
    return {
        "resolved": "clear resolution reached during the call",
        "probable_cause": "probable cause identified but verification remains",
        "escalated": "escalated to engineering or product with operational state preserved",
        "handoff": "handed off to customer admin, identity team, or implementation owner",
        "unresolved": "investigation remains open with incomplete evidence",
    }[resolution_type]


def _build_persona(scenario_type: str, rng: random.Random) -> dict[str, str]:
    if scenario_type == "b2c_subscription_billing":
        return {
            "role": rng.choice(["Subscriber", "Family account owner", "Trial user", "Annual plan customer"]),
            "mood": rng.choice(["confused", "frustrated", "anxious", "impatient"]),
            "clarity": rng.choice(CUSTOMER_CLARITY),
            "patience": rng.choice(CUSTOMER_PATIENCE),
            "technical_skill": rng.choice(TECHNICAL_SKILL),
        }
    return {
        "role": rng.choice(["Customer Success Ops Lead", "IT Admin", "RevOps Manager", "Implementation Manager"]),
        "mood": rng.choice(CUSTOMER_MOODS),
        "clarity": rng.choice(CUSTOMER_CLARITY),
        "patience": rng.choice(CUSTOMER_PATIENCE),
        "technical_skill": rng.choice(TECHNICAL_SKILL),
    }


def _build_product_policy(scenario_type: str) -> dict[str, str]:
    if scenario_type == "b2c_subscription_billing":
        return {
            "support_boundary": "Billing support can verify identity, explain charges, cancel renewal, and submit refunds within policy. Fraud or card-not-recognized claims must route to fraud/payments review.",
            "escalation_policy": "Escalate to payments engineering when settled charges do not match subscription events, refund ledger state is missing, or a charge cannot be tied to the verified account.",
        }
    return {
        "support_boundary": "Support can diagnose configuration and migration issues, but customer admins must approve identity, DNS, or OAuth changes.",
        "escalation_policy": "Escalate when a production deadline is at risk, multiple users are blocked, or root cause remains unclear after three diagnostic branches.",
    }


def _build_customer_unreliability(rng: random.Random, scenario_type: str) -> list[str]:
    if scenario_type == "b2c_subscription_billing":
        options = [
            "customer is unsure whether they cancelled the trial or only deleted the app",
            "customer initially says no one else uses the account, then remembers a shared household profile",
            "customer mixes up pending and posted card activity",
            "customer gives the charge date from their banking app before realizing it is the posting date",
            "customer overfocuses on a previous refund experience that does not match this charge",
        ]
    else:
        options = [
            "customer initially says nothing changed, then remembers a recent admin change",
            "customer overfocuses on a symptom from a previous incident",
            "customer gives a timeline that later needs correction",
            "customer mixes up app roles with identity-provider groups",
            "customer reports a secondhand observation that turns out to be incomplete",
        ]
    rng.shuffle(options)
    return options[:2]


def _b2c_catalog_entry(label: str, root_cause: str) -> dict[str, Any]:
    fraud_flagged = "fraud" in label.lower() or "card not recognized" in label.lower()
    return {
        "hidden_root_cause": root_cause,
        **({"resolution_type": "handoff"} if fraud_flagged else {}),
        "root_cause_id": _root_id(root_cause),
        "root_cause_category": "b2c_subscription_billing",
        "issue_path": [
            "subscriber reports a disputed subscription charge",
            "agent verifies identity and checks payment/subscription records",
            f"late evidence points toward {label}",
            "call ends according to the selected resolution type",
        ],
        "known_facts": [
            "customer reports a card charge they do not recognize",
            "the descriptor looks like the subscription product but the customer is unsure which account used it",
            "one account or household detail points away from the first explanation",
        ],
        "delayed_facts": [
            f"billing evidence later mentions {label}",
            "payment records include a detail the customer did not see in their banking app",
            "subscription history differs from the customer's first timeline",
        ],
        "wrong_paths": _wrong_paths_for("b2c_subscription_billing", label),
        "escalation_trigger": "customer is worried about an unexpected personal card charge and wants a safe next step",
        "final_outcome": (
            "agent preserves the unexplained charge evidence and routes the case to fraud/payments review"
            if fraud_flagged
            else f"agent treats {label} as the likely billing explanation, while following refund or fraud policy boundaries"
        ),
        "expected_handoff_seed": {
            "account_id": "acct_consumer_catalog",
            "subscription_id": "sub_catalog_review",
            "customer_identity": "Verified subscriber using account email and card last four",
            "charge": {
                "amount": "$19.99",
                "date": "2026-06-18",
                "descriptor": "NOVA STREAM PLUS",
                "last4": "4242",
                "transaction_id": "txn_catalog_review",
            },
            "customer_claim": "Customer disputes a subscription charge and wants the charge explained.",
            "desired_outcome": "Explain the charge and apply refund or fraud routing policy.",
            "checks": [
                "Verified identity and card last four.",
                "Checked payment processor status.",
                "Checked subscription history and refund ledger.",
            ],
            "ruled_out": _wrong_paths_for("b2c_subscription_billing", label)[:2],
            "risk": "Medium urgency due to disputed personal card charge.",
            "next_step": "Continue billing review under refund and fraud policy boundaries.",
            "what_not_to_promise": "Do not promise refund timing or confirm fraud before review.",
            **({"fraud_flagged": True} if fraud_flagged else {}),
        },
    }


def _build_stressors(base: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    wrong_paths = list(base["wrong_paths"])
    delayed_facts = list(base["delayed_facts"])
    known_facts = list(base["known_facts"])

    rng.shuffle(wrong_paths)
    rng.shuffle(delayed_facts)

    return {
        "misleading_evidence": [
            f"An early symptom seems to support {wrong_paths[0]}, but later evidence weakens it.",
            f"A customer-provided detail sounds decisive at first, but turns out to describe a separate condition: {known_facts[-1]}.",
        ],
        "false_leads": wrong_paths[:2],
        "abandoned_troubleshooting_paths": [
            f"The agent spends several turns checking {wrong_paths[0]} before abandoning it.",
            f"The customer suggests {wrong_paths[1]} because it happened in a previous incident, but it does not fit the current evidence.",
        ],
        "hypothesis_reversals": [
            f"The likely explanation shifts away from {wrong_paths[0]} after a delayed fact appears.",
            f"A hypothesis that looked unlikely becomes plausible only after this late fact: {delayed_facts[0]}.",
        ],
        "conflicting_observations": [
            f"{known_facts[0]}, but {known_facts[-1]}.",
            f"{delayed_facts[0]}, while another affected example points away from the same branch.",
        ],
        "late_reveal_facts": delayed_facts[:2],
        "root_cause_reveal": "Do not make the actual root cause clear until the final third of the call.",
        "stress_goal": "Stress-test operational state tracking, hypothesis management, and recovery from wrong paths rather than simple final root-cause identification.",
    }
