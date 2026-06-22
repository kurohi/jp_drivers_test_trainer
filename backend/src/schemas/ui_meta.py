"""UI meta types — shared Literal types used across all schemas."""

from typing import Literal

Language = Literal["en", "pt"]
Difficulty = Literal[0.0, 0.25, 0.5, 0.75, 1.0]
