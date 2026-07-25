"""State models.

Pydantic schemas for internal state representation
shared across cognitive modules.
"""

from pydantic import BaseModel


class EmotionState(BaseModel):
    """Current emotional state of the character."""

    mood: str = "neutral"
    trust: float = 0.5
    stress: float = 0.0
    energy: float = 0.7
    confidence: float = 0.5
    curiosity: float = 0.5


class RelationshipState(BaseModel):
    """Current relationship state with the user."""

    friendship_score: float = 0.0
    trust: float = 0.0
    conversation_count: int = 0
    shared_experiences: list = []


class PersonaProfile(BaseModel):
    """Persistent identity profile of the character."""

    name: str = "Alive"
    age: int = 25
    interests: list = []
    writing_style: str = "casual"
    personality_traits: list = []
    opinions: dict = {}


class LifeContext(BaseModel):
    """Recent life simulation events."""

    recent_activities: list = []
    ongoing_events: list = []
    daily_routine: list = []
