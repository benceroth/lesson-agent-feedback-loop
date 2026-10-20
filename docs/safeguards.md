# Safeguards

## In the lab

- **Allow-list.** `task.json` `editable` lists the only writable paths. Everything else (tests, config, hidden checks, `pytest.ini`, `conftest.py`) is protected.
- **Diff scope.** `max_changed_files` / `max_changed_lines` reject sprawling edits.
- **Unsafe paths.** Absolute paths, drive letters and `..` are rejected before anything is written.
- **Defense in depth.** Protected files are hashed before the run and re-verified after every applied attempt; changes, deletions and new files outside the allow-list are violations.
- **Hidden checks.** Run in a separate copy of the workspace; the loop only gets test names back, never their source.
- **Budgets.** Attempts, wall time, token proxy, stall detection; each ends the run with an escalation message.
- **Reviewer is read-only.** Edits in its reply are ignored and counted.

## Not provided

- **No sandbox.** Generated code runs as a local subprocess with your privileges (pytest strips `PYTEST_*` variables; that is all). For real models use a container or VM with no secrets and restricted network.
- The guard stops a model from *changing the judge*; it cannot stop malicious code in the editable file.
- Prompts contain task code and are sent to the configured endpoint.

See also the sibling repo [`lesson-agent-harness`](https://github.com/benceroth/lesson-agent-harness) for broader agent safety patterns.
