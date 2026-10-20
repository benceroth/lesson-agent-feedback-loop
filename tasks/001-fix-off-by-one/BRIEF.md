## Goal
`paginate(items, page, page_size)` in `src/pagination.py` returns the items on a **1-based** page, but page 1 currently skips the first items.

## Requirements
- Page 1 is the first `page_size` items; the last page may be shorter.
- A page past the end returns an empty list.
- `page < 1` or `page_size < 1` raises `ValueError`.

## Constraints
- Change only `src/pagination.py`. Keep the function signature.

## Acceptance checks
- Visible tests in `tests/` pass.
- Hidden acceptance tests (not shown) pass.

## Out of scope
- Do not change tests or add dependencies.
