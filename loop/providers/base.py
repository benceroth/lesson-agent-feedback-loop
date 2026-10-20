"""Provider interface and reply parsing shared by every provider."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol


class ProviderError(Exception):
    """The provider could not produce a reply (network, auth, rate limit...)."""


class ReplyError(Exception):
    """The reply was not in the expected JSON shape."""


@dataclass(frozen=True)
class ProviderRequest:
    role: str  # "builder" | "reviewer"
    task_id: str
    attempt: int
    system: str
    prompt: str


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    tokens_in: int
    tokens_out: int


class Provider(Protocol):
    name: str
    model: str

    def complete(self, request: ProviderRequest) -> ProviderResponse: ...

    def info(self) -> dict: ...


def estimate_tokens(text: str) -> int:
    """Token proxy: roughly four characters per token."""
    return max(1, len(text) // 4)


def extract_json(text: str) -> dict:
    stripped = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start == -1 or end <= start:
        raise ReplyError("reply contains no JSON object")
    try:
        data = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ReplyError(f"reply is not valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ReplyError("reply JSON must be an object")
    return data


def parse_builder_reply(text: str) -> tuple[dict[str, str], str]:
    data = extract_json(text)
    files = data.get("files", {})
    if not isinstance(files, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
        raise ReplyError("'files' must map relative paths to full file contents")
    summary = data.get("summary", "")
    return files, summary if isinstance(summary, str) else ""
