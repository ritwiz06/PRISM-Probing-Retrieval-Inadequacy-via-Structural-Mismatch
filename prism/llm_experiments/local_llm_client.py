from __future__ import annotations

from dataclasses import dataclass
import json
import os
import urllib.error
import urllib.request


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    available: bool
    model: str
    provider: str
    raw: dict[str, object]
    error: str = ""


class LocalLLMClient:
    """Small Ollama-compatible local LLM client.

    The client is deliberately minimal and optional. A failed local connection
    is represented as an unavailable response so analysis CLIs can still write
    honest partial artifacts.
    """

    def __init__(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.provider = provider or os.environ.get("PRISM_LLM_PROVIDER", "ollama")
        self.model = model or os.environ.get("PRISM_LLM_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))
        self.endpoint = endpoint or os.environ.get("PRISM_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else float(os.environ.get("PRISM_LLM_TIMEOUT", "2.0"))

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> LLMResponse:
        if self.provider != "ollama":
            return LLMResponse(
                text="",
                available=False,
                model=self.model,
                provider=self.provider,
                raw={},
                error=f"Unsupported local LLM provider: {self.provider}",
            )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return LLMResponse(
                text="",
                available=False,
                model=self.model,
                provider=self.provider,
                raw={},
                error=str(exc),
            )
        return LLMResponse(
            text=str(raw.get("response", "")).strip(),
            available=True,
            model=self.model,
            provider=self.provider,
            raw=raw,
            error="",
        )

    def diagnostics(self) -> dict[str, object]:
        probe = self.complete(
            'Return exactly this JSON: {"route":"dense","confidence":0.5,"rationale":"probe"}',
            max_tokens=48,
        )
        return {
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "available": probe.available,
            "error": probe.error,
        }

