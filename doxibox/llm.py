from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Optional

from .config import DoxiConfig


@dataclass
class LLMResponse:
    text: str
    provider: str


class BaseProvider:
    name = "base"

    def generate(self, prompt: str, context: Optional[str] = None) -> LLMResponse:
        raise NotImplementedError

    def generate_streaming(self, prompt: str, context: Optional[str] = None) -> Iterator[str]:
        raise NotImplementedError


class EchoProvider(BaseProvider):
    name = "local-echo"

    def __init__(self, prefix: str = "Doxibox") -> None:
        self.prefix = prefix

    def generate(self, prompt: str, context: Optional[str] = None) -> LLMResponse:
        parts = [self.prefix, "heard:", prompt]
        if context:
            parts.append(f"(context: {context})")
        return LLMResponse(text=" ".join(parts), provider=self.name)

    def generate_streaming(self, prompt: str, context: Optional[str] = None) -> Iterator[str]:
        yield from self.generate(prompt, context=context).text.split()


class ModalProvider(BaseProvider):
    """Optional Modal-based provider for remote LLM execution.

    Modal always runs in the cloud; this client simply forwards requests over
    the network. It defers imports until a request is made so that local/offline
    users can keep the dependency optional.

    ```bash
    pip install modal
    python3 -m modal setup
    ```

    After setup, configure `DoxiConfig.llm_provider` to `"modal"` and supply a
    `function_path` that points to a deployed Modal function capable of
    returning a text string. Use the `local-echo` provider instead when
    operating fully offline.
    """

    name = "modal"

    def __init__(self, function_path: str = "doxibox.modal_app:run") -> None:
        self.function_path = function_path
        self._modal = None

    def _load_client(self):
        if self._modal:
            return self._modal
        try:  # pragma: no cover - depends on optional external dependency
            import modal  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "ModalProvider requires the 'modal' package. Install with 'pip install modal' "
                "and run 'python3 -m modal setup'."
            ) from exc
        self._modal = modal
        return self._modal

    def generate(self, prompt: str, context: Optional[str] = None) -> LLMResponse:
        modal = self._load_client()
        client = modal.Client()  # pragma: no cover - networked dependency
        function = client.function_handle(self.function_path)
        # The remote function should accept a prompt/context and return text.
        result = function.call(prompt=prompt, context=context)
        return LLMResponse(text=str(result), provider=self.name)

    def generate_streaming(self, prompt: str, context: Optional[str] = None) -> Iterator[str]:
        modal = self._load_client()
        client = modal.Client()  # pragma: no cover - networked dependency
        function = client.function_handle(self.function_path)
        result = function.call(prompt=prompt, context=context)
        if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
            for chunk in result:
                yield str(chunk)
        else:
            yield str(result)


class OpenAIProvider(BaseProvider):
    """OpenAI Chat Completions provider with streaming support."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._client = None

    def _load_client(self):
        if self._client:
            return self._client
        try:  # pragma: no cover - depends on external package
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "OpenAIProvider requires the 'openai' package. Install with 'pip install openai'"
            ) from exc
        self._client = OpenAI()
        return self._client

    def generate(self, prompt: str, context: Optional[str] = None) -> LLMResponse:
        client = self._load_client()
        sys_msg = context or "You are Doxibox, a concise voice assistant."
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content or ""
        return LLMResponse(text=text, provider=self.name)

    def generate_streaming(self, prompt: str, context: Optional[str] = None) -> Iterator[str]:
        client = self._load_client()
        sys_msg = context or "You are Doxibox, a concise voice assistant."
        stream = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:  # pragma: no cover - streaming path
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class LLMRouter:
    """Minimal provider router with a plugin-friendly surface."""

    def __init__(
        self, config: DoxiConfig, providers: Optional[Dict[str, BaseProvider]] = None
    ) -> None:
        self.config = config
        self.providers: Dict[str, BaseProvider] = providers or {}
        self.providers.setdefault(EchoProvider.name, EchoProvider())
        self._maybe_register_modal()
        self._maybe_register_openai()

    def _maybe_register_modal(self) -> None:
        modal_opts = self.config.provider_options.get(ModalProvider.name)
        if modal_opts is None:
            return
        function_path = modal_opts.get("function_path", "doxibox.modal_app:run")
        self.providers.setdefault(ModalProvider.name, ModalProvider(function_path))

    def _maybe_register_openai(self) -> None:
        openai_opts = self.config.provider_options.get(OpenAIProvider.name)
        if openai_opts is None:
            return
        model = openai_opts.get("model", "gpt-4o-mini")
        self.providers.setdefault(OpenAIProvider.name, OpenAIProvider(model))

    def register(self, provider: BaseProvider) -> None:
        self.providers[provider.name] = provider

    def _select(self) -> BaseProvider:
        return self.providers.get(
            self.config.llm_provider, self.providers[EchoProvider.name]
        )

    def generate(self, prompt: str, context: Optional[str] = None) -> LLMResponse:
        provider = self._select()
        return provider.generate(prompt, context=context)

    def generate_streaming(self, prompt: str, context: Optional[str] = None) -> Iterable[str]:
        provider = self._select()
        return provider.generate_streaming(prompt, context=context)
