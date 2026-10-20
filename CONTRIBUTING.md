# Contributing

Small, focused changes are welcome.

## Setup

```text
pip install -r requirements-dev.txt
python -m pytest
python -m loop validate-tasks
ruff check .
```

## Adding a task

1. Create `tasks/NNN-name/` with `task.json`, `BRIEF.md`, `starter/{src,tests}`, `hidden/` and `scripted.py`.
2. The starter must **fail** its checks. Give `scripted.py` weighted scenarios, each with an `expect` outcome.
3. Make hidden checks independent of the visible tests, and list only non-test paths as `editable`.
4. `python -m loop validate-tasks` must pass.

## Rules

- Standard library only in `loop/`. No new runtime dependencies.
- Tests must be deterministic and must not call real models or the network (except a local mock server).
- Never commit keys, `.env` files or `runs/`.
- Changing scenarios, checks or the runner changes the example results: re-run
  `python -m loop experiment --provider scripted --runs 10 --seed 20261020` and commit the outputs, or
  `python -m loop verify-results` will fail. Real-model results must state model, date and N, and live outside `experiments/results/` (use `experiments/local/` or a new labelled folder).
