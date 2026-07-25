"""Behaviour models.

Pydantic models specific to the human behaviour layer
for emotion, relationship, and life-simulation data.
"""

from pydantic import BaseModel


class EmotionSnapshot(BaseModel):
    """A snapshot of the character's emotional state at a point in time."""

    mood: str
    confidence: float
    trust: float
    stress: float
    energy: float


class RelationshipSnapshot(BaseModel):
    """A snapshot of the relationship with the user."""

    friendship_score: float
    trust_level: float
    conversation_count: int
    shared_experiences: list[str]


class LifeEvent(BaseModel):
    """A single simulated life event."""

    title: str
    description: str
    timestamp: str
    category: str
