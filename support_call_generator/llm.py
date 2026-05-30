from __future__ import annotations

import json
import os
from typing import Any

from support_call_generator.doctrines import render_doctrines


SYSTEM_PROMPT = """You generate synthetic B2B SaaS support calls for evaluation.
Return only valid JSON. Do not include markdown fences.
The transcript must be realistic, operationally difficult, and not too clean.
Keep hidden ground truth consistent with the scenario scaffold.
The simulator doctrines are mandatory and override natural dialogue instincts."""


def build_generation_prompt(spec: dict[str, Any]) -> str:
    return f"""
Create one realistic support-call case from this scaffold.

Mandatory simulator doctrines:
{render_doctrines()}

Rules:
- 16 to 28 turns.
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
- Keep product details generic B2B SaaS.

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
    "final_outcome": "..."
  }},
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
        model=model or os.getenv("SCG_MODEL", "gpt-5.4-mini"),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_generation_prompt(spec)},
        ],
    )

    text = getattr(response, "output_text", None)
    if not text:
        text = _extract_response_text(response)

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
