from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .config import DoxiConfig


@dataclass
class TranscriptSegment:
    text: str
    confidence: float = 1.0


class WhisperASR:
    """Whisper wrapper with lazy loading.

    Uses the `openai-whisper` reference implementation by default. When the
    dependency is missing, a clear error guides the user to install the ASR
    extras.
    """

    def __init__(self, config: DoxiConfig) -> None:
        self.config = config
        self._whisper = None

    def _load_model(self):
        if self._whisper:
            return self._whisper
        try:  # pragma: no cover - optional dependency
            import whisper  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "WhisperASR requires 'openai-whisper'. Install with 'pip install doxibox[asr]'"
            ) from exc
        device = None if self.config.device == "auto" else self.config.device
        self._whisper = whisper.load_model(self.config.model_size, device=device)
        return self._whisper

    def transcribe(self, audio_path_or_bytes: str | bytes | Path) -> List[TranscriptSegment]:
        whisper_model = self._load_model()
        if isinstance(audio_path_or_bytes, (str, Path)):
            result = whisper_model.transcribe(str(audio_path_or_bytes))
        else:
            result = whisper_model.transcribe(audio_path_or_bytes)
        text = (result.get("text") or "").strip()
        return [TranscriptSegment(text=text, confidence=float(result.get("confidence", 1.0)))]

    def transcribe_text(self, audio_path_or_bytes: str | bytes | Path) -> str:
        segments = self.transcribe(audio_path_or_bytes)
        return " ".join(segment.text for segment in segments if segment.text)

    def transcribe_streaming(self, audio_stream: Sequence[str | bytes]) -> Iterable[TranscriptSegment]:
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                text = chunk.decode("utf-8", errors="ignore")
            else:
                text = str(chunk)
            yield TranscriptSegment(text=text.strip())
