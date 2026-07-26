"""Embeddings pipeline.

Generates vector embeddings for memory content
using the OpenAI embeddings API.
"""

import logging
import time

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "text-embedding-3-small"
_DEFAULT_DIMENSIONS = 1536
_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_RETRIES = 2


class Embeddings:
    """Generates vector embeddings for text content via OpenAI.

    Usage::

        emb = Embeddings(api_key="sk-...", model="text-embedding-3-small")
        vector = emb.embed("Hello world")
        vectors = emb.embed_batch(["Hello", "World"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._api_key = api_key or ""
        self._model = model or _DEFAULT_MODEL
        self._dimensions = dimensions or _DEFAULT_DIMENSIONS
        self._timeout = timeout or _DEFAULT_TIMEOUT
        self._max_retries = max_retries or _DEFAULT_MAX_RETRIES
        self._client = None

        if self._api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self._api_key,
                    timeout=self._timeout,
                    max_retries=self._max_retries,
                )
                logger.info(
                    "Embeddings ready (model=%s, dimensions=%d)",
                    self._model,
                    self._dimensions,
                )
            except Exception as exc:
                logger.error("Failed to initialize OpenAI client: %s", exc)
                self._client = None
        else:
            logger.warning("No OpenAI API key provided — embeddings will return zero vectors")

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Parameters
        ----------
        text : str
            The text to embed.

        Returns
        -------
        list[float]
            The embedding vector, or a zero vector on failure.
        """
        if not text or not text.strip():
            return [0.0] * self._dimensions

        if self._client is None:
            return [0.0] * self._dimensions

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=text,
                dimensions=self._dimensions,
            )
            vector = response.data[0].embedding
            logger.debug("Embedding generated (%d dims, %d chars input)", len(vector), len(text))
            return vector
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            return [0.0] * self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        Parameters
        ----------
        texts : list[str]
            List of texts to embed.

        Returns
        -------
        list[list[float]]
            List of embedding vectors. Failed items become zero vectors.
        """
        if not texts:
            return []

        if self._client is None:
            return [[0.0] * self._dimensions for _ in texts]

        non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        results: list[list[float]] = [[0.0] * self._dimensions for _ in texts]

        if not non_empty:
            return results

        try:
            batch_texts = [t for _, t in non_empty]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch_texts,
                dimensions=self._dimensions,
            )

            for idx, (original_idx, _) in enumerate(non_empty):
                if idx < len(response.data):
                    results[original_idx] = response.data[idx].embedding

            logger.debug("Batch embedding generated (%d vectors)", len(non_empty))
            return results
        except Exception as exc:
            logger.error("Batch embedding generation failed: %s", exc)
            return [[0.0] * self._dimensions for _ in texts]
