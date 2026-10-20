## Goal
`moving_average(values, window)` in `src/rolling.py` has almost no tests. Write `tests/test_generated.py` so that a wrong implementation would be caught.

## Behavior to cover
- Returns the average of each consecutive window as floats (`[1, 2, 3, 4]` with window 2 gives `[1.5, 2.5, 3.5]`).
- A window of zero or less raises `ValueError`.
- A window larger than the data raises `ValueError`.

## Constraints
- Create or replace only `tests/test_generated.py`. Do not touch `src/` or the existing tests.

## Acceptance checks
- Your tests pass on the real implementation.
- Hidden check: your tests must also **fail** on deliberately broken variants of the module ("mutants"). Feedback names the mutants that survived.

## Out of scope
- Changing the implementation.
