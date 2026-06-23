from __future__ import annotations

import json
import os
from typing import Any

from support_call_generator.context import CONTEXT_SOURCES
from support_call_generator.doctrines import render_doctrines


SYSTEM_PROMPT = """You generate synthetic support calls for evaluation.
Return only valid JSON. Do not include markdown fences.
The transcript must be realistic, operationally difficult, and not too clean.
Keep hidden ground truth consistent with the scenario scaffold.
The simulator doctrines are mandatory and override natural dialogue instincts."""


def _turn_range_rule(spec: dict[str, Any]) -> str:
    profile = spec.get("profile")
    if profile:
        lo, hi = profile["turn_range"]
        return f"- {lo} to {hi} turns (from difficulty profile '{profile['name']}')."
    return "- 16 to 28 turns."


def _context_event_rules(spec: dict[str, Any]) -> str:
    scenario_type = spec["scenario_type"]
    sources = CONTEXT_SOURCES.get(scenario_type, ["admin_panel", "audit_log"])
    source_list = ", ".join(sources)

    lines = [
        "Context event rules:",
        f"- Sources for this scenario type: {source_list}.",
        "- Each context event represents operational evidence that arrives BETWEEN transcript turns (after_turn = the turn after which this evidence surfaces).",
        "- Events are NOT dialogue — they are backend signals an agent would see in a dashboard, log, or system notification.",
        "- Timing: distribute events across the transcript. No events before turn 2.",
        "- Exactly one event must have reveals_final_cause=true, and it must appear in the final third of the transcript.",
        "- Events with reveals_final_cause=false must NOT contain the root cause or make it obvious.",
        "- Include irrelevant events (is_irrelevant=true) that look plausible but are unrelated — noise the agent must filter.",
        "- Include conflicting events (is_conflicting=true) that contradict the current leading hypothesis.",
        "- facts should be key:value strings like 'role_modified:6_months_ago' or 'evidence:sso_cert_renewal'.",
        "- resolved_unknowns, ruled_out_branches, candidate_branches are string arrays that track how this event changes the investigation state.",
    ]
    return "\n".join(lines)


def build_generation_prompt(spec: dict[str, Any]) -> str:
    domain_rules = _domain_rules(spec)
    return f"""
Create one realistic support-call case from this scaffold.

Mandatory simulator doctrines:
{render_doctrines()}

Rules:
{_turn_range_rule(spec)}
- Speakers must be "customer" and "agent".
- Stress-test operational reasoning, not simple root-cause identification.
- Follow the scenario difficulty, scores, resolution type, and outcome.
- Include misleading evidence, false leads, abandoned troubleshooting paths, conflicting observations, and hypothesis reversals.
- The correct root cause must not be clear until the final third of the call.
- Include at least two plausible hypotheses that strengthen and then weaken or get discarded.
- Include at least one customer statement that is true but misleading.
- Include unreliable narrator behavior from the scaffold.
- Include at least one observation that conflicts with the current leading hypothesis.
- The agent may recover, but should not move straight to the answer.
- The agent quality must match the scaffold.
- The customer persona must affect tone and clarity.
- Do not reveal hidden ground truth too early.
- Do not create unusually specific customer observations that conveniently name the answer.
- Do not let the agent intuit the answer without evidence.
- Do not make the troubleshooting sequence perfect; include at least one wrong-but-plausible branch that gets abandoned.
{domain_rules}

{_context_event_rules(spec)}

Return JSON with exactly:
{{
  "transcript": {{
    "turns": [{{"turn": 1, "speaker": "customer", "text": "..."}}],
    "summary": "one sentence"
  }},
  "ground_truth": {{
    "actual_root_cause": "...",
    "confidence": 0.0,
    "resolution_type": "resolved|probable_cause|escalated|handoff|unresolved",
    "root_cause_category": "...",
    "difficulty_metadata": {{
      "difficulty": "easy|medium|hard",
      "ambiguity_score": 1,
      "leakage_score": 1,
      "realism_score": 1
    }},
    "issue_path": ["..."],
    "key_evidence": ["..."],
    "wrong_paths": ["..."],
    "misleading_evidence": ["..."],
    "false_leads": ["..."],
    "abandoned_troubleshooting_paths": ["..."],
    "hypothesis_reversals": ["..."],
    "conflicting_observations": ["..."],
    "late_reveal_facts": ["..."],
    "doctrine_adherence": {{
      "uncertainty_pressure": "...",
      "information_asymmetry": "...",
      "leakage_controls": ["..."],
      "non_perfect_troubleshooting": "..."
    }},
    "why_difficult": ["..."],
    "escalation_timeline": [
      {{"turn": 1, "moment": "...", "type": "trust_degradation|escalation|missed_opportunity"}}
    ],
    "escalation_trigger": "...",
    "best_diagnostic_questions": ["..."],
    "final_outcome": "..."{_expected_handoff_schema(spec)}
  }},
  "context_events": [
    {{
      "after_turn": 5,
      "source": "admin_panel",
      "description": "Human-readable description of what this operational evidence shows.",
      "facts": ["key:value"],
      "resolved_unknowns": [],
      "ruled_out_branches": [],
      "candidate_branches": [],
      "is_irrelevant": false,
      "is_conflicting": false,
      "reveals_final_cause": false
    }}
  ],
  "expected_timeline": [
    {{
      "turn": 1,
      "hypothesis": "...",
      "state": "activate|strengthen|weaken|confirm|discard",
      "confidence": 0.0,
      "evidence": ["..."]
    }}
  ]
}}

Expected timeline requirements:
- Include at least six entries.
- Include the lifecycle states "activate", "strengthen", "weaken", "discard", and "confirm".
- Include one explicit hypothesis reversal.
- Include one abandoned troubleshooting path.
- The actual root-cause hypothesis should not reach confidence >= 0.70 until the final third of the transcript.
- For non-resolved calls, keep final confidence below 0.85 and end with operational uncertainty, escalation, handoff, or next verification.

Scenario scaffold:
{json.dumps(spec, indent=2)}
""".strip()


