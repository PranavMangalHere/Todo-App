import csv
from pathlib import Path

import pytest

from todo.storage import (
    TASKS_CSV_HEADER,
    add_task,
    is_legacy_tasks_csv,
    load_tasks,
    migrate_legacy_tasks_csv,
    save_tasks,
    set_task_completed,
)


def test_migrate_legacy_csv_is_idempotent(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    p.write_text("Task A\nTask B\n", encoding="utf-8")

    assert is_legacy_tasks_csv(str(p))
    migrate_legacy_tasks_csv(str(p))

    # now structured
    assert not is_legacy_tasks_csv(str(p))

    first = load_tasks(str(p))
    assert [t.title for t in first] == ["Task A", "Task B"]
    assert all(t.completed is False for t in first)

    # running again should not change data
    migrate_legacy_tasks_csv(str(p))
    second = load_tasks(str(p))
    assert [t.id for t in second] == [t.id for t in first]
    assert [t.title for t in second] == [t.title for t in first]


def test_save_and_load_roundtrip(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    t1 = add_task(str(p), "Hello")
    t2 = add_task(str(p), "World")

    tasks = load_tasks(str(p))
    assert [t.id for t in tasks] == [t1.id, t2.id]
    assert [t.title for t in tasks] == ["Hello", "World"]
    assert all(not t.completed for t in tasks)


def test_set_task_completed_persists(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    t1 = add_task(str(p), "Hello")

    ok = set_task_completed(str(p), t1.id, True)
    assert ok is True

    tasks = load_tasks(str(p))
    assert len(tasks) == 1
    assert tasks[0].id == t1.id
    assert tasks[0].completed is True


def test_load_skips_invalid_rows(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(TASKS_CSV_HEADER)
        w.writerow(["", "Missing id", "false"])
        w.writerow(["123", "", "false"])
        w.writerow(["ok", "Good", "true"])

    tasks = load_tasks(str(p))
    assert [(t.id, t.title, t.completed) for t in tasks] == [("ok", "Good", True)]


def test_add_task_rejects_empty_title(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    with pytest.raises(ValueError):
        add_task(str(p), "   ")


def test_is_legacy_false_when_file_missing(tmp_path: Path):
    p = tmp_path / "missing.csv"
    assert is_legacy_tasks_csv(str(p)) is False


def test_save_writes_header(tmp_path: Path):
    p = tmp_path / "tasks.csv"
    save_tasks(str(p), [])
    contents = p.read_text(encoding="utf-8").splitlines()
    assert contents[0] == ",".join(TASKS_CSV_HEADER)
