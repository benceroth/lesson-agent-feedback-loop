# A builder that weakens the tests

**Break it:** the scripted `cheater` rewrites the visible tests to match the buggy code. Then misconfigure the allow-list so the tests are writable.

```text
python break-it/weakened-tests/run.py
```

| Setup | Result |
|---|---|
| correct allow-list | guard rejects the edit |
| tests writable, hidden checks on | hidden tests still fail the buggy code |
| tests writable, hidden checks off | passes, and the code was never fixed |

**Lesson:** the guard and the hidden checks are separate layers. Remove both and the loop reports success for a lie. See `loop/guard.py` and `docs/safeguards.md`. For the single-layer version, run `python -m loop guard-demo`.
