from __future__ import annotations

import random
from typing import Any


CONTEXT_SOURCES: dict[str, list[str]] = {
    "permissions_access": ["admin_panel", "identity_provider", "audit_log", "incident_note", "prior_ticket"],
    "onboarding_migration": ["admin_panel", "migration_log", "audit_log", "prior_ticket", "incident_note"],
    "workspace_setup": ["admin_panel", "billing_system", "email_delivery", "audit_log", "incident_note"],
    "integrations_data_sync": ["integration_log", "crm_connector", "webhook_log", "admin_panel", "prior_ticket"],
    "billing_plan_entitlement": ["billing_system", "entitlement_service", "admin_panel", "audit_log", "prior_ticket"],
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
    "integrations_data_sync": [
        {
            "source": "prior_ticket",
            "description": "Previous ticket about a sandbox connector was resolved and involved a different workspace.",
            "facts": ["prior_ticket:sandbox_connector", "status:resolved"],
        },
        {
            "source": "webhook_log",
            "description": "Unrelated webhook retries affected a deprecated object type that this customer does not use.",
            "facts": ["webhook:deprecated_object", "scope:unrelated"],
        },
    ],
    "billing_plan_entitlement": [
        {
            "source": "prior_ticket",
            "description": "Earlier invoice PDF request was resolved and did not change plan entitlements.",
            "facts": ["prior_ticket:invoice_pdf", "status:resolved"],
        },
        {
            "source": "admin_panel",
            "description": "A different workspace reached a seat warning last month, but this workspace did not.",
            "facts": ["seat_warning:different_workspace", "scope:unrelated"],
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
    "integrations_data_sync": [
        {
            "source": "webhook_log",
            "description": "Webhook delivery shows recent successful acknowledgements, which weakens a broad outage hypothesis.",
            "facts": ["webhook_delivery:successful"],
        },
    ],
    "billing_plan_entitlement": [
        {
            "source": "admin_panel",
            "description": "Admin panel shows available seats, contradicting a simple seat-limit explanation.",
            "facts": ["seat_count:available"],
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


_OPERATIONAL_PATTERNS = [
    (["billing", "analyst", "group"], "group:billing_analyst"),
    (["billing", "analyst", "role"], "role:billing_analyst"),
    (["sso", "group"], "sso_group:membership"),
    (["department", "change"], "dept_change:recent"),
    (["department", "removed"], "sso_group:removed"),
    (["app", "role", "access"], "app_role:works_for_others"),
    (["manually", "invited", "access"], "manual_invite:works"),
    (["migration", "completed"], "migration:completed"),
    (["migration", "last", "night"], "migration:recent"),
    (["custom", "legacy", "role"], "role_mapping:custom_legacy"),
    (["fallback", "role", "mapping"], "role_mapping:fallback"),
    (["newly", "created", "editable"], "new_records:editable"),
    (["archived", "teams", "own"], "archived_teams:owns_records"),
    (["csv", "export", "filtered"], "export_filter:archived_excluded"),
    (["legacy", "team", "ids"], "legacy_teams:shared_ids"),
    (["txt", "record", "added"], "dns:txt_wrong_subdomain"),
    (["verification", "expects"], "dns:verification_target"),
    (["staging", "guide"], "docs:staging_guide_copied"),
    (["integration", "permission", "declined"], "oauth:permission_declined"),
    (["write", "access"], "integration:write_scope_needed"),
    (["admin", "role", "approve"], "admin:can_approve"),
    (["admin", "mentions"], "admin:late_mention"),
    (["logs", "show", "warning"], "logs:warning_dismissed"),
    (["working", "example", "differs"], "comparison:config_differs"),
    (["scim", "sync"], "scim:sync_delay"),
    (["entitlement", "cache"], "cache:stale_entitlement"),
    (["role", "conflict"], "role:conflict"),
    (["role", "mapping", "rule"], "role_mapping:disabled"),
    (["owner", "translation"], "migration:ownership_translation"),
    (["duplicate", "merge"], "migration:duplicate_merge"),
    (["environment", "mismatch"], "env:mismatch"),
    (["inactive", "owner"], "owner:inactive_excluded"),
    (["field", "mapping"], "migration:field_mapping_fallback"),
    (["partial", "export"], "export:partial_scope"),
    (["dns", "record"], "dns:wrong_host"),
    (["oauth", "permission"], "oauth:declined"),
    (["connector", "authorization"], "connector:auth_failure"),
    (["provisioning", "timeout"], "provisioning:timeout"),
    (["template", "dependency"], "template:dependency_failure"),
    (["region", "mismatch"], "region:mismatch"),
    (["refresh", "token"], "oauth:refresh_token_failed"),
    (["integration", "owner", "password"], "integration_owner:password_rotated"),
    (["webhook", "delivery"], "webhook:delivery_status"),
    (["external", "ids"], "external_id:changed"),
    (["old", "external", "id"], "external_id:old_match"),
    (["non-migrated", "account"], "comparison:non_migrated_account"),
    (["entitlement", "logs"], "entitlement:changed"),
    (["automation", "disabled"], "feature:automation_disabled"),
    (["ui", "cache"], "ui:stale_cache"),
    (["failed", "invoice"], "invoice:failed"),
    (["grace", "period"], "billing:grace_period"),
    (["billing", "owner"], "billing_owner:different_from_admin"),
]


def _fact_key(text: str) -> str:
    lower = text.lower().replace(",", "").replace(".", "")
    for keywords, label in _OPERATIONAL_PATTERNS:
        if all(kw in lower for kw in keywords):
            return label
    words = lower.split()
    nouns = [w for w in words if len(w) > 3 and w not in _STOP_WORDS]
    if len(nouns) >= 2:
        return f"{nouns[0]}:{nouns[1]}"
    if nouns:
        return f"evidence:{nouns[0]}"
    return "evidence:" + "_".join(words[:3])


_STOP_WORDS = {
    "the", "that", "this", "with", "from", "have", "been", "were", "they",
    "their", "about", "after", "before", "into", "also", "each", "which",
    "does", "more", "than", "same", "some", "only", "still", "just",
}


def _infer_unknown(issue_path: list[str]) -> str:
    if len(issue_path) >= 3:
        return issue_path[2].lower().replace(" ", "_")[:40]
    return "root_cause_mechanism"


def _infer_candidate(spec: dict[str, Any]) -> str:
    root = spec.get("root_cause_id", "unknown")
    return root
