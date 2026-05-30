from __future__ import annotations


SIMULATOR_DOCTRINES = [
    "Doctrine 1: Optimize for uncertainty, not realism. The call must stress-test reasoning through ambiguity.",
    "Doctrine 2: Hidden truth is sacred. Only the simulator knows the complete root cause and answer key.",
    "Doctrine 3: Information asymmetry is required. Customer, agent, and admin knowledge must be incomplete and different.",
    "Doctrine 4: Root causes should not appear directly. Diagnosis must emerge through investigation.",
    "Doctrine 5: Introduce misleading evidence. Use irrelevant clues, coincidental timing, incorrect assumptions, or partially true explanations.",
    "Doctrine 6: Generate wrong-but-plausible hypotheses. Each call needs one correct explanation and at least two plausible incorrect explanations.",
    "Doctrine 7: Force hypothesis evolution. Hypotheses should activate, strengthen, weaken, reverse, and resolve over time.",
    "Doctrine 8: Support calls are messy. Include incomplete answers, forgotten details, interruptions, corrections, and contradictions.",
    "Doctrine 9: Agents should not always be good. Agent quality must affect the troubleshooting path.",
    "Doctrine 10: Not every call should resolve. Some calls can escalate, hand off, or end with unresolved operational risk.",
    "Doctrine 11: Operational state matters more than dialogue. Ground truth, timeline, dead ends, and uncertainty are primary.",
    "Doctrine 12: Optimize for adversarial evaluation. If the answer feels obvious, delay it or add contradictory evidence.",
    "Doctrine 13: Prevent simulator leakage. Never reveal hidden root cause through unusually specific observations, convenient clues, intuition without evidence, or perfect troubleshooting.",
]


def render_doctrines() -> str:
    return "\n".join(f"- {doctrine}" for doctrine in SIMULATOR_DOCTRINES)
