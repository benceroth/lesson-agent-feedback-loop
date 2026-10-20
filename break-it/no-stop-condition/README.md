# No stop condition

**Break it:** remove every limit (attempts, time, tokens, stall detection) and give the builder a task it keeps getting wrong.

```text
python break-it/no-stop-condition/run.py
```

The first run uses the default budget and ends as `stopped:stalled` after 3 attempts with an escalation message. The second run has no limits; it only ends because the demo cuts the provider off after 12 calls, with more than four times the tokens spent and nothing fixed.

**Lesson:** the stop condition is part of the loop, not an optional extra. See `loop/budget.py`.

The builder here is scripted, so this shows the mechanism, not how often a real model gets stuck.
