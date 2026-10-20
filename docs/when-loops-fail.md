# When loops fail

A loop is only as good as its checks and its stop rules. Failure modes, with where the lab shows them:

1. **Weak checks.** A loop converges to whatever the checks reward. Task 002 passes every test the loop sees yet fails an unseen audit case: `audit_ok=0`, counted as *false confidence*. More attempts do not fix a check that cannot see the bug.
2. **Gameable checks.** Task 001 `cheater` edits the tests/special-cases the answer. Without the guard and hidden checks it "passes" (`python -m loop guard-demo`). Task 005's cheater would even pass the hidden tests if unguarded, because they are not contradictory; only protected visible tests catch it.
3. **Contradictory or impossible specs.** Task 005. The honest outcome is a stall and an escalation message. Any "success" there is a bug in the checks or a lie.
4. **No convergence.** Task 003 `never-converges` and 004 `vacuous`/`happy-path-only` burn the budget or stall. Retrying is not progress; the stall rule (two attempts without strictly fewer failures) exists to stop it.
5. **Echo review.** A reviewer that shares the author's blind spots approves the same mistake. Separate context and prompt help (002: review blocks the gap in the scripted demo) but do not guarantee it; a real reviewer model may also echo. Evidence-less blocking findings are demoted so that confidence alone cannot block or approve.
6. **Flaky tests.** A nondeterministic check makes feedback noise and progress tracking meaningless. Fix or quarantine flaky tests before looping; the lab's CI uses only deterministic checks.
7. **Cost.** In the scripted demo the loop spends about 40% more proxy tokens per run than single-shot for 20 extra points of pass rate, and review adds more. Compare cost per success, not just pass rate.

Rule of thumb: spend effort on the checks and the stop conditions before the prompt.
