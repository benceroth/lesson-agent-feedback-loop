import json

import pytest

from loop.providers.base import ProviderRequest, ProviderResponse
from loop.reviewer import parse_findings, review
from loop.task import get_task


def findings_json(*items, **extra):
    return json.dumps({"findings": list(items), **extra})


def test_evidence_less_blockers_are_demoted():
    findings, _ = parse_findings(
        findings_json(
            {"severity": "blocker", "category": "bug", "file": "a.py", "claim": "wrong"},
            {"severity": "major", "category": "bug", "file": "a.py", "line": 3, "claim": "wrong", "evidence": "f('é') returns 0"},
        )
    )
    assert findings[0].severity == "nit" and findings[0].demoted and not findings[0].blocking
    assert findings[1].blocking and findings[1].line == 3
    assert "evidence" in findings[1].render()


def test_unknown_severity_and_bad_shapes_are_rejected():
    from loop.providers.base import ReplyError

    for bad in [findings_json({"severity": "huge"}), '{"findings": "x"}', findings_json("text")]:
        with pytest.raises(ReplyError):
            parse_findings(bad)


def test_reviewer_edits_are_ignored_but_counted():
    _, ignored = parse_findings(findings_json(files={"src/a.py": "x"}))
    assert ignored == 1


class Canned:
    name, model = "canned", "m"

    def __init__(self, text):
        self.text, self.seen = text, []

    def complete(self, request: ProviderRequest):
        self.seen.append(request)
        return ProviderResponse(self.text, 10, 5)

    def info(self):
        return {}


def test_review_never_receives_builder_reasoning(tmp_path):
    from loop.workspace import create_workspace

    task = get_task("001")
    ws = create_workspace(task, tmp_path / "ws")
    provider = Canned(findings_json())
    result = review(provider, task, ws, 1, "all visible tests pass")
    assert result.approved and result.tokens == 15
    request = provider.seen[0]
    assert request.role == "reviewer"
    assert "all visible tests pass" in request.prompt


def test_malformed_review_is_not_approval(tmp_path):
    from loop.workspace import create_workspace

    task = get_task("001")
    ws = create_workspace(task, tmp_path / "ws")
    result = review(Canned("not json"), task, ws, 1, "")
    assert result.malformed and not result.approved
