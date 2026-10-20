import json

from loop import cli
from loop.chart import grouped_bar_svg
from loop.experiment import make_provenance, run_experiment, save_experiment, verify_results, write_report
from loop.metrics import failure_categories, read_csv, summarize, write_csv


def row(task, mode, passed, attempts=1, tokens=100, audit="", outcome=None, cats="ok", p1=None):
    return {
        "task": task, "mode": mode, "passed": passed, "pass_at_1": passed if p1 is None else p1,
        "attempts": attempts, "tokens": tokens, "audit_ok": audit,
        "outcome": outcome or ("passed" if passed else "stopped:stalled"), "categories": cats,
    }


def test_summarize_computes_rates_and_false_confidence():
    rows = [
        row("t", "loop", 1, 2, 200, audit=0, p1=0),
        row("t", "loop", 1, 1, 100, audit=1),
        row("t", "loop", 0, 3, 300, cats="visible_failure|guard_violation"),
        row("t", "loop", 0, 3, 300),
    ]
    by = {(r["task"], r["mode"]): r for r in summarize(rows)}
    group = by[("t", "loop")]
    assert group["n"] == 4 and group["pass_within_budget"] == 0.5 and group["pass_at_1"] == 0.25
    assert group["false_confidence"] == 1 and group["stopped_stalled"] == 2
    assert group["attempts_per_success"] == 4.5 and group["tokens_per_success"] == 450
    assert ("ALL", "loop") in by


def test_failure_categories_skip_ok():
    cats = failure_categories([row("t", "loop", 0, cats="ok|guard_violation|guard_violation")])
    assert cats == [{"mode": "loop", "category": "guard_violation", "attempts": 2}]


def test_csv_round_trip(tmp_path):
    path = tmp_path / "x.csv"
    write_csv(path, [{"a": 1, "b": "x"}], ["a", "b"])
    assert read_csv(path) == [{"a": "1", "b": "x"}]
    assert b"\r" not in path.read_bytes()


def test_svg_chart_is_well_formed_and_escaped():
    import xml.dom.minidom

    svg = grouped_bar_svg("A & B <demo>", "sub", ["g1", "g2"], {"single-shot": [0.5, None], "loop": [1.0, 0.25]}, 1.0)
    xml.dom.minidom.parseString(svg)
    assert "A &amp; B &lt;demo&gt;" in svg


def test_small_experiment_report_and_verification(tmp_path):
    work = tmp_path / "work"
    results = run_experiment(runs=2, task_ids=["001"], modes=["single-shot", "loop"], work_root=work, seed=5)
    assert len(results) == 4
    again = run_experiment(runs=2, task_ids=["001"], modes=["single-shot", "loop"], work_root=work, seed=5)
    assert [r.scenario for r in results] == [r.scenario for r in again]
    out = tmp_path / "out"
    prov = make_provenance("scripted", "scripted-demo", 2, 5, ["001-fix-off-by-one"])
    save_experiment(results, out, prov)
    for name in ("runs.csv", "summary.csv", "summary.md", "pass-rate.svg", "cost.svg", "provenance.json"):
        assert (out / name).is_file(), name
    assert "Scripted demo" in (out / "summary.md").read_text(encoding="utf-8")
    write_report(read_csv(out / "runs.csv"), out, json.loads((out / "provenance.json").read_text(encoding="utf-8")))


def test_committed_results_are_labelled_and_consistent():
    from loop.task import REPO_ROOT

    results = REPO_ROOT / "experiments" / "results"
    prov = json.loads((results / "provenance.json").read_text(encoding="utf-8"))
    assert "not a model benchmark" in prov["note"]
    rows = read_csv(results / "runs.csv")
    assert len(rows) == prov["runs"] * len(prov["tasks"]) * 3
    assert (results / "summary.md").read_text(encoding="utf-8").count("Scripted demo") >= 1
    assert callable(verify_results)


def test_cli_run_json_and_errors(tmp_path, capsys):
    base = ["--work-root", str(tmp_path / "w")]
    assert cli.main([*base, "run", "001", "--scenario", "correct", "--json"]) == 0
    out = capsys.readouterr().out
    data = json.loads(out[out.index("{\n"):])
    assert data["outcome"] == "passed"
    assert cli.main([*base, "run", "001", "--scenario", "nope"]) == 2
    assert cli.main([*base, "run", "999"]) == 2


def test_guard_demo_shows_three_outcomes(tmp_path, capsys):
    assert cli.main(["--work-root", str(tmp_path / "w"), "guard-demo"]) == 0
    out = capsys.readouterr().out
    assert "guard_violation" in out and "passed" in out and "stalled" in out
