from __future__ import annotations

from typing import Iterable, List, Optional

from .agent import AgentOrchestrator
from .asr import WhisperASR
from .audio_input import AudioInput
from .audio_output import AudioOutput
from .config import DoxiConfig
from .llm import LLMRouter
from .wakeword import WakeWordDetector


def run_cli(prompts: Optional[List[str]] = None, config_dict: dict | None = None) -> List[str]:
    """Run the assistant pipeline.

    Args:
        prompts: Input prompts that simulate recorded utterances. If omitted and
            the configuration sets ``input_mode="microphone"``, the microphone
            capture flow is used.
        config_dict: Optional overrides for :class:`DoxiConfig`.

    Returns:
        The audio output history, which doubles as a transcript of the TTS layer.
    """

    config = DoxiConfig.from_dict(config_dict)
    config.ensure_dirs()

    asr = WhisperASR(config)
    llm = LLMRouter(config)
    agent = AgentOrchestrator(config, llm)
    audio_in = AudioInput(config, asr=asr)
    audio_out = AudioOutput(config)
    detector = WakeWordDetector(config.wake_word)

    stream = audio_in.record(prompts)
    for event in detector.detect(stream):
        if not event.triggered:
            continue
        agent_result = agent.run(event.text)
        audio_out.speak(agent_result.final_response)

    return audio_out.history


if __name__ == "__main__":  # pragma: no cover - manual entry point
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run Doxibox CLI assistant")
    parser.add_argument(
        "--mic",
        action="store_true",
        help="Use microphone mode (requires audio + asr extras)",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Enable agent mode with visible reasoning",
    )
    parser.add_argument("prompts", nargs="*", help="Text prompts in text mode")
    args = parser.parse_args()

    cfg_overrides = {"enable_agent_mode": args.agent}
    if args.mic:
        cfg_overrides["input_mode"] = "microphone"
    config = DoxiConfig.from_dict(cfg_overrides)
    history = run_cli(prompts=args.prompts or None, config_dict=cfg_overrides)
    print(json.dumps(history, indent=2))
