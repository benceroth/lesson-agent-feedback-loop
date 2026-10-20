# Experiment results

**Scripted demo, not a model benchmark.** The replies come from canned scenarios (see `tasks/*/scripted.py`) chosen by a seeded random generator, so these numbers show how the harness measures a loop, not how any model performs.

- Provider: `scripted` (model: `scripted-demo`)
- Date: 2026-10-20
- Runs per task per mode (N): 10; seed: 20261020
- Loop budget: 4 attempts, stall patience 2; single-shot = 1 attempt
- Token figures are a proxy (about 4 characters per token), not billed tokens.

## Pass rates and cost proxy

| Task | Mode | N | pass@1 | pass within budget | attempts / success | tokens / success | false confidence | stalled | budget stops |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 001-fix-off-by-one | single-shot | 10 | 40% | 40% | 2.5 | 1208 | 0 | 0 | 6 |
| 001-fix-off-by-one | loop | 10 | 40% | 70% | 2.286 | 1235 | 0 | 3 | 0 |
| 001-fix-off-by-one | loop-review | 10 | 40% | 70% | 2.286 | 1928 | 0 | 3 | 0 |
| 002-add-input-validation | single-shot | 10 | 80% | 80% | 1.25 | 734 | 3 | 0 | 2 |
| 002-add-input-validation | loop | 10 | 80% | 100% | 1.2 | 727 | 3 | 0 | 0 |
| 002-add-input-validation | loop-review | 10 | 50% | 100% | 1.5 | 1944 | 0 | 0 | 0 |
| 003-refactor-keep-behavior | single-shot | 10 | 50% | 50% | 2 | 1799 | 0 | 0 | 5 |
| 003-refactor-keep-behavior | loop | 10 | 50% | 80% | 2.375 | 2241 | 0 | 0 | 2 |
| 003-refactor-keep-behavior | loop-review | 10 | 50% | 80% | 2.375 | 3227 | 0 | 0 | 2 |
| 004-write-missing-tests | single-shot | 10 | 30% | 30% | 3.333 | 1873 | 0 | 0 | 7 |
| 004-write-missing-tests | loop | 10 | 30% | 50% | 4.4 | 2869 | 0 | 5 | 0 |
| 004-write-missing-tests | loop-review | 10 | 30% | 50% | 4.4 | 3656 | 0 | 5 | 0 |
| 005-impossible-spec | single-shot | 10 | 0% | 0% | n/a | n/a | 0 | 0 | 10 |
| 005-impossible-spec | loop | 10 | 0% | 0% | n/a | n/a | 0 | 10 | 0 |
| 005-impossible-spec | loop-review | 10 | 0% | 0% | n/a | n/a | 0 | 10 | 0 |
| ALL | single-shot | 50 | 40% | 40% | 2.5 | 1494 | 3 | 0 | 30 |
| ALL | loop | 50 | 40% | 60% | 3.233 | 2101 | 3 | 18 | 2 |
| ALL | loop-review | 50 | 34% | 60% | 3.333 | 3063 | 0 | 18 | 2 |

`false confidence` = runs that passed the loop's own checks but failed a ground-truth audit that the loop never sees.
`attempts / success` and `tokens / success` divide the total spent across all runs, including failed runs, by the number of successes.

## Failing attempts by category

| Mode | Category | Attempts |
|---|---|---:|
| single-shot | guard_violation | 5 |
| single-shot | hidden_failure | 15 |
| single-shot | visible_failure | 10 |
| loop | guard_violation | 10 |
| loop | hidden_failure | 31 |
| loop | visible_failure | 26 |
| loop-review | guard_violation | 10 |
| loop-review | hidden_failure | 31 |
| loop-review | review_blocked | 3 |
| loop-review | visible_failure | 26 |

## How runs ended

| Mode | Outcome | Runs |
|---|---|---:|
| single-shot | passed | 20 |
| single-shot | stopped:max_attempts | 30 |
| loop | passed | 30 |
| loop | stopped:max_attempts | 2 |
| loop | stopped:stalled | 18 |
| loop-review | passed | 30 |
| loop-review | stopped:max_attempts | 2 |
| loop-review | stopped:stalled | 18 |

![pass rates](pass-rate.svg)

![cost proxy](cost.svg)

With a small N, differences of a few runs are noise. Read the protocol in `experiments/single-shot-vs-loop.md` before drawing conclusions.
