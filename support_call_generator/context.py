from __future__ import annotations

import random
from typing import Any


CONTEXT_SOURCES: dict[str, list[str]] = {
    "permissions_access": ["admin_panel", "identity_provider", "audit_log", "incident_note", "prior_ticket"],
    "onboarding_migration": ["admin_panel", "migration_log", "audit_log", "prior_ticket", "incident_note"],
    "workspace_setup": ["admin_panel", "billing_system", "email_delivery", "audit_log", "incident_note"],
}

_IRRELEVANT_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "permissions_access": [
        {
            "source": "incident_note",
            "description": "Unrelated SSO certificate renewal completed last week for a different region.",
            "facts": ["incident:sso_cert_renewal", "region:eu_west"],
        },
        {
            "source": "prior_ticket",
            "description": "Previous ticket about password complexity policy was resolved two months ago.",
            "facts": ["prior_ticket:password_policy", "status:resolved"],
        },
    ],
    "onboarding_migration": [
        {
            "source": "incident_note",
            "description": "Scheduled maintenance window affected a staging environment, not production.",
            "facts": ["incident:staging_maintenance", "environment:staging"],
        },
        {
            "source": "prior_ticket",
            "description": "Earlier ticket about CSV encoding was resolved with UTF-8 normalization.",
            "facts": ["prior_ticket:csv_encoding", "status:resolved"],
        },
    ],
    "workspace_setup": [
        {
            "source": "incident_note",
            "description": "CDN edge cache was purged last night during routine maintenance.",
            "facts": ["incident:cdn_purge", "scope:routine"],
        },
        {
            "source": "prior_ticket",
            "description": "Previous workspace creation for a different team completed without issues.",
            "facts": ["prior_ticket:other_workspace", "status:resolved"],
        },
    ],
}

_CONFLICTING_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "permissions_access": [
        {
            "source": "audit_log",
            "description": "Audit log shows the affected role was last modified 6 months ago, suggesting no recent change.",
            "facts": ["role_modified:6_months_ago"],
        },
    ],
    "onboarding_migration": [
        {
            "source": "migration_log",
            "description": "Migration log reports all records as successfully imported, contradicting the missing count.",
            "facts": ["migration_status:all_imported"],
        },
    ],
    "workspace_setup": [
        {
            "source": "billing_system",
            "description": "Billing system shows the account is active and fully paid, ruling out a billing hold.",
            "facts": ["billing_status:active", "payment:current"],
        },
    ],
}


def build_context_events(spec: dict[str, Any], turn_count: int) -> list[dict[str, Any]]:
    seed = hash(spec.get("root_cause_id", "")) & 0xFFFFFFFF
    rng = random.Random(seed)
    scenario_type = spec["scenario_type"]
    sources = CONTEXT_SOURCES.get(scenario_type, ["admin_panel", "audit_log"])
    profile = spec.get("profile")

    delayed_facts = list(spec.get("delayed_facts", []))
    late_reveal_facts = list(spec.get("stressors", {}).get("late_reveal_facts", []))
    wrong_paths = list(spec.get("wrong_paths", []))
    issue_path = list(spec.get("issue_path", []))

    events: list[dict[str, Any]] = []
    final_third_start = max(1, int(turn_count * 2 / 3))

    for i, fact in enumerate(delayed_facts):
        position = _distribute_turn(i, len(delayed_facts), 3, final_third_start - 1, rng)
        source = sources[i % len(sources)]
        events.append({
            "after_turn": position,
            "source": source,
            "description": fact,
            "facts": [_fact_key(fact)],
            "resolved_unknowns": [],
            "ruled_out_branches": [wrong_paths[i]] if i < len(wrong_paths) else [],
            "candidate_branches": [],
            "is_irrelevant": False,
            "is_conflicting": False,
            "reveals_final_cause": False,
        })

    for i, fact in enumerate(late_reveal_facts):
        position = _distribute_turn(i, len(late_reveal_facts), final_third_start, turn_count, rng)
        source = sources[(len(delayed_facts) + i) % len(sources)]
        is_last = (i == len(late_reveal_facts) - 1)
        events.append({
            "after_turn": position,
            "source": source,
            "description": fact,
            "facts": [_fact_key(fact)],
            "resolved_unknowns": [_infer_unknown(issue_path)] if is_last else [],
            "ruled_out_branches": [],
            "candidate_branches": [_infer_candidate(spec)] if is_last else [],
            "is_irrelevant": False,
            "is_conflicting": False,
            "reveals_final_cause": is_last,
        })

    if profile:
        irr_lo, irr_hi = profile.get("irrelevant_context_count", (0, 0))
        irr_count = rng.randint(irr_lo, irr_hi)
        templates = _IRRELEVANT_TEMPLATES.get(scenario_type, [])
        for tmpl in rng.sample(templates, min(irr_count, len(templates))):
            position = rng.randint(2, final_third_start - 1)
            events.append({
                "after_turn": position,
                "source": tmpl["source"],
                "description": tmpl["description"],
                "facts": list(tmpl["facts"]),
                "resolved_unknowns": [],
                "ruled_out_branches": [],
                "candidate_branches": [],
                "is_irrelevant": True,
                "is_conflicting": False,
                "reveals_final_cause": False,
            })

        con_lo, con_hi = profile.get("conflicting_context_count", (0, 0))
        con_count = rng.randint(con_lo, con_hi)
        templates = _CONFLICTING_TEMPLATES.get(scenario_type, [])
        for tmpl in rng.sample(templates, min(con_count, len(templates))):
            position = rng.randint(3, final_third_start)
            events.append({
                "after_turn": position,
                "source": tmpl["source"],
                "description": tmpl["description"],
                "facts": list(tmpl["facts"]),
                "resolved_unknowns": [],
                "ruled_out_branches": [],
                "candidate_branches": [],
                "is_irrelevant": False,
                "is_conflicting": True,
                "reveals_final_cause": False,
            })

    if not any(e["reveals_final_cause"] for e in events) and events:
        last_real = [e for e in events if not e["is_irrelevant"] and not e["is_conflicting"]]
        if last_real:
            target = max(last_real, key=lambda e: e["after_turn"])
            target["reveals_final_cause"] = True
            target["after_turn"] = max(target["after_turn"], final_third_start)
            target["candidate_branches"] = [_infer_candidate(spec)]

    events.sort(key=lambda e: e["after_turn"])
    return events


def _distribute_turn(index: int, total: int, start: int, end: int, rng: random.Random) -> int:
    if total <= 1:
        return rng.randint(start, end)
    slot_size = max(1, (end - start) // total)
    slot_start = start + index * slot_size
    slot_end = min(end, slot_start + slot_size)
    return rng.randint(slot_start, max(slot_start, slot_end))


def _fact_key(text: str) -> str:
    words = text.lower().replace(",", "").replace(".", "").split()[:4]
    return "evidence:" + "_".join(words)


def _infer_unknown(issue_path: list[str]) -> str:
    if len(issue_path) >= 3:
        return issue_path[2].lower().replace(" ", "_")[:40]
    return "root_cause_mechanism"


def _infer_candidate(spec: dict[str, Any]) -> str:
    root = spec.get("root_cause_id", "unknown")
    return root
