# AGENTS.md (template)

Instructions for AI coding sessions in this repository. Copy to the root of your project and edit the bracketed parts. Keep it short; it is read on every run.

## Project
- [One line: what this project is.]
- Language and tools: [e.g. Python 3.12, pytest, ruff].

## How to check your work
Run these before you say a task is done. The output decides, not your confidence.

```
[pytest -q]
[ruff check .]
```

If a check fails, read the failing test names and messages, fix the code, and run the checks again.

## Rules
- Edit only the paths named in the task brief.
- Never edit tests, test configuration, CI files or lock files to make a check pass. If you believe a test is wrong, stop and explain why.
- Keep changes small and focused. No unrelated refactors or formatting churn.
- Do not add dependencies without asking.
- Do not read or print secrets, `.env` files or credentials.

## Loop limits
- At most [3] attempts per task.
- If two consecutive attempts do not reduce the number of failing checks, stop.

## When you stop without success
Write a short report: what you changed, which checks still fail (names and messages), what you tried, and what decision a human needs to make. Do not claim success.

## Done means
- The acceptance checks in the task brief pass.
- The diff is small enough for a person to review.
- A human approves before merge or release.
