## Goal
`parse_quantity(text)` in `src/quantity.py` turns user input from an order form into an integer quantity. Today it accepts anything `int()` accepts, including values that make no sense for an order.

## Requirements
- Surrounding whitespace is ignored.
- Valid input is a whole number written with the ASCII digits `0-9` only: no sign, no decimal point, no underscores, no other scripts' digits.
- The value must be between 1 and `MAX_QUANTITY` (1000), inclusive.
- Anything else raises `ValueError`.

## Constraints
- Change only `src/quantity.py`. Keep the function name and `MAX_QUANTITY`.

## Acceptance checks
- Visible tests in `tests/` pass.
- Hidden acceptance tests (not shown) pass.

## Out of scope
- Localized number formats such as `1,000`.
