from pathlib import Path

import pytest

from loop.task import TASKS_DIR, get_task


@pytest.fixture
def work_root(tmp_path: Path) -> Path:
    return tmp_path / "work"


@pytest.fixture(scope="session")
def tasks_dir() -> Path:
    return TASKS_DIR


@pytest.fixture
def task001():
    return get_task("001")
