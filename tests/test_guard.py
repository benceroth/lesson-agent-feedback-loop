from loop.guard import Guard, changed_lines, glob_to_regex, normalize_path


def test_glob_matching():
    assert glob_to_regex("src/**").match("src/a/b.py")
    assert glob_to_regex("src/*.py").match("src/a.py")
    assert not glob_to_regex("src/*.py").match("src/a/b.py")
    assert glob_to_regex("**/test_*.py").match("tests/test_a.py")
    assert glob_to_regex("**/test_*.py").match("test_a.py")


def test_normalize_path_rejects_escapes():
    assert normalize_path("src/a.py") == "src/a.py"
    assert normalize_path("src\\a.py") == "src/a.py"
    for bad in ["../x.py", "/etc/passwd", "C:/x.py", "src/../tests/x.py", "", "src//a.py"]:
        assert normalize_path(bad) is None


def test_only_allow_listed_paths_are_editable():
    guard = Guard(["src/pagination.py"])
    assert guard.check_proposal({"src/pagination.py": "x = 1\n"}, {}) == []
    rules = {v.rule for v in guard.check_proposal({"tests/test_visible.py": "", "conftest.py": ""}, {})}
    assert rules == {"protected_path"}


def test_path_traversal_is_a_violation():
    violations = Guard(["src/**"]).check_proposal({"src/../tests/test_x.py": ""}, {})
    assert [v.rule for v in violations] == ["unsafe_path"]


def test_diff_scope_limits():
    guard = Guard(["src/**"], max_files=1, max_lines=3)
    assert any(v.rule == "diff_scope" for v in guard.check_proposal({"src/a.py": "a\n", "src/b.py": "b\n"}, {}))
    big = "\n".join(str(i) for i in range(10))
    assert any(v.rule == "diff_scope" for v in guard.check_proposal({"src/a.py": big}, {"src/a.py": ""}))
    assert guard.check_proposal({"src/a.py": "a\nb\n"}, {"src/a.py": "a\n"}) == []


def test_changed_lines_counts_additions_and_removals():
    assert changed_lines("a\nb\n", "a\nc\n") == 2
    assert changed_lines("a\n", "a\n") == 0


def test_snapshot_detects_tampering_with_protected_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n")
    guard = Guard(["src/**"])
    snap = guard.snapshot_protected(tmp_path)
    assert "src/a.py" not in snap and "tests/test_a.py" in snap
    assert guard.verify_protected(tmp_path, snap) == []
    (tmp_path / "src" / "a.py").write_text("x = 2\n")  # editable: fine
    assert guard.verify_protected(tmp_path, snap) == []
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n")
    assert [v.rule for v in guard.verify_protected(tmp_path, snap)] == ["modified_protected"]
    (tmp_path / "conftest.py").write_text("")
    assert len(guard.verify_protected(tmp_path, snap)) == 2
