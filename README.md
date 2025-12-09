# Doxibox

A functional, cross‑platform voice assistant core that follows the architecture in `Doxibox-Final-Plan.txt`. It works locally with microphone capture, Whisper ASR, on-device TTS, wake-word gating, and pluggable LLM providers (OpenAI for cloud chat completions, Modal for cloud-executed functions, and a local echo path for offline use).

## Features
- Wake-word scanning (`WakeWordDetector`) on transcribed utterances
- Microphone capture with WAV export plus text-mode fallback for testing
- Whisper ASR wrapper with lazy loading and configurable model size/device
- TTS output via `pyttsx3` (or text-only logging)
- LLM routing: local echo, OpenAI Chat Completions, Modal remote function hook
- Agent Mode surface that preserves reasoning steps while returning a spoken reply
- CLI entry point usable in both text simulation and live microphone mode

## Quickstart

Interactive setup scripts bootstrap a virtual environment and let you pick optional features.

### macOS / Linux
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Windows (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pwsh -File scripts/setup.ps1
```

During setup you can opt into:
- `audio` (microphone capture via `sounddevice`)
- `tts` (offline `pyttsx3` speech)
- `asr` (Whisper speech-to-text)
- `llm` (OpenAI client for Chat Completions)
- `modal` (remote provider)

After installation, activate the environment (scripts print the command) and verify:

```bash
pytest
```

## Running the assistant

### Text simulation (no audio hardware needed)
```python
from doxibox import run_cli

responses = run_cli([
    "hello there",
    "Doxi what is the weather?",
    "thanks!",
])
for line in responses:
    print(line)
```

### Live microphone loop
```bash
python -m doxibox.cli  # uses microphone when input_mode=microphone
```

Configure microphone mode by passing overrides:

```python
from doxibox import run_cli

config = {
    "input_mode": "microphone",
    "output_mode": "tts",            # speak aloud via pyttsx3
    "model_size": "small",          # Whisper model size
    "llm_provider": "openai",       # or "modal" / "local-echo"
    "provider_options": {"openai": {"model": "gpt-4o-mini"}},
}

run_cli(prompts=None, config_dict=config)
```
When prompted, press **Enter** to record up to the configured duration, or type `q` to exit. Captured audio is saved in `.cache/doxibox/capture.wav` for inspection.

## Provider setup
- **OpenAI:** set `OPENAI_API_KEY` in your environment and install `pip install doxibox[llm]`.
- **Modal (cloud-only):** `pip install modal` then `python3 -m modal setup`; set `llm_provider="modal"` and point `provider_options["modal"]["function_path"]` at your deployed Modal function handle. Modal always executes remotely and requires internet access; use the `local-echo` provider for offline runs.
- **Local echo:** default, no network or dependencies.

## ASR & Audio notes
- Install FFmpeg for Whisper to decode WAV/MP3/FLAC (e.g., `brew install ffmpeg`, `apt-get install ffmpeg`, or [ffmpeg.org/download](https://ffmpeg.org/download.html)).
- If you prefer not to install audio dependencies, keep `input_mode="text"` and `output_mode="text"` for simulation/testing.

## Troubleshooting
- Missing dependency errors include the exact `pip install` extras group to enable the feature.
- If microphone capture is silent, confirm your OS privacy settings allow microphone access and select the correct default input device in system preferences.
- Whisper model downloads can be large; set `model_size` to `tiny` or `base` for quicker setup on constrained devices.
