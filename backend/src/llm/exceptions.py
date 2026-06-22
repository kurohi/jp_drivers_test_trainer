"""LLM exception classes."""


class OllamaUnavailableError(Exception):
    """Raised when Ollama host cannot be reached (connection error)."""

    pass


class OllamaResponseError(Exception):
    """Raised when Ollama returns a non-success HTTP status after retries."""

    pass


class StudyPlanParseError(Exception):
    """Raised when the LLM study plan response cannot be parsed or violates schema constraints.

    This includes:
    - Malformed JSON that cannot be decoded
    - JSON that does not conform to the StudyPlanOut schema
    - Hallucinated theme_ids not present in the allowed weak_theme_ids set
    """

    pass
