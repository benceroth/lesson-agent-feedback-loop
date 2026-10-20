# Experiment protocol: single-shot vs loop

The do-it-yourself counterpart to the post's "what research can and cannot tell us": measure it on your model, and look at the variance.

## Question

For a given model, how much does a feedback loop (and a separate reviewer) change success, and at what cost?

## Conditions

| Mode | Attempts | Reviewer |
|---|---:|---|
| `single-shot` | 1 | no |
| `loop` | 4, stall patience 2 | no |
| `loop-review` | 4 | separate provider instance, read-only |

Same tasks, same seeds, same checks in every mode.

## Procedure

1. `python -m loop validate-tasks` (starters fail; scripted scenarios behave).
2. Choose N: at least 10 runs per task per mode; 20+ if you can afford it. Fix the seed (`--seed`).
3. Real model: set `LOOP_API_KEY`, `LOOP_MODEL`, optionally `LOOP_REVIEWER_MODEL` (use a *different* model or at least a fresh context), `LOOP_BASE_URL`. Use temperature 0 as shipped, so variance reflects real run-to-run differences.
4. `python -m loop experiment --provider openai --runs 10 --out experiments/local/<model>-<date>`
5. Read `summary.md`, `failure-categories.csv`, `attempts.jsonl`.

## Metrics

- **pass@1** - passed on the first attempt.
- **pass within budget** - passed within the attempt budget.
- **attempts / tokens per success** - total spent (including failed runs) divided by successes.
- **false confidence** - passed the loop's checks, failed the ground-truth audit (task 002).
- **stalled / budget stops** - how runs ended.

## Reading the results

- With N=10 a difference of one or two runs is noise (a 40% vs 50% gap is not a finding). Report counts, not just percentages, and repeat with another seed.
- Task 005 must be 0% pass. Any pass there means a check or the guard is broken (or the model cheated).
- Look at *why* attempts fail, not just whether they pass: guard violations, malformed replies, review blocks.
- A higher pass rate that costs three times the tokens may not be a win. Compare cost per success.

## Reporting

Always state: model and version, provider/base URL type, date, N, seed, budgets, and the harness commit. Label results "teaching experiment, not a benchmark". Do not mix scripted and real results. The committed `experiments/results/` are a **scripted demo** and reproducible with `python -m loop verify-results`.

## Threats to validity

Tiny tasks; my hidden checks; possible training-data contamination; reviewer and builder may share a model; token proxy; no repeated seeds by default.
