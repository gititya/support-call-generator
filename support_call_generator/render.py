from __future__ import annotations

from typing import Any


def render_transcript_markdown(case_id: str, spec: dict[str, Any], transcript: dict[str, Any]) -> str:
    lines = [
        f"# {case_id}",
        "",
        f"- Scenario: `{spec['scenario_type']}`",
        f"- Customer mood: `{spec['customer_persona']['mood']}`",
        f"- Customer clarity: `{spec['customer_persona']['clarity']}`",
        f"- Customer patience: `{spec['customer_persona']['patience']}`",
        f"- Customer technical skill: `{spec['customer_persona']['technical_skill']}`",
        f"- Agent quality: `{spec['agent_quality']}`",
        "",
        "## Transcript",
        "",
    ]

    for turn in transcript["turns"]:
        speaker = turn["speaker"].title()
        lines.append(f"**{turn['turn']}. {speaker}:** {turn['text']}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
