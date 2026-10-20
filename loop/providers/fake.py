"""Scripted provider: deterministic canned replies for CI and the committed demo.

It is NOT a model. Each task ships ``scripted.py`` with named scenarios (a
sequence of attempts, plus optional canned reviews). A seeded RNG picks one
scenario per (seed, task, run_index), so single-shot and loop modes see the same
scenario for the same run and can be compared pairwise.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from loop.providers.base import ProviderRequest, ProviderResponse, estimate_tokens
from loop.task import TASKS_DIR, discover_tasks, load_scenarios


class ScriptedProvider:
    name = "scripted"
    model = "scripted-demo"

    def __init__(self, tasks_dir: Path = TASKS_DIR, seed: int = 0, run_index: int = 0, scenario: str | None = None):
        self.tasks_dir = Path(tasks_dir)
        self.seed = seed
        self.run_index = run_index
        self.forced = scenario
        self._chosen: dict[str, str] = {}
        self._scenarios: dict[str, dict[str, dict]] = {}

    def _load(self, task_id: str) -> dict[str, dict]:
        if task_id not in self._scenarios:
            task = next(t for t in discover_tasks(self.tasks_dir) if t.id == task_id)
            self._scenarios[task_id] = load_scenarios(task)
        return self._scenarios[task_id]

    def scenario_name(self, task_id: str) -> str:
        if task_id not in self._chosen:
            scenarios = self._load(task_id)
            if self.forced is not None:
                if self.forced not in scenarios:
                    raise KeyError(f"{task_id} has no scenario {self.forced!r}; choose from {sorted(scenarios)}")
                self._chosen[task_id] = self.forced
            else:
                rng = random.Random(f"{self.seed}:{task_id}:{self.run_index}")
                names = sorted(scenarios)
                self._chosen[task_id] = rng.choices(names, weights=[scenarios[n]["weight"] for n in names])[0]
        return self._chosen[task_id]

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        scenario = self._load(request.task_id)[self.scenario_name(request.task_id)]
        attempts = scenario["attempts"]
        step = attempts[min(request.attempt, len(attempts)) - 1]
        if request.role == "reviewer":
            body = {"findings": step.get("review", [])}
        else:
            body = {"summary": step.get("summary", ""), "files": step.get("files", {})}
        text = json.dumps(body)
        return ProviderResponse(text, estimate_tokens(request.system + request.prompt), estimate_tokens(text))

    def info(self) -> dict:
        return {"scenarios": dict(self._chosen)}
