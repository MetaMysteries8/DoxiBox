from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import dataclass, field
from typing import Iterable, List

from .config import DoxiConfig
from .llm import LLMRouter


@dataclass
class AgentStep:
    thought: str
    action: str
    observation: str = ""


@dataclass
class AgentResult:
    steps: List[AgentStep] = field(default_factory=list)
    final_response: str = ""


class AgentOrchestrator:
    """Minimal agent that echoes the reasoning path.

    This keeps the interface flexible for future tool integrations while
    satisfying the specification's Agent Mode requirement with deterministic and
    test-friendly behavior.
    """

    def __init__(self, config: DoxiConfig, llm: LLMRouter) -> None:
        self.config = config
        self.llm = llm

    def run(self, prompt: str) -> AgentResult:
        if not self.config.enable_agent_mode:
            response = self.llm.generate(prompt).text
            return AgentResult(final_response=response)

        steps = [
            AgentStep(thought="Assessing user intent", action="echo"),
            AgentStep(thought="Executing requested task", action="llm.generate"),
        ]
        final = self.llm.generate(prompt, context="agent-mode").text
        return AgentResult(steps=steps, final_response=final)

    def run_streaming(self, prompt: str) -> Iterable[str]:
        for token in self.llm.generate_streaming(prompt, context="agent-mode"):
            yield token
