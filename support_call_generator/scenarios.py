from __future__ import annotations

import random
from typing import Any


SCENARIO_TYPES = ["permissions_access", "onboarding_migration", "workspace_setup"]

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
}


def build_scenario_spec(
    scenario_type: str,
    seed: int,
    root_cause_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    if scenario_type not in SCENARIO_TYPES:
        raise ValueError(f"Unknown scenario '{scenario_type}'. Expected one of: {', '.join(SCENARIO_TYPES)}")

    rng = random.Random(seed)
    base = _choose_base(scenario_type, rng, root_cause_counts or {})
    difficulty = _weighted_choice(rng, {"easy": 15, "medium": 45, "hard": 40})
    resolution_type = _weighted_choice(rng, RESOLUTION_WEIGHTS)

    persona = {
        "role": rng.choice(["Customer Success Ops Lead", "IT Admin", "RevOps Manager", "Implementation Manager"]),
        "mood": rng.choice(CUSTOMER_MOODS),
        "clarity": rng.choice(CUSTOMER_CLARITY),
        "patience": rng.choice(CUSTOMER_PATIENCE),
        "technical_skill": rng.choice(TECHNICAL_SKILL),
    }
    stressors = _build_stressors(base, rng)

    return {
        "scenario_type": scenario_type,
        "hidden_root_cause": base["hidden_root_cause"],
        "customer_persona": persona,
        "agent_quality": _weighted_choice(rng, AGENT_QUALITY_WEIGHTS),
        "difficulty": difficulty,
        "difficulty_metadata": _build_difficulty_metadata(difficulty, rng),
        "resolution_type": resolution_type,
        "resolution_outcome": _resolution_outcome(resolution_type),
        "root_cause_id": base["root_cause_id"],
        "root_cause_category": base["root_cause_category"],
        "product_policy": {
            "support_boundary": "Support can diagnose configuration and migration issues, but customer admins must approve identity, DNS, or OAuth changes.",
            "escalation_policy": "Escalate when a production deadline is at risk, multiple users are blocked, or root cause remains unclear after three diagnostic branches.",
        },
        "known_facts": list(base["known_facts"]),
        "delayed_facts": list(base["delayed_facts"]),
        "ambiguity_level": rng.choice(AMBIGUITY_LEVELS),
        "delayed_fact_timing": rng.choice(DELAYED_FACT_TIMING),
        "escalation_risk": rng.choice(ESCALATION_RISK),
        "escalation_conditions": [base["escalation_trigger"]],
        "issue_path": list(base["issue_path"]),
        "wrong_paths": list(base["wrong_paths"]),
        "stressors": stressors,
        "customer_unreliability": _build_customer_unreliability(rng),
        "final_outcome": base["final_outcome"],
    }


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
    }[scenario_type]
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
    }[scenario_type]
    return [item for item in pool if item.lower() not in label.lower()][:3]


def _root_cause_sentence(scenario_type: str, label: str) -> str:
    return {
        "permissions_access": f"The access failure is caused by {label}.",
        "onboarding_migration": f"The migration problem is caused by {label}.",
        "workspace_setup": f"The workspace setup failure is caused by {label}.",
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


def _resolution_outcome(resolution_type: str) -> str:
    return {
        "resolved": "clear resolution reached during the call",
        "probable_cause": "probable cause identified but verification remains",
        "escalated": "escalated to engineering or product with operational state preserved",
        "handoff": "handed off to customer admin, identity team, or implementation owner",
        "unresolved": "investigation remains open with incomplete evidence",
    }[resolution_type]


def _build_customer_unreliability(rng: random.Random) -> list[str]:
    options = [
        "customer initially says nothing changed, then remembers a recent admin change",
        "customer overfocuses on a symptom from a previous incident",
        "customer gives a timeline that later needs correction",
        "customer mixes up app roles with identity-provider groups",
        "customer reports a secondhand observation that turns out to be incomplete",
    ]
    rng.shuffle(options)
    return options[:2]


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
