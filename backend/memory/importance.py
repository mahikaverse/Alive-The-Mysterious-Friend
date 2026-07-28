"""Importance scoring.

Evaluates how important a piece of information is
to decide which memories should be retained long-term.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Keywords that signal high-importance content
_PERSONAL_KEYWORDS = frozenset({
    "name", "age", "birthday", "born", "live", "lives", "from",
    "family", "mother", "father", "sister", "brother", "parent",
    "friend", "boyfriend", "girlfriend", "partner", "husband", "wife",
    "love", "hate", "fear", "dream", "goal", "wish", "hope",
    "school", "university", "college", "work", "job", "career",
    "hobby", "music", "movie", "book", "game", "sport",
    "food", "drink", "travel", "pet", "cat", "dog",
    "feel", "feeling", "emotion", "happy", "sad", "angry", "scared",
    "remember", "forget", "important", "never", "always",
})

_EMOTIONAL_KEYWORDS = frozenset({
    "love", "hate", "miss", "lonely", "excited", "nervous",
    "proud", "ashamed", "grateful", "jealous", "confused",
    "anxious", "depressed", "hopeful", "desperate",
})

_QUESTION_SIGNALS = frozenset({
    "what", "when", "where", "who", "how", "why",
    "which", "whose", "whom",
})

_INTENSIFIERS = frozenset({
    "very", "really", "extremely", "absolutely", "totally",
    "completely", "always", "never", "most", "best", "worst",
})


class ImportanceScorer:
    """Scores the importance of content for long-term retention.

    Uses a heuristic approach based on keyword signals, message
    length, emotional content, and question density.
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold

    def score(self, content: str, context: dict | None = None) -> float:
        """Compute an importance score for the given content.

        Parameters
        ----------
        content : str
            The text to evaluate.
        context : dict | None
            Optional context (conversation history, emotional state, etc.).

        Returns
        -------
        float
            Importance score between 0.0 and 1.0.
        """
        if not content or not content.strip():
            return 0.0

        text = content.lower().strip()
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0

        score = 0.0

        # --- Length signal ---
        if word_count >= 5:
            score += 0.1
        if word_count >= 15:
            score += 0.05

        # --- Personal information signal ---
        personal_hits = sum(1 for w in words if w in _PERSONAL_KEYWORDS)
        personal_ratio = min(personal_hits / max(word_count, 1), 0.3)
        score += personal_ratio * 0.4

        # --- Emotional content signal ---
        emotional_hits = sum(1 for w in words if w in _EMOTIONAL_KEYWORDS)
        emotional_ratio = min(emotional_hits / max(word_count, 1), 0.3)
        score += emotional_ratio * 0.25

        # --- Question signal ---
        if text.rstrip().endswith("?"):
            score += 0.1
        question_starts = sum(1 for w in words[:3] if w in _QUESTION_SIGNALS)
        if question_starts > 0:
            score += 0.05

        # --- Intensifier signal ---
        intensifier_hits = sum(1 for w in words if w in _INTENSIFIERS)
        score += min(intensifier_hits * 0.03, 0.1)

        # --- Exclamation / caps signal ---
        exclamation_count = content.count("!")
        if exclamation_count > 0:
            score += min(exclamation_count * 0.03, 0.1)

        caps_words = sum(1 for w in content.split() if w.isupper() and len(w) > 1)
        if caps_words > 0:
            score += min(caps_words * 0.02, 0.08)

        # --- Context boost ---
        if context:
            emotional_state = context.get("emotion", {})
            mood = emotional_state.get("mood", "neutral")
            if mood in ("excited", "happy", "grateful", "proud"):
                score += 0.05

            relationship = context.get("relationship", {})
            trust = relationship.get("trust", 0.5)
            if trust > 0.7:
                score += 0.05

        return min(round(score, 4), 1.0)

    def should_store(self, score: float, threshold: float | None = None) -> bool:
        """Determine whether content exceeds the storage threshold.

        Parameters
        ----------
        score : float
            The computed importance score.
        threshold : float | None
            Override the default threshold.

        Returns
        -------
        bool
            True if the score meets or exceeds the threshold.
        """
        t = threshold if threshold is not None else self._threshold
        return score >= t
