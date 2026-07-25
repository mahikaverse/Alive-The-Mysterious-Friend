"""State models.

Pydantic schemas for internal state representation
shared across cognitive modules during the pipeline.
"""

from pydantic import BaseModel, Field


class EmotionState(BaseModel):
    """Current emotional state of the character."""

    mood: str = "neutral"
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    stress: float = Field(default=0.0, ge=0.0, le=1.0)
    energy: float = Field(default=0.7, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0)


class RelationshipState(BaseModel):
    """Current relationship state with the user."""

    friendship_score: float = Field(default=0.0, ge=0.0, le=1.0)
    trust: float = Field(default=0.0, ge=0.0, le=1.0)
    conversation_count: int = Field(default=0, ge=0)
    shared_experiences: list[str] = Field(default_factory=list)


class PersonaProfile(BaseModel):
    """Persistent identity profile of the character."""

    name: str = "Alive"
    age: int = Field(default=25, ge=1, le=150)
    interests: list[str] = Field(default_factory=list)
    writing_style: str = "casual"
    personality_traits: list[str] = Field(default_factory=list)
    opinions: dict[str, str] = Field(default_factory=dict)


class LifeContext(BaseModel):
    """Recent life simulation events."""

    recent_activities: list[str] = Field(default_factory=list)
    ongoing_events: list[str] = Field(default_factory=list)
    daily_routine: list[str] = Field(default_factory=list)


class PipelineContext(BaseModel):
    """Rich context object passed through the entire cognitive pipeline.

    Each step reads from and writes to this container.
    Modules that have not been implemented yet leave their
    section at default values.
    """

    conversation: list[dict] = Field(default_factory=list)
    current_message: str = ""
    metadata: dict = Field(default_factory=dict)

    memories: list[dict] = Field(default_factory=list)
    emotion: EmotionState = Field(default_factory=EmotionState)
    relationship: RelationshipState = Field(default_factory=RelationshipState)
    life_events: LifeContext = Field(default_factory=LifeContext)
    persona: PersonaProfile = Field(default_factory=PersonaProfile)
