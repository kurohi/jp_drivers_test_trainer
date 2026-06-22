"""LLM exception classes."""


class OllamaUnavailableError(Exception):
    """Raised when Ollama host cannot be reached (connection error)."""

    pass


class OllamaResponseError(Exception):
    """Raised when Ollama returns a non-success HTTP status after retries."""

    pass
