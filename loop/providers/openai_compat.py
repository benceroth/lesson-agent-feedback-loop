"""Optional OpenAI-compatible chat-completions provider (stdlib only).

Configuration comes from environment variables; nothing is hardcoded:

    LOOP_API_KEY           API key (optional for local servers)
    LOOP_BASE_URL          default https://api.openai.com/v1 (http only for localhost)
    LOOP_MODEL             model name for the builder
    LOOP_REVIEWER_MODEL    model for the reviewer (defaults to LOOP_MODEL)
    LOOP_TIMEOUT_SECONDS   per-request timeout (default 120)

Works with any server exposing /chat/completions (hosted APIs, Ollama, llama.cpp,
vLLM...). Prompts include task code, so only point it at endpoints you trust.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

from loop.providers.base import ProviderError, ProviderRequest, ProviderResponse, estimate_tokens

DEFAULT_BASE_URL = "https://api.openai.com/v1"
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 120.0, temperature: float = 0.0):
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ProviderError("LOOP_BASE_URL must be an http(s) URL")
        if parsed.scheme == "http" and parsed.hostname not in _LOCAL_HOSTS:
            raise ProviderError("plain http is only allowed for localhost; use https")
        if not model:
            raise ProviderError("LOOP_MODEL is not set")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._api_key = api_key
        self.timeout = timeout
        self.temperature = temperature

    @classmethod
    def from_env(cls, role: str = "builder", env: dict[str, str] | None = None) -> "OpenAICompatibleProvider":
        env = dict(os.environ) if env is None else env
        model = env.get("LOOP_MODEL", "")
        if role == "reviewer":
            model = env.get("LOOP_REVIEWER_MODEL", model)
        return cls(
            base_url=env.get("LOOP_BASE_URL", DEFAULT_BASE_URL),
            model=model,
            api_key=env.get("LOOP_API_KEY", ""),
            timeout=float(env.get("LOOP_TIMEOUT_SECONDS", "120")),
        )

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.prompt},
                ],
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        http_request = urllib.request.Request(f"{self.base_url}/chat/completions", data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:  # noqa: S310 - scheme validated in __init__
                body = json.loads(response.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"HTTP {exc.code} from provider") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError(f"provider unreachable: {type(exc).__name__}") from None
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise ProviderError("provider returned an unexpected response shape") from None
        usage = body.get("usage") or {}
        return ProviderResponse(
            text,
            int(usage.get("prompt_tokens") or estimate_tokens(request.system + request.prompt)),
            int(usage.get("completion_tokens") or estimate_tokens(text)),
        )

    def info(self) -> dict:
        return {"base_url": self.base_url}
