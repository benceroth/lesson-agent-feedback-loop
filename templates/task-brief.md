# Task brief: <short title>

Copy this file, fill it in, and keep it in the repository or the issue so every run starts from the same written state.

## Goal
One or two sentences: what should be true when the task is done?

## Context
Files and docs the agent should read first. Link decisions, not chat history.

## Requirements
- Observable behavior, one per line. Each should be checkable.

## Constraints
- Paths the agent may edit (everything else is protected).
- No new dependencies / no public API changes / etc.

## Acceptance checks
- The exact commands that decide success, e.g. `pytest tests/auth` and `ruff check src`.
- Which checks are hidden from the agent, if any (and who owns them).
- What these checks do NOT prove (be explicit).

## Budget and stop conditions
- Max attempts: 3
- Max wall time / token proxy:
- Stop early when: the same checks fail twice in a row without progress.

## Out of scope
- Things the agent must not do, even if they look helpful.

## Who reviews and approves
- Name the human who decides whether this ships.

## If it cannot finish
Report which checks still fail, what was tried, and hand the task back. Do not edit tests or weaken checks to get green.
