from __future__ import annotations

from pathlib import Path

from loop.providers.base import Provider, ProviderError
from loop.providers.fake import ScriptedProvider
from loop.providers.openai_compat import OpenAICompatibleProvider
from loop.task import TASKS_DIR

PROVIDER_KINDS = ("scripted", "openai")


def make_provider(
    kind: str,
    role: str = "builder",
    tasks_dir: Path = TASKS_DIR,
    seed: int = 0,
    run_index: int = 0,
    scenario: str | None = None,
) -> Provider:
    """Create a provider. Builder and reviewer get separate instances (separate contexts)."""
    if kind == "scripted":
        return ScriptedProvider(tasks_dir, seed, run_index, scenario)
    if kind == "openai":
        return OpenAICompatibleProvider.from_env(role)
    raise ProviderError(f"unknown provider {kind!r}; choose from {PROVIDER_KINDS}")
