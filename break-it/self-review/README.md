# A reviewer that is also the builder

**Break it:** task 002 has a scripted change that passes every visible and hidden test but accepts non-ASCII digits. Review it once with a separate reviewer, once with a reviewer that shares the builder's blind spot.

```text
python break-it/self-review/run.py
```

| Reviewer | Result |
|---|---|
| separate | blocks the change, the retry passes the ground-truth audit |
| builder reviewing itself | approves it, the audit fails (false confidence) |

**Lesson:** a second pass only adds information if it can see something the first pass could not. See `loop/reviewer.py` and `docs/when-loops-fail.md`.

The self-reviewer is a stand-in that returns no findings; it simulates a shared blind spot rather than measuring a real model.
