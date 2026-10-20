# Break it

Three small scenarios that remove a safeguard on purpose, so you can watch what fails. All use the scripted provider (not a model) and need nothing but Python.

| Scenario | Run |
|---|---|
| [A loop with no stop condition](no-stop-condition/README.md) | `python break-it/no-stop-condition/run.py` |
| [A builder that weakens the tests](weakened-tests/README.md) | `python break-it/weakened-tests/run.py` |
| [A reviewer that is also the builder](self-review/README.md) | `python break-it/self-review/run.py` |
