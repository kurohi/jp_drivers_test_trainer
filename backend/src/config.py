"""Application settings — pydantic-settings with config.yaml merge."""

from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from config.yaml with .env overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
    )

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3.6-256k"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout_seconds: float = 60.0

    # Database
    db_url: str = "sqlite+aiosqlite:///data/jp_drivers.sqlite"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Internal storage for YAML config
    _config: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_config_yaml()

    def _load_config_yaml(self):
        """Load additional config from config.yaml (layered under .env values)."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            if config:
                self._config = config
                # Layer YAML values that were not set via env vars
                # BaseSettings already prefers env values over defaults,
                # so we only need to fill YAML-driven fields that have no env override.
                # pydantic_settings will handle env precedence automatically.
                for key, value in config.items():
                    if key not in self.model_fields_set and hasattr(self, key):
                        setattr(self, key, value)
