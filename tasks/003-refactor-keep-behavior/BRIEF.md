## Goal
`shipping_cost(weight_kg, zone, express=False)` in `src/shipping.py` works but is a tangle of nested `if` statements that is hard to extend. Refactor it to be **table-driven** (rates in data, one short code path).

## Requirements
- Behavior must stay **exactly** the same for every input, including tier boundaries, rounding and error cases.
- No nested `if` blocks deeper than one level (checked by a hidden structure test; `elif` chains do not count as nesting).

## Constraints
- Change only `src/shipping.py`. Keep the function signature.

## Acceptance checks
- Visible tests in `tests/` pass.
- Hidden acceptance tests (not shown) pass.

## Out of scope
- New zones, new rates or any change to existing prices.
