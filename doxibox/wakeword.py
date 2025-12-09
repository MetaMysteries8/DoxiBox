from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .audio_input import CapturedAudio


@dataclass
class WakeWordEvent:
    text: str
    triggered: bool


class WakeWordDetector:
    """Lightweight wake word detector based on string matching.

    This keeps the interface expandable so that a future DSP-based detector can
    be swapped in without touching the consumer code. For now, it simply checks
    text fragments for the configured wake word.
    """

    def __init__(self, wake_word: str = "doxi") -> None:
        self.wake_word = wake_word.lower()

    def detect(self, stream: Iterable[str | CapturedAudio]) -> Iterable[WakeWordEvent]:
        for item in stream:
            if isinstance(item, CapturedAudio):
                text = item.text
            else:
                text = item
            normalized = text.strip().lower()
            yield WakeWordEvent(text=text, triggered=self.wake_word in normalized)
