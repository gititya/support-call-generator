from __future__ import annotations

import random
from typing import Any


DIFFICULTY_PROFILES: dict[str, dict[str, Any]] = {
    "simple": {
        "turn_range": (12, 16),
        "hypothesis_count": (1, 2),
        "context_event_count": (1, 2),
        "irrelevant_context_count": (0, 0),
        "conflicting_context_count": (0, 0),
        "customer_corrections": (0, 1),
        "agent_quality_weights": {"good": 60, "average": 30, "confused": 5, "overly_rigid": 5},
        "resolution_weights": {"resolved": 70, "probable_cause": 20, "escalated": 5, "handoff": 5, "unresolved": 0},
        "final_cause_confirmed": True,
    },
    "hard": {
        "turn_range": (16, 28),
        "hypothesis_count": (2, 4),
        "context_event_count": (2, 3),
        "irrelevant_context_count": (0, 1),
        "conflicting_context_count": (0, 1),
        "customer_corrections": (1, 2),
        "agent_quality_weights": {"good": 20, "average": 40, "confused": 25, "overly_rigid": 15},
        "resolution_weights": {"resolved": 20, "probable_cause": 40, "escalated": 25, "handoff": 10, "unresolved": 5},
        "final_cause_confirmed": True,
    },
    "harder": {
        "turn_range": (22, 32),
        "hypothesis_count": (3, 5),
        "context_event_count": (3, 5),
        "irrelevant_context_count": (1, 2),
        "conflicting_context_count": (1, 2),
        "customer_corrections": (2, 3),
        "agent_quality_weights": {"good": 10, "average": 30, "confused": 30, "overly_rigid": 30},
        "resolution_weights": {"resolved": 5, "probable_cause": 30, "escalated": 35, "handoff": 20, "unresolved": 10},
        "final_cause_confirmed": False,
    },
}

PROFILE_NAMES = list(DIFFICULTY_PROFILES.keys())


def apply_profile(spec: dict[str, Any], profile_name: str, rng: random.Random) -> None:
    if profile_name not in DIFFICULTY_PROFILES:
        raise ValueError(f"Unknown profile '{profile_name}'. Expected one of: {', '.join(PROFILE_NAMES)}")

    profile = DIFFICULTY_PROFILES[profile_name]

    difficulty_map = {"simple": "easy", "hard": "hard", "harder": "hard"}
    spec["difficulty"] = difficulty_map[profile_name]
    spec["difficulty_metadata"]["difficulty"] = difficulty_map[profile_name]

    spec["agent_quality"] = _weighted_choice(rng, profile["agent_quality_weights"])
    spec["resolution_type"] = _weighted_choice(rng, profile["resolution_weights"])
    spec["resolution_outcome"] = _resolution_outcome(spec["resolution_type"])

    spec["profile"] = {"name": profile_name, **profile}


def _weighted_choice(rng: random.Random, weights: dict[str, int]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def _resolution_outcome(resolution_type: str) -> str:
    return {
        "resolved": "clear resolution reached during the call",
        "probable_cause": "probable cause identified but verification remains",
        "escalated": "escalated to engineering or product with operational state preserved",
        "handoff": "handed off to customer admin, identity team, or implementation owner",
        "unresolved": "investigation remains open with incomplete evidence",
    }[resolution_type]
