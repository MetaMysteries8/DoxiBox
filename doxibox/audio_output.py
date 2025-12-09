from __future__ import annotations

from typing import Iterable

from .config import DoxiConfig


class AudioOutput:
    """Text logging plus optional on-device TTS."""

    def __init__(self, config: DoxiConfig) -> None:
        self.config = config
        self.history: list[str] = []
        self._tts_engine = None

    def speak(self, text: str) -> None:
        rendered = f"[voice:{self.config.language}] {text}"
        self.history.append(rendered)
        if self.config.output_mode == "tts":
            engine = self._load_tts()
            engine.say(text)
            engine.runAndWait()

    def play_notifications(self, notes: Iterable[str]) -> None:
        for note in notes:
            self.history.append(f"[notification] {note}")
            if self.config.output_mode == "tts":
                engine = self._load_tts()
                engine.say(note)
        if self.config.output_mode == "tts" and self.history:
            engine = self._load_tts()
            engine.runAndWait()

    def _load_tts(self):
        if self._tts_engine:
            return self._tts_engine
        try:  # pragma: no cover - optional dependency
            import pyttsx3  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Text-to-speech requires 'pyttsx3'. Install with 'pip install doxibox[tts]'."
            ) from exc
        self._tts_engine = pyttsx3.init()
        self._tts_engine.setProperty("rate", 175)
        return self._tts_engine
