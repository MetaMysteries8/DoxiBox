from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


def _default_model_size() -> str:
    return "tiny"


def _default_llm_provider() -> str:
    return "local-echo"


@dataclass
class DoxiConfig:
    """Runtime configuration for the Doxibox assistant.

    The configuration mirrors the Final Plan at a high level while keeping the
    defaults lightweight enough to run in constrained environments.
    """

    wake_word: str = "doxi"
    model_size: str = field(default_factory=_default_model_size)
    llm_provider: str = field(default_factory=_default_llm_provider)
    language: str = "en"
    transcript_dir: Path = field(default_factory=lambda: Path("transcripts"))
    provider_options: Dict[str, Dict[str, str]] = field(default_factory=dict)
    cache_dir: Path = field(default_factory=lambda: Path(".cache/doxibox"))
    device: str = "auto"
    enable_agent_mode: bool = False
    input_mode: str = "text"  # text | microphone
    output_mode: str = "text"  # text | tts
    sample_rate: int = 16000
    channels: int = 1
    max_record_seconds: int = 15
    noise_floor: float = 0.01
    silence_timeout_s: float = 7.0
    logger_level: str = "INFO"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, object]]) -> "DoxiConfig":
        data = data or {}
        return cls(**data)

    def ensure_dirs(self) -> None:
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def summary(self) -> str:
        provider_details = ", ".join(
            f"{name}={options}" for name, options in self.provider_options.items()
        ) or "defaults"
        return (
            f"Wake word: '{self.wake_word}', model_size: {self.model_size}, "
            f"LLM provider: {self.llm_provider} ({provider_details}), "
            f"language: {self.language}, device: {self.device}, "
            f"agent mode: {self.enable_agent_mode}"
        )
