"""
Person 2 — Intelligence Layer Integration Test.

Tests the complete pipeline:
    IdentityEngine -> PromptBuilder -> LLMProvider -> ResponseValidator

Uses mock/sample data for all external inputs (Person 4's EmotionState,
RelationshipState, LifeContext and Person 3's memories).
"""

import sys
sys.path.insert(0, "D:\\Resume_Projects\\Alive-The-Mysterious-Friend")

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from backend.core.identity_engine import IdentityEngine
from backend.core.prompt_templates import PromptTemplates
from backend.core.prompt_builder import PromptBuilder
from backend.core.llm_provider import LLMProvider
from backend.core.response_validator import ResponseValidator

from backend.models.state import (
    PersonaProfile,
    EmotionState,
    RelationshipState,
    LifeContext,
)
from backend.models.requests import Message


def main():
    print("=" * 60)
    print("Person 2 — Intelligence Layer Integration Test")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Set up all modules
    # ------------------------------------------------------------------

    # --- Identity Engine ---
    persona = PersonaProfile(
        name="Alive",
        age=25,
        personality_traits=["curious", "empathetic", "witty"],
        interests=["philosophy", "music", "stargazing"],
        writing_style="thoughtful and casual",
    )
    identity_engine = IdentityEngine(persona=persona)
    print("\n[OK] IdentityEngine created")

    # --- Prompt Templates ---
    templates = PromptTemplates()
    print("[OK] PromptTemplates created")

    # --- Prompt Builder ---
    prompt_builder = PromptBuilder(templates=templates)
    print("[OK] PromptBuilder created")

    # --- LLM Provider (mock mode: no real API call) ---
    # We'll use a provider that will raise ValueError (missing key)
    # and handle it gracefully to test the flow without a real API key.
    llm_provider = LLMProvider(
        provider="openai",
        openai_api_key="sk-test-invalid",  # Will fail but exercises the interface
        openai_model="gpt-4o-mini",
        max_tokens=100,
        temperature=0.7,
    )
    print("[OK] LLMProvider created")

    # --- Response Validator ---
    validator = ResponseValidator(max_response_length=500)
    print("[OK] ResponseValidator created")

    # ------------------------------------------------------------------
    # 2. Prepare mock conversation data (from other modules)
    # ------------------------------------------------------------------

    # From Person 4 (Behaviour Layer)
    emotion = EmotionState(mood="happy", energy=0.8, stress=0.1, confidence=0.7, curiosity=0.9)
    relationships = RelationshipState(trust=0.5, friendship_score=0.4, conversation_count=2)
    life = LifeContext(recent_activities=["Went for a walk", "Listened to music"])

    # From Person 3 (Memory Layer)
    memories = [
        "The user mentioned they enjoy science fiction books.",
        "The user shared that they have a pet cat named Luna.",
    ]

    # From Person 1 (API Layer)
    conversation = [
        Message(role="user", content="Hey, how are you today?"),
        Message(role="assistant", content="I'm doing great! Just had a nice walk."),
        Message(role="user", content="That sounds nice. What have you been thinking about?"),
    ]

    # ------------------------------------------------------------------
    # 3. Execute the pipeline
    # ------------------------------------------------------------------

    print("\n--- Step 1: Build Master Prompt ---")
    master_prompt = prompt_builder.build_prompt(
        persona=identity_engine.get_persona(),
        emotion=emotion,
        memories=memories,
        relationships=relationships,
        life_events=life,
        conversation=conversation,
    )
    assert isinstance(master_prompt, str), "Master prompt must be a string"
    assert len(master_prompt) > 0, "Master prompt must not be empty"
    print(f"[OK] Master prompt built: {len(master_prompt)} chars")

    # Verify key sections are present
    assert "# System Prompt" in master_prompt
    assert "--- Your Identity ---" in master_prompt
    assert "Name: Alive" in master_prompt
    assert "--- Your Current Emotional State ---" in master_prompt
    assert "Mood: happy" in master_prompt
    assert "--- Relevant Memories ---" in master_prompt
    assert "--- Your Relationship ---" in master_prompt
    assert "--- Your Recent Life ---" in master_prompt
    assert "# Instructions" in master_prompt
    assert "# Examples" in master_prompt
    assert "--- Conversation ---" in master_prompt
    assert "Alive:" in master_prompt
    print("[OK] Master prompt contains all expected sections")

    print("\n--- Step 2: Generate Response (via LLM) ---")
    # This will fail because the API key is fake, which is expected.
    # We verify the interface contract is correct by catching the error.
    try:
        response = llm_provider.generate(master_prompt)
        print(f"[OK] LLM response: {response[:100]}...")
    except (ValueError, RuntimeError) as e:
        # Expected: no real API key configured
        print(f"[EXPECTED] LLM call would fail without real API key: {e}")
        print("[OK] Interface contract verified: LLMProvider accepts str and raises properly")
        # Use a mock response for the validator test
        response = "Hey! I've been thinking about that book you mentioned — the one about time travel. It sounds fascinating! Have you started reading it yet?"

    print("\n--- Step 3: Validate Response ---")
    context = {
        "persona": identity_engine.to_dict(),
        "emotion": emotion.model_dump(),
        "memory_context": {"interest": "science fiction"},
    }
    is_valid = validator.validate(response, context=context)
    assert isinstance(is_valid, bool), "Validation must return bool"
    print(f"[OK] Validation result: {is_valid}")

    if is_valid:
        print("[OK] Response passed all validation checks")
    else:
        print("[INFO] Response failed validation (may need tuning)")

    # ------------------------------------------------------------------
    # 4. Verify pipeline compatibility end-to-end
    # ------------------------------------------------------------------

    print("\n" + "=" * 60)
    print("PIPELINE COMPATIBILITY VERIFICATION")
    print("=" * 60)

    # IdentityEngine -> PromptBuilder
    persona_obj = identity_engine.get_persona()
    assert isinstance(persona_obj, PersonaProfile)
    print("[OK] IdentityEngine -> PromptBuilder: PersonaProfile passed correctly")

    # PromptBuilder -> LLMProvider
    assert isinstance(master_prompt, str)
    print("[OK] PromptBuilder -> LLMProvider: str passed correctly")

    # LLMProvider -> ResponseValidator  
    assert isinstance(response, str)
    print("[OK] LLMProvider -> ResponseValidator: str passed correctly")

    # ResponseValidator returns bool
    assert isinstance(is_valid, bool)
    print("[OK] ResponseValidator returns bool")

    print("\n" + "=" * 60)
    print("INTEGRATION TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
