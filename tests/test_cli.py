from doxibox import run_cli, DoxiConfig


def test_run_cli_triggers_on_wake_word():
    prompts = ["hello", "Doxi tell me a joke", "bye"]
    outputs = run_cli(prompts)
    assert outputs == ["[voice:en] Doxibox heard: Doxi tell me a joke"]


def test_agent_mode_outputs_steps():
    prompts = ["nothing", "doxi plan the day"]
    outputs = run_cli(prompts, {"enable_agent_mode": True})
    # Agent mode still produces audible output, but includes context marker.
    assert "agent-mode" in outputs[0]
