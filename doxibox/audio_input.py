from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional

from .config import DoxiConfig
from .asr import WhisperASR


@dataclass
class CapturedAudio:
    """A captured utterance.

    The text is filled via ASR for microphone recordings, or directly when using
    text-based simulation.
    """

    text: str
    path: Optional[Path] = None
    sample_rate: Optional[int] = None


class AudioInput:
    """Microphone + text fallback input pipeline."""

    def __init__(self, config: DoxiConfig, asr: Optional[WhisperASR] = None) -> None:
        self.config = config
        self.asr = asr

    # --- Public API -----------------------------------------------------
    def record(self, prompts: Optional[List[str]] = None) -> Iterable[CapturedAudio]:
        if prompts is not None:
            yield from self._record_text(prompts)
            return
        if self.config.input_mode != "microphone":
            raise ValueError("Input mode is not 'microphone'. Provide prompts or switch modes.")
        if self.asr is None:
            raise RuntimeError("Microphone mode requires an ASR instance (WhisperASR).")
        yield from self._record_microphone()

    # --- Text mode ------------------------------------------------------
    def _record_text(self, prompts: List[str]) -> Iterable[CapturedAudio]:
        for chunk in prompts:
            yield CapturedAudio(text=chunk)

    # --- Microphone mode ------------------------------------------------
    def _record_microphone(self) -> Iterator[CapturedAudio]:
        sd = self._load_sounddevice()
        cache_dir = self.config.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("Press Enter to record. Type 'q' and Enter to quit.")
        while True:
            user = input(">>> Ready. Hit Enter to capture up to %ss: " % self.config.max_record_seconds)
            if user.strip().lower() == "q":
                break
            audio = self._capture_once(sd)
            wav_path = cache_dir / "capture.wav"
            self._write_wav(wav_path, audio, self.config.sample_rate)
            transcript = self.asr.transcribe_text(wav_path)
            yield CapturedAudio(text=transcript, path=wav_path, sample_rate=self.config.sample_rate)

    def _capture_once(self, sd_module) -> Any:
        import numpy as np  # lazy import to keep text-mode lightweight

        duration = self.config.max_record_seconds
        print("Recording...")
        frames = sd_module.rec(
            int(duration * self.config.sample_rate),
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype="float32",
        )
        sd_module.wait()
        audio = np.squeeze(frames)
        print("Captured.")
        return audio

    # --- Utilities ------------------------------------------------------
    def _write_wav(self, path: Path, audio: Any, sample_rate: int) -> None:
        import numpy as np  # lazy import

        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            max_amp = np.iinfo(np.int16).max
            wf.writeframes((audio * max_amp).astype(np.int16).tobytes())

    def _load_sounddevice(self):
        try:  # pragma: no cover - optional external dependency
            import sounddevice as sd  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Microphone mode requires the 'sounddevice' package. Install with 'pip install doxibox[audio]'."
            ) from exc
        return sd