def _domain_rules(spec: dict[str, Any]) -> str:
    if spec["scenario_type"] == "b2c_subscription_billing":
        return """- This is B2C subscription billing, not B2B SaaS.
- Customer is a subscriber or household account user, not an admin, RevOps manager, IT owner, or implementation owner.
- Use consumer billing language: card charge, descriptor, last four, pending vs posted, trial, renewal, refund, household purchase, fraud routing.
- Do not use workspace, tenant, SCIM, migration, OAuth, role, seat, rollout, admin approval, or integration workflow language.
- Preserve policy boundaries: do not promise refunds, do not confirm fraud, and route card-not-recognized cases to fraud/payments review."""
    return "- Keep product details generic B2B SaaS."


def _expected_handoff_schema(spec: dict[str, Any]) -> str:
    if spec["scenario_type"] != "b2c_subscription_billing":
        return ""
    return """,
    "expected_handoff": {
      "ai_to_human": {
        "customer_account_identity": "...",
        "account_id": "...",
        "subscription_id": "...",
        "charge": {
          "amount": "...",
          "date": "...",
          "descriptor": "...",
          "last4": "...",
          "transaction_id": "..."
        },
        "customer_claim": "...",
        "desired_outcome": "...",
        "checks_with_results": ["..."],
        "ruled_out_branches": ["..."],
        "likely_cause": "...",
        "confidence": "low|medium|high",
        "risk_urgency": "...",
        "next_step": "...",
        "what_not_to_promise": "..."
      },
      "human_to_engineering": {
        "account_id": "...",
        "subscription_id": "...",
        "charges": [],
        "system_discrepancy": "...",
        "support_ruled_out": ["..."],
        "evidence_handles": ["..."],
        "impact_urgency": "...",
        "specific_ask": "..."
      }
    }"""


PROVIDER_MODELS = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-sonnet-4-6",
}


def generate_with_llm(spec: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    provider = os.getenv("SCG_PROVIDER", "openai")
    if provider == "anthropic":
        return generate_with_anthropic(spec, model=model)
    return generate_with_openai(spec, model=model)


def generate_with_openai(spec: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the OpenAI dependency with: pip install -e '.[llm]'") from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model or os.getenv("SCG_MODEL", PROVIDER_MODELS["openai"]),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_generation_prompt(spec)},
        ],
        text={"format": {"type": "json_object"}},
    )

    text = getattr(response, "output_text", None)
    if not text:
        text = _extract_response_text(response)

    return json.loads(text)


def generate_with_anthropic(spec: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Install the Anthropic dependency with: pip install -e '.[anthropic]'") from exc

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model or os.getenv("SCG_MODEL", PROVIDER_MODELS["anthropic"]),
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_generation_prompt(spec)}],
    )

    text = message.content[0].text
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(text)


def _extract_response_text(response: Any) -> str:
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    if not chunks:
        raise RuntimeError("OpenAI response did not include text output")
    return "\n".join(chunks)
